from pathlib import Path
import json,time,warnings
import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,roc_auc_score,average_precision_score,brier_score_loss,roc_curve,confusion_matrix
R=Path(__file__).resolve().parent;O=R/'temporal_results';O.mkdir(exist_ok=True)
a=pd.read_csv(R/'data/lycos_tuesday_labelled.csv');meta=json.load(open(R/'results/temporal_source.json'));cols=meta['features'];y=a.label.to_numpy();X=a[cols].to_numpy()
G={'interarrival':[c for c in cols if 'iat_' in c],'payload':[c for c in cols if 'pkt_len_' in c],'activity':[c for c in cols if c.startswith(('active_','idle_'))],'flags':[c for c in cols if 'flag_' in c]};assert all(G.values())
def ece(z,p):
 k=np.minimum((p*10).astype(int),9);return sum(np.mean(k==i)*abs(p[k==i].mean()-z[k==i].mean()) for i in range(10) if np.any(k==i))
records=[];splits=[];fits=[];warn=[]
METHODS=['RF_median','Hist_median','Hist_native','MLP_clean']
for window,cut in enumerate(['2017-07-04T12:30:00Z','2017-07-04T12:40:00Z','2017-07-04T12:50:00Z']):
 t0=pd.Timestamp(cut).value//1000;t1=t0+10*60*10**6;t2=t1+15*60*10**6
 # Flow start and flow end must both lie inside the relevant historical window.
 start=a.timestamp.to_numpy();end=start+a.flow_duration.to_numpy()
 train=np.flatnonzero(end<t0);cal=np.flatnonzero((start>=t0)&(end<t1));test=np.flatnonzero((start>=t1)&(end<t2))
 for p in [train,cal,test]:assert len(np.unique(y[p]))==2
 print('window',window,'available',len(train),len(cal),len(test),'attacks',[int(y[p].sum()) for p in [train,cal,test]],flush=True)
 for seed in range(1001,1013):
  def take(ids,n):
   return train_test_split(ids,train_size=n,stratify=y[ids],random_state=seed)[0] if len(ids)>n else ids
  tr=take(train,6000);ca=take(cal,1500);te=take(test,3000)
  assert end[tr].max()<start[ca].min() and end[ca].max()<start[te].min()
  A=X[tr];C=X[ca];T=X[te];yt=y[tr];yc=y[ca];z=y[te];med=SimpleImputer(strategy='median').fit(A);scale=StandardScaler().fit(A)
  splits.append(dict(window=window,seed=seed,train=len(tr),calibration=len(ca),test=len(te),train_attack=int(yt.sum()),cal_attack=int(yc.sum()),test_attack=int(z.sum()),train_end_max=float(end[tr].max()),cal_start_min=int(start[ca].min()),cal_end_max=float(end[ca].max()),test_start_min=int(start[te].min())))
  np.savez_compressed(O/f'window_{window}_seed_{seed}.npz',train=tr,calibration=ca,test=te)
  tests=[('clean','none',0,T)]
  rng=np.random.default_rng(seed+80000)
  for group,features in G.items():
   V=T.copy();V[:,[cols.index(c) for c in features]]=np.nan;tests.append(('semantic',group,0,V))
   for rep in range(2):
    V=T.copy();ix=rng.choice(len(cols),len(features),replace=False);V[:,ix]=np.nan;tests.append(('matched_random',group,rep,V))
  for method in METHODS:
   def prep(V):
    if method=='Hist_native':return V
    V=med.transform(V);return scale.transform(V) if method=='MLP_clean' else V
   if method.startswith('Hist'):model=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,early_stopping=False,random_state=seed)
   elif method=='MLP_clean':model=MLPClassifier(hidden_layer_sizes=(64,32),max_iter=100,early_stopping=True,random_state=seed,batch_size=256)
   else:model=RandomForestClassifier(n_estimators=60,max_depth=18,n_jobs=2,random_state=seed)
   t=time.perf_counter()
   with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter('always');model.fit(prep(A),yt);warn.extend([dict(window=window,seed=seed,method=method,message=str(w.message)) for w in ws])
   fits.append(dict(window=window,seed=seed,method=method,fit_seconds=time.perf_counter()-t))
   pc=model.predict_proba(prep(C))[:,1]
   def logit(p):p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p)).reshape(-1,1)
   platt=LogisticRegression(C=1e6,max_iter=1000).fit(logit(pc),yc);qc=platt.predict_proba(logit(pc))[:,1];fp,tp,th=roc_curve(yc,qc);ok=np.isfinite(th);tau=th[np.flatnonzero(ok)[np.argmax((tp-fp)[ok])]]
   for scenario,group,rep,V in tests:
    prob=model.predict_proba(prep(V))[:,1];q=platt.predict_proba(logit(prob))[:,1];pred=prob>=.5;calpred=q>=tau;tn,fp,fn,tp=confusion_matrix(z,pred).ravel()
    records.append(dict(window=window,seed=seed,method=method,scenario=scenario,group=group,replicate=rep,macro_f1=f1_score(z,pred,average='macro'),calibrated_f1=f1_score(z,calpred,average='macro'),auroc=roc_auc_score(z,prob),ap=average_precision_score(z,prob),brier=brier_score_loss(z,prob),brier_calibrated=brier_score_loss(z,q),ece_raw=ece(z,prob),ece_calibrated=ece(z,q),attack_recall=tp/(tp+fn),fpr=fp/(fp+tn),tau=tau))
   pd.DataFrame(records).to_csv(O/'temporal_raw.csv',index=False);pd.DataFrame(splits).to_csv(O/'splits.csv',index=False);pd.DataFrame(fits).to_csv(O/'fits.csv',index=False);(O/'warnings.json').write_text(json.dumps(warn,indent=2));(O/'groups.json').write_text(json.dumps(G,indent=2))
  print('window',window,'seed',seed,'records',len(records),flush=True)
print('COMPLETE',len(records),len(fits),flush=True)
