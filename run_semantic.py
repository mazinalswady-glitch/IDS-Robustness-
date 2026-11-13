"""Executed semantic-family benchmark. No inferred timestamps. See PROTOCOL.md."""
from pathlib import Path
import json,hashlib,time,warnings,platform,argparse
import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer,KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,roc_curve,f1_score,confusion_matrix,balanced_accuracy_score
R=Path(__file__).resolve().parent;O=R/'grouped_results';O.mkdir(exist_ok=True)
SEEDS=list(range(1001,1013));METHODS=['RF_median','RF_repeat','RF_mask','RF_noise','Hist_median','Hist_native','Hist_native_mask','RF_knn','RF_iterative','MLP_clean','MLP_mask','MLP_noise']
a=pd.read_csv(R/'data/rtiot.csv');y=(~a.Attack_type.isin(['Thing_Speak','MQTT_Publish','Wipro_bulb'])).astype(int).to_numpy()
cols=[c for c in a.select_dtypes('number') if c not in ['id','id.orig_p','id.resp_p']];X=a[cols].astype(float)
b=X.copy();b['label']=y;bad=b.groupby(cols,sort=False,dropna=False).label.transform('nunique').to_numpy()>1
dupe=b.duplicated().to_numpy();X=X[~dupe].reset_index(drop=True);y=y[~dupe];X=X.to_numpy()
group_codes=pd.factorize([row.tobytes() for row in np.ascontiguousarray(X)])[0];unique_groups=np.unique(group_codes)
GROUPS={'interarrival':[c for c in cols if '_iat.' in c],'payload':[c for c in cols if '_pkts_payload.' in c],'activity':[c for c in cols if c.startswith(('active.','idle.'))],'flags':[c for c in cols if 'flag_count' in c]}
assert all(GROUPS.values());assert len(set(sum(GROUPS.values(),[])))==sum(map(len,GROUPS.values()))
manifest={'dataset':'RT-IoT2022 official UCI CSV','source_url':'https://archive.ics.uci.edu/static/public/942/data.csv','source_sha256':hashlib.sha256((R/'data/rtiot.csv').read_bytes()).hexdigest(),'ambiguous_rows_removed':0,'ambiguous_source_rows_retained_before_pair_dedup':int(bad.sum()),'unique_feature_groups':len(unique_groups),'duplicate_rows_removed':int(dupe.sum()),'retained_rows':len(y),'features':cols,'semantic_groups':GROUPS,'split_seeds':SEEDS,'methods':METHODS,'scope':'label-blind random feature-group splits with contradictory binary labels retained; not temporal; no physical fault validation','python':platform.python_version(),'splits':{}}
(O/'protocol_manifest.json').write_text(json.dumps(manifest,indent=2));records=[];fitlog=[];warnlog=[]
# Resume completed split-method units using append-only CSV checkpoint.
path=O/'semantic_raw.csv'
if path.exists():records=pd.read_csv(path).to_dict('records')
if (O/'fits.csv').exists():fitlog=pd.read_csv(O/'fits.csv').to_dict('records')
if (O/'warnings.json').exists():warnlog=json.load(open(O/'warnings.json'))

def choose(ids,cap,seed):
 if len(ids)<=cap:return ids
 return train_test_split(ids,train_size=cap,stratify=y[ids],random_state=seed)[0]
def ece(z,p):
 k=np.minimum((p*10).astype(int),9);return sum(np.mean(k==i)*abs(p[k==i].mean()-z[k==i].mean()) for i in range(10) if np.any(k==i))
