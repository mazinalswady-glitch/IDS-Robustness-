"""Training-only importance and redundancy matched outage controls; no semantic causality claim."""
from pathlib import Path
import json,time,warnings,hashlib,argparse
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score,roc_auc_score,average_precision_score,brier_score_loss,mutual_info_score
R=Path(__file__).resolve().parent;parser=argparse.ArgumentParser();parser.add_argument('--dataset',choices=['rt','thursday'],default='rt');args=parser.parse_args();O=R/('control_results' if args.dataset=='rt' else 'thursday_controls');O.mkdir(exist_ok=True)
a=pd.read_csv(R/'data/rtiot.csv');y=(~a.Attack_type.isin(['Thing_Speak','MQTT_Publish','Wipro_bulb'])).astype(int).to_numpy();cols=json.load(open(R/'grouped_results/protocol_manifest.json'))['features'];X=a[cols].astype(float);b=X.copy();b['label']=y;keep=~b.duplicated();X=X[keep].to_numpy();y=y[keep]
if args.dataset=='thursday':
 a=pd.read_csv(R/'data/lycos_thursday_labelled.csv');cols=json.load(open(R/'thursday_results/protocol_manifest.json'))['features'];X=a[cols].to_numpy();y=a.label.to_numpy()
G=json.load(open(R/'grouped_results/protocol_manifest.json'))['semantic_groups']
if args.dataset=='thursday':G={g:[c for c in cols if ('iat_' in c if g=='interarrival' else 'pkt_len_' in c if g=='payload' else c.startswith(('active_','idle_')) if g=='activity' else 'flag_' in c)] for g in G}
methods=['RF_median','RF_mask','Hist_median','Hist_native','MLP_clean'];rows=[];fits=[];diag=[];drawlog=[];allwarnings=[]
for seed in range(1001,1013):
 s=np.load(R/('grouped_results' if args.dataset=='rt' else 'thursday_results')/f'split_{seed}.npz');A=X[s['train']];T=X[s['test']];yt=y[s['train']];z=y[s['test']];med=SimpleImputer(strategy='median').fit(A);scale=StandardScaler().fit(A)
 mi=np.array([mutual_info_score(yt,np.searchsorted(np.unique(np.quantile(A[:,j],np.linspace(0,1,11))),A[:,j],side='right')) for j in range(len(cols))]);corr=np.nan_to_num(np.abs(pd.DataFrame(A).corr(method='spearman').to_numpy()));constant=np.ptp(A,axis=0)==0
 rng=np.random.default_rng(seed+310000);tests=[('none','clean',0,np.array([],dtype=int))]
 for family,names in G.items():
  ix=np.array([cols.index(v) for v in names]);k=len(ix);tri=np.triu_indices(k,1)
  def descriptor(sets):return np.c_[mi[sets].sum(1),corr[sets[:,:,None],sets[:,None,:]][:,tri[0],tri[1]].mean(1),constant[sets].mean(1)]
  target=descriptor(ix[None,:])[0]
  pool=np.argsort(rng.random((20000,len(cols))),axis=1)[:,:k];pool=np.sort(pool,axis=1);pool=np.unique(pool,axis=0);pool=pool[~np.all(pool==np.sort(ix),axis=1)];d=descriptor(pool);sd=np.maximum(d.std(0),1e-8)
  importance=((d[:,0]-target[0])/sd[0])**2+((d[:,2]-target[2])/sd[2])**2
  joint=importance+((d[:,1]-target[1])/sd[1])**2
  subsets={'uniform':pool[rng.choice(len(pool),20,replace=False)],'importance':pool[np.argsort(importance,kind='stable')[:20]],'importance_correlation':pool[np.argsort(joint,kind='stable')[:20]],'semantic':ix[None,:]}
  for control,sets in subsets.items():
   for rep,(indices,desc) in enumerate(zip(sets,descriptor(sets))):
    tests.append((family,control,rep,indices));drawlog.append(dict(seed=seed,family=family,control=control,replicate=rep,columns=[cols[i] for i in indices]))
    diag.append(dict(seed=seed,family=family,control=control,replicate=rep,mi_sum=desc[0],mean_abs_spearman=desc[1],constant_fraction=desc[2],target_mi=target[0],target_correlation=target[1],target_constant=target[2],mi_standardized_error=(desc[0]-target[0])/sd[0],correlation_standardized_error=(desc[1]-target[1])/sd[1]))
 for method in methods:
  def prep(V):
   if method=='Hist_native':return V
   V=med.transform(V);return scale.transform(V) if method=='MLP_clean' else V
  train=A;targety=yt
  if method=='RF_mask':
   # Reproduce the exact original masking RNG before any new draw generation.
   rr=np.random.default_rng(seed+90000);mask=A.copy();mask[rr.random(A.shape)<.3]=np.nan;train=np.r_[A,mask];targety=np.r_[yt,yt]
  model=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,early_stopping=False,random_state=seed) if method.startswith('Hist') else MLPClassifier(hidden_layer_sizes=(64,32),max_iter=100,early_stopping=True,random_state=seed,batch_size=256) if method=='MLP_clean' else RandomForestClassifier(n_estimators=60,max_depth=18,n_jobs=2,random_state=seed)
  start=time.perf_counter()
  with warnings.catch_warnings(record=True) as ws:
   warnings.simplefilter('always');model.fit(prep(train),targety);allwarnings.extend([dict(seed=seed,method=method,message=str(w.message)) for w in ws])
  fits.append(dict(seed=seed,method=method,fit_seconds=time.perf_counter()-start))
  for family,control,rep,indices in tests:
   V=T.copy();V[:,indices]=np.nan;p=model.predict_proba(prep(V))[:,1];rows.append(dict(seed=seed,method=method,family=family,control=control,replicate=rep,macro_f1=f1_score(z,p>=.5,average='macro'),auroc=roc_auc_score(z,p),ap=average_precision_score(z,p),brier=brier_score_loss(z,p)))
  pd.DataFrame(rows).to_csv(O/'raw.csv',index=False);pd.DataFrame(fits).to_csv(O/'fits.csv',index=False);print(seed,method,len(rows),flush=True)
 pd.DataFrame(diag).to_csv(O/'matching_diagnostics.csv',index=False);(O/'draws.json').write_text(json.dumps(drawlog));(O/'warnings.json').write_text(json.dumps(allwarnings,indent=2))
print('COMPLETE',len(rows),len(fits),flush=True)
