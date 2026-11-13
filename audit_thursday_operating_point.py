"""Post hoc audit of selected training attacks and Thursday MLP threshold behavior."""
from pathlib import Path
import json,numpy as np,pandas as pd,warnings
from sklearn.neural_network import MLPClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix,f1_score
R=Path(__file__).resolve().parent;a=pd.read_csv(R/'data/lycos_thursday_labelled.csv');meta=json.load(open(R/'thursday_results/protocol_manifest.json'));cols=meta['features'];X=a[cols].to_numpy();y=a.label.to_numpy();old=pd.read_csv(R/'thursday_controls/raw.csv');rows=[];sets=[]
for seed in range(1001,1013):
 s=np.load(R/'thursday_results'/f'split_{seed}.npz');A=X[s['train']];T=X[s['test']];z=y[s['test']];sets.append(set(s['train'][y[s['train']]==1].tolist()));med=SimpleImputer(strategy='median').fit(A);sc=StandardScaler().fit(A);model=MLPClassifier(hidden_layer_sizes=(64,32),max_iter=100,early_stopping=True,random_state=seed,batch_size=256)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');model.fit(sc.transform(med.transform(A)),y[s['train']])
 for family in ['clean','interarrival','activity','payload','flags']:
  V=T.copy()
  if family!='clean':
   names=[c for c in cols if ('iat_' in c if family=='interarrival' else 'pkt_len_' in c if family=='payload' else c.startswith(('active_','idle_')) if family=='activity' else 'flag_' in c)];V[:,[cols.index(c) for c in names]]=np.nan
  prob=model.predict_proba(sc.transform(med.transform(V)))[:,1];pred=prob>=.5;tn,fp,fn,tp=confusion_matrix(z,pred,labels=[0,1]).ravel();score=f1_score(z,pred,average='macro');ref=old[(old.seed==seed)&(old.method=='MLP_clean')&(old.control==('clean' if family=='clean' else 'semantic'))]
  if family!='clean':ref=ref[ref.family==family]
  assert abs(score-ref.macro_f1.iloc[0])<1e-12
  rows.append(dict(seed=seed,family=family,tn=tn,fp=fp,fn=fn,tp=tp,macro_f1=score,attack_prevalence=z.mean(),predicted_attack_fraction=pred.mean(),attack_recall=tp/(tp+fn),all_benign_f1=f1_score(z,np.zeros_like(z),average='macro')))
 print(seed,flush=True)
pd.DataFrame(rows).to_csv(R/'mechanism_results/thursday_operating_points.csv',index=False)
summary={'training_attack_counts':[len(v) for v in sets],'identical_attack_row_sets':all(v==sets[0] for v in sets),'unique_training_attack_rows':len(set.union(*sets)),'refits':12,'scope':'Conditional fixed chronological construction; descriptive post hoc audit.'};(R/'mechanism_results/thursday_training_overlap.json').write_text(json.dumps(summary,indent=2));print(summary);d=pd.DataFrame(rows);print(d.groupby('family')[['macro_f1','attack_recall','predicted_attack_fraction','all_benign_f1']].mean());print(d[d.family=='interarrival'][['seed','tn','fp','fn','tp']].to_string(index=False))
