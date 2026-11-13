"""Secondary descriptive ranking contrasts on existing predictions, no extra fits/tests."""
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t
R=Path(__file__).resolve().parent;out=[];splits=[]
for component,file,seedcol,scenario,familycol,f1,controls in [('primary_RT','grouped_results/semantic_raw.csv','split_seed','scenario','group','fixed_f1',['random']),('expanded_RT','control_results/raw.csv','seed','control','family','macro_f1',['uniform','importance','importance_correlation']),('Thursday','thursday_controls/raw.csv','seed','control','family','macro_f1',['uniform','importance','importance_correlation'])]:
 d=pd.read_csv(R/file).rename(columns={seedcol:'seed',scenario:'control',familycol:'family',f1:'macro_f1'})
 print(component,d.control.unique())
 if component=='primary_RT':controls=['matched_random'] if 'matched_random' in set(d.control) else ['random']
 u=d[d.control.isin(['semantic']+controls)].groupby(['seed','method','family','control'])[['macro_f1','auroc','ap']].mean().reset_index()
 for (method,family),a in u[u.control=='semantic'].groupby(['method','family']):
  a=a.set_index('seed')
  for control in controls:
   b=u[(u.method==method)&(u.family==family)&(u.control==control)].set_index('seed');assert len(a)==len(b)==12
   for metric in ['macro_f1','auroc','ap']:
    v=a[metric]-b[metric];assert v.notna().all();se=np.sqrt((1/len(v)+.5)*v.var(ddof=1));mu=v.mean();out.append(dict(component=component,method=method,family=family,control=control,metric=metric,semantic=a[metric].mean(),comparator=b[metric].mean(),difference=mu,ci95_lower=mu-t.ppf(.975,11)*se,ci95_upper=mu+t.ppf(.975,11)*se))
    for seed in v.index:splits.append(dict(component=component,method=method,family=family,control=control,metric=metric,seed=seed,semantic=a.loc[seed,metric],comparator=b.loc[seed,metric],difference=v.loc[seed]))
q=pd.DataFrame(out);q.to_csv(R/'results/ranking_contrasts_secondary.csv',index=False);pd.DataFrame(splits).to_csv(R/'results/ranking_contrasts_by_seed.csv',index=False)
assert len(q)==(48+120)*3
print(q[(q.method.isin(['MLP_clean','RF_median']))&(q.control=='uniform')].round(6).to_string(index=False))
print('Rows',len(q),'(48 primary + 120 expanded) x 3 outcomes; no secondary p-values computed')
