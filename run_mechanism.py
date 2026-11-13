"""Frozen-model replacement and single-column diagnostics; post hoc, descriptive."""
from pathlib import Path
import json,warnings,time
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score,roc_auc_score,average_precision_score,brier_score_loss
R=Path(__file__).resolve().parent;O=R/'mechanism_results';O.mkdir(exist_ok=True)
rows=[];clean=[];columns=[];fits=[];variation=[];warningslog=[]
for dataset in ['rt','thursday']:
 if dataset=='rt':
  a=pd.read_csv(R/'data/rtiot.csv');y=(~a.Attack_type.isin(['Thing_Speak','MQTT_Publish','Wipro_bulb'])).astype(int).to_numpy();meta=json.load(open(R/'grouped_results/protocol_manifest.json'));cols=meta['features'];G=meta['semantic_groups'];X=a[cols].astype(float);b=X.copy();b['label']=y;keep=~b.duplicated();X=X[keep].to_numpy();y=y[keep];splitdir='grouped_results';targetdir='control_results'
 else:
  a=pd.read_csv(R/'data/lycos_thursday_labelled.csv');cols=json.load(open(R/'thursday_results/protocol_manifest.json'))['features'];X=a[cols].to_numpy();y=a.label.to_numpy();G={g:[c for c in cols if ('iat_' in c if g=='interarrival' else 'pkt_len_' in c if g=='payload' else c.startswith(('active_','idle_')) if g=='activity' else 'flag_' in c)] for g in ['interarrival','payload','activity','flags']};splitdir='thursday_results';targetdir='thursday_controls'
 draws=json.load(open(R/targetdir/'draws.json'));old=pd.read_csv(R/targetdir/'raw.csv')
 for seed in range(1001,1013):
  s=np.load(R/splitdir/f'split_{seed}.npz');A=X[s['train']];T=X[s['test']];yt=y[s['train']];z=y[s['test']];med=SimpleImputer(strategy='median').fit(A);scaler=StandardScaler().fit(A);median=med.statistics_;mean=A.mean(0)
  for family,names in G.items():
   for partition,V in [('train',A),('test',T)]:
    for name in names:
     j=cols.index(name);mode=float(pd.Series(V[:,j]).value_counts(normalize=True).iloc[0]);variation.append(dict(dataset=dataset,seed=seed,family=family,partition=partition,column=name,constant=np.ptp(V[:,j])==0,near_constant=mode>=.99,modal_fraction=mode,unique_values=len(np.unique(V[:,j])),std=float(V[:,j].std()),median_standardized=(median[j]-mean[j])/scaler.scale_[j]))
  methods=['RF_median','RF_mask','Hist_median','Hist_native','MLP_clean'] if dataset=='rt' else ['RF_median','MLP_clean']
  for method in methods:
   def prep(V):
    if method=='Hist_native':return V
    V=med.transform(V);return scaler.transform(V) if method=='MLP_clean' else V
   train=A;target=yt
   if method=='RF_mask':
    rng=np.random.default_rng(seed+90000);masked=A.copy();masked[rng.random(A.shape)<.3]=np.nan;train=np.r_[A,masked];target=np.r_[yt,yt]
   model=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,early_stopping=False,random_state=seed) if method.startswith('Hist') else MLPClassifier(hidden_layer_sizes=(64,32),max_iter=100,early_stopping=True,random_state=seed,batch_size=256) if method=='MLP_clean' else RandomForestClassifier(n_estimators=60,max_depth=18,n_jobs=2,random_state=seed)
   start=time.perf_counter()
   with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter('always');model.fit(prep(train),target);warningslog += [dict(dataset=dataset,seed=seed,method=method,message=str(w.message)) for w in ws]
   fits.append(dict(dataset=dataset,seed=seed,method=method,fit_seconds=time.perf_counter()-start))
   baseline=model.predict_proba(prep(T))[:,1]
   def metrics(prob):return dict(macro_f1=f1_score(z,prob>=.5,average='macro'),auroc=roc_auc_score(z,prob),ap=average_precision_score(z,prob),brier=brier_score_loss(z,prob))
   clean.append(dict(dataset=dataset,seed=seed,method=method,**metrics(baseline)))
   if dataset=='rt':
    orig=pd.read_csv(R/'grouped_results/semantic_raw.csv');ref=orig[(orig.split_seed==seed)&(orig.method==method)&(orig.scenario=='clean')].iloc[0];assert abs(metrics(baseline)['macro_f1']-ref.fixed_f1)<1e-12
   if method in ['RF_median','MLP_clean']:
    for j,name in enumerate(cols):
     V=T.copy();V[:,j]=median[j];prob=model.predict_proba(prep(V))[:,1];v=metrics(prob);columns.append(dict(dataset=dataset,seed=seed,method=method,column=name,f1_change=v['macro_f1']-metrics(baseline)['macro_f1'],probability_change=float(np.mean(abs(prob-baseline))),**v))
    tests=[d for d in draws if d['seed']==seed and d['control'] in ['semantic','uniform']]
    for d in tests:
     ix=[cols.index(c) for c in d['columns']]
     for replacement,repl in [('median',median),('mean',mean)]:
      V=T.copy();V[:,ix]=repl[ix];prob=model.predict_proba(prep(V))[:,1];rows.append(dict(dataset=dataset,seed=seed,method=method,family=d['family'],control=d['control'],replicate=d['replicate'],replacement=replacement,mean_probability_change=float(np.mean(abs(prob-baseline))),prediction_change=float(np.mean((prob>=.5)!=(baseline>=.5))),**metrics(prob)))
     if d['control']=='semantic':
      reference=old[(old.seed==seed)&(old.method==method)&(old.family==d['family'])&(old.control=='semantic')].macro_f1.iloc[0];assert abs(rows[-2]['macro_f1']-reference)<1e-12
   pd.DataFrame(clean).to_csv(O/'clean_rechecks.csv',index=False);pd.DataFrame(rows).to_csv(O/'replacement_raw.csv',index=False);pd.DataFrame(columns).to_csv(O/'single_column_raw.csv',index=False);pd.DataFrame(fits).to_csv(O/'fits.csv',index=False);pd.DataFrame(variation).to_csv(O/'feature_variation.csv',index=False);(O/'warnings.json').write_text(json.dumps(warningslog,indent=2));print(dataset,seed,method,len(rows),len(columns),flush=True)
# Restore the missing clean condition to the RT expanded table with computed recheck scores.
p=R/'control_results/raw.csv';d=pd.read_csv(p);d=d[d.control!='clean'];extra=pd.DataFrame([dict(seed=r['seed'],method=r['method'],family='none',control='clean',replicate=0,**{k:r[k] for k in ['macro_f1','auroc','ap','brier']}) for r in clean if r['dataset']=='rt']);assert len(extra)==60;pd.concat([d,extra],ignore_index=True).to_csv(p,index=False);assert len(d)+len(extra)==14700
print('COMPLETE',len(fits),len(rows),len(columns),'RT clean restored 60',flush=True)
