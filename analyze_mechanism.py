from pathlib import Path
import numpy as np,pandas as pd,json
R=Path(__file__).resolve().parent;O=R/'mechanism_results'
v=pd.read_csv(O/'feature_variation.csv');v['constant']=v.constant.astype(bool);v['near_constant']=v.near_constant.astype(bool)
v.groupby(['dataset','family','partition']).agg(n_feature_split_rows=('constant','size'),constant_fraction=('constant','mean'),near_constant_fraction=('near_constant','mean'),mean_modal_fraction=('modal_fraction','mean'),median_absolute_offset=('median_standardized',lambda a:abs(a).mean())).to_csv(O/'variation_summary.csv')
a=pd.read_csv(O/'replacement_raw.csv');u=a.groupby(['dataset','seed','method','family','control','replacement'])[['macro_f1','mean_probability_change','prediction_change']].mean().reset_index();u.to_csv(O/'replacement_split_means.csv',index=False)
rows=[]
for (ds,method,fam,repl),g in u[u.control=='semantic'].groupby(['dataset','method','family','replacement']):
 b=u[(u.dataset==ds)&(u.method==method)&(u.family==fam)&(u.replacement==repl)&(u.control=='uniform')].set_index('seed');g=g.set_index('seed');delta=g.macro_f1-b.macro_f1
 rows.append(dict(dataset=ds,method=method,family=fam,replacement=repl,semantic_f1=g.macro_f1.mean(),random_f1=b.macro_f1.mean(),contrast=delta.mean(),sd_split=delta.std(ddof=1),mean_abs_probability_change=g.mean_probability_change.mean(),prediction_change=g.prediction_change.mean()))
s=pd.DataFrame(rows);s.to_csv(O/'replacement_summary.csv',index=False)
c=pd.read_csv(O/'single_column_raw.csv');c.groupby(['dataset','method','column'])[['f1_change','probability_change']].agg(['mean','std']).to_csv(O/'single_column_summary.csv')
g=c.groupby(['dataset','method','column'])[['f1_change','probability_change']].mean().reset_index();g.to_csv(O/'single_column_means.csv',index=False)
assert len(pd.read_csv(O/'clean_rechecks.csv'))==84 and len(a)==8064 and len(c)==3696
clean=pd.read_csv(O/'clean_rechecks.csv');assert clean.groupby(['dataset','method']).size().eq(12).all()
print('Validated diagnostic refits84; replacement evaluations8064; single-column evaluations3696; clean84')
print(s.round(5).to_string(index=False))
print('\nFeature variation\n',pd.read_csv(O/'variation_summary.csv').round(5).to_string(index=False))
print('\nMost damaging columns\n',g.sort_values('f1_change').groupby(['dataset','method']).head(5).to_string(index=False))
