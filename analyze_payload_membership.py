"""Post hoc stratification of already evaluated uniform draws by two payload minima."""
from pathlib import Path
import json,pandas as pd,numpy as np
R=Path(__file__).resolve().parent
key={'fwd_pkts_payload.min','flow_pkts_payload.min'}
draws=pd.DataFrame([dict(seed=d['seed'],family=d['family'],replicate=d['replicate'],contains_payload_minimum=bool(key.intersection(d['columns'])),n_payload_minima=len(key.intersection(d['columns']))) for d in json.load(open(R/'control_results/draws.json')) if d['control']=='uniform' and d['family']=='interarrival'])
d=pd.read_csv(R/'control_results/raw.csv');d=d[(d.method=='MLP_clean')&(d.family=='interarrival')];u=d[d.control=='uniform'].merge(draws,on=['seed','family','replicate'],validate='one_to_one');sem=d[d.control=='semantic'].set_index('seed').macro_f1
u['semantic_f1']=u.seed.map(sem);u['semantic_minus_uniform']=u.semantic_f1-u.macro_f1
u.to_csv(R/'mechanism_results/payload_membership_draws.csv',index=False)
a=u.groupby(['seed','contains_payload_minimum']).agg(n_draws=('macro_f1','size'),uniform_f1=('macro_f1','mean'),semantic_f1=('semantic_f1','first'),contrast=('semantic_minus_uniform','mean')).reset_index();a.to_csv(R/'mechanism_results/payload_membership_by_seed.csv',index=False)
g=a.groupby('contains_payload_minimum').agg(seeds=('seed','nunique'),n_draws=('n_draws','sum'),uniform_f1=('uniform_f1','mean'),semantic_f1=('semantic_f1','mean'),contrast=('contrast','mean'),contrast_min=('contrast','min'),contrast_max=('contrast','max')).reset_index();g.to_csv(R/'mechanism_results/payload_membership_summary.csv',index=False)
print(g.to_string(index=False));print(a.to_string(index=False))