for s in SEEDS:
 train_groups,other_groups=train_test_split(unique_groups,test_size=.4,random_state=s);cal_groups,test_groups=train_test_split(other_groups,test_size=.5,random_state=s+1)
 tr=np.flatnonzero(np.isin(group_codes,train_groups));ca=np.flatnonzero(np.isin(group_codes,cal_groups));te=np.flatnonzero(np.isin(group_codes,test_groups))
 tr=choose(tr,6000,s+10);ca=choose(ca,1500,s+11);te=choose(te,3000,s+12)
 A=X[tr];C=X[ca];T=X[te];yt=y[tr];yc=y[ca];z=y[te];np.savez_compressed(O/f'split_{s}.npz',train=tr,calibration=ca,test=te,train_groups=group_codes[tr],calibration_groups=group_codes[ca],test_groups=group_codes[te])
 manifest['splits'][str(s)]={'train':len(tr),'calibration':len(ca),'test':len(te),'test_train_ratio':len(te)/len(tr)}
 med=SimpleImputer(strategy='median').fit(A);scaler=StandardScaler().fit(A);lo=A.min(0);hi=A.max(0);sigma=A.std(0);integer=np.all(A==np.round(A),0)
 rng=np.random.default_rng(s+90000);mask=A.copy();mask[rng.random(A.shape)<.3]=np.nan
 noiseA=A+.1*sigma*rng.normal(size=A.shape)
 tests=[('clean','none',0,T)]
 for name,features in GROUPS.items():
  ix=[cols.index(c) for c in features];V=T.copy();V[:,ix]=np.nan;tests.append(('semantic',name,0,V))
  for rep in range(3):
   rand=rng.choice(len(cols),size=len(ix),replace=False);V=T.copy();V[:,rand]=np.nan;tests.append(('matched_random',name,rep,V))
 N=rng.normal(size=T.shape)
 for alpha in [.1,.3]:
  for mode in ['noise_only','clip_only','clip_noise','project_only','project_noise']:
   V=T.copy()
   if mode in ['noise_only','clip_noise','project_noise']:V=V+alpha*sigma*N
   if mode!='noise_only':V=np.clip(V,lo,hi)
   if mode.startswith('project'):V[:,integer]=np.round(V[:,integer])
   tests.append((mode,str(alpha),0,V))
 for method in METHODS:
  if any(r['split_seed']==s and r['method']==method for r in fitlog):continue
  t=time.perf_counter();native=method in ['Hist_native','Hist_native_mask'];train=A;target=yt
  if method in ['RF_repeat']:train=np.r_[A,A];target=np.r_[yt,yt]
  if method in ['RF_mask','Hist_native_mask','MLP_mask']:train=np.r_[A,mask];target=np.r_[yt,yt]
  if method in ['RF_noise','MLP_noise']:train=np.r_[A,noiseA];target=np.r_[yt,yt]
  imp=med;scale=method.startswith('MLP') or method=='RF_knn'
  if method=='RF_knn':
   imp=KNNImputer(n_neighbors=5).fit(scaler.transform(A[:256]))
  elif method=='RF_iterative':
   with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter('always');imp=IterativeImputer(max_iter=3,n_nearest_features=5,skip_complete=False,random_state=s).fit(scaler.transform(A))
    warnlog.extend([{'seed':s,'method':method,'phase':'imputer_fit','warning':str(w.message)} for w in ws])
   scale=True
  def transform(V):
   if native:return V
   if method in ['RF_knn','RF_iterative']:return imp.transform(scaler.transform(V))
   W=imp.transform(V)
   return scaler.transform(W) if scale else W
  V=transform(train)
  if method.startswith('Hist'):model=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,early_stopping=False,random_state=s)
  elif method.startswith('MLP'):model=MLPClassifier(hidden_layer_sizes=(64,32),max_iter=100,early_stopping=True,random_state=s,batch_size=256)
  else:model=RandomForestClassifier(n_estimators=60,max_depth=18,n_jobs=2,random_state=s)
  with warnings.catch_warnings(record=True) as ws:
   warnings.simplefilter('always');model.fit(V,target)
   warnlog.extend([{'seed':s,'method':method,'phase':'classifier_fit','warning':str(w.message)} for w in ws])
  fitsec=time.perf_counter()-t;pc=model.predict_proba(transform(C))[:,1]
  # Platt model on log-odds, fit on clean held-out calibration only.
  def logit(p):p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p)).reshape(-1,1)
  platt=LogisticRegression(C=1e6,max_iter=1000).fit(logit(pc),yc);qc=platt.predict_proba(logit(pc))[:,1]
  fpr,tpr,thresholds=roc_curve(yc,qc);valid=np.isfinite(thresholds);idx=np.flatnonzero(valid)[np.argmax((tpr-fpr)[valid])];tau=float(thresholds[idx])
  methodrows=[]
  for scenario,group,rep,Vtest in tests:
   start=time.perf_counter();p=model.predict_proba(transform(Vtest))[:,1];q=platt.predict_proba(logit(p))[:,1];infer=time.perf_counter()-start
   row={'split_seed':s,'method':method,'scenario':scenario,'group':group,'replicate':rep,'n_train':len(tr),'n_test':len(te),'tau':tau,'auroc':roc_auc_score(z,p),'ap':average_precision_score(z,p),'brier_raw':brier_score_loss(z,p),'brier_calibrated':brier_score_loss(z,q),'ece_raw':ece(z,p),'ece_calibrated':ece(z,q),'predict_ms_record':infer/len(te)*1000}
   for label,prob,th in [('fixed',p,.5),('calibrated',q,tau)]:
    pred=(prob>=th).astype(int);tn,fp,fn,tp=confusion_matrix(z,pred,labels=[0,1]).ravel();row.update({label+'_f1':f1_score(z,pred,average='macro'),label+'_balanced_accuracy':balanced_accuracy_score(z,pred),label+'_recall':tp/(tp+fn),label+'_fpr':fp/(fp+tn)})
   methodrows.append(row)
  records.extend(methodrows);fitlog.append({'split_seed':s,'method':method,'fit_seconds':fitsec,'train_rows_seen':len(train)})
  pd.DataFrame(records).to_csv(path,index=False);pd.DataFrame(fitlog).to_csv(O/'fits.csv',index=False);(O/'protocol_manifest.json').write_text(json.dumps(manifest,indent=2));(O/'warnings.json').write_text(json.dumps(warnlog,indent=2))
  print(s,method,round(fitsec,2),'s','rows',len(records),flush=True)
print('COMPLETE',len(records),len(fitlog),flush=True)
