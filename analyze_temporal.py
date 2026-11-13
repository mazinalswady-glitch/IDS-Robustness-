from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;O=R/'temporal_results'
d=pd.read_csv(O/'temporal_raw.csv');s=pd.read_csv(O/'splits.csv');f=pd.read_csv(O/'fits.csv')
assert len(d)==1872 and len(f)==144 and len(s)==36
assert not d.duplicated(['window','seed','method','scenario','group','replicate']).any()
assert (s.train_end_max<s.cal_start_min).all() and (s.cal_end_max<s.test_start_min).all()
metrics=['macro_f1','calibrated_f1','auroc','ap','brier','brier_calibrated','ece_raw','ece_calibrated','attack_recall','fpr']
assert d[metrics].ge(-1e-12).all().all() and d[metrics].le(1+1e-12).all().all()
u=d.groupby(['window','seed','method','scenario','group'])[metrics].mean().reset_index();u.to_csv(O/'split_means.csv',index=False)
u.groupby(['window','method','scenario','group'])[metrics].agg(['mean','std']).to_csv(O/'summary.csv')
m=u.groupby(['window','method','scenario','group'])[metrics].mean().reset_index();m.to_csv(O/'means.csv',index=False)
g=[]
for (w,method,family),a in u[u.scenario=='semantic'].groupby(['window','method','group']):
 b=u[(u.window==w)&(u.method==method)&(u.group==family)&(u.scenario=='matched_random')].set_index('seed');z=a.set_index('seed').macro_f1-b.macro_f1
 g.append(dict(window=w,method=method,family=family,semantic_minus_random=z.mean(),sd=z.std(ddof=1)))
pd.DataFrame(g).to_csv(O/'semantic_gaps.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(9,3.4),sharey=True)
for w,ax in enumerate(axes):
 for method in ['RF_median','Hist_median','Hist_native','MLP_clean']:
  q=m[(m.window==w)&(m.method==method)];v=[q[q.scenario=='clean'].macro_f1.iloc[0]]+[q[(q.scenario=='semantic')&(q.group==x)].macro_f1.iloc[0] for x in ['interarrival','payload','activity','flags']];ax.plot(range(5),v,'o-',label=method,ms=3)
 ax.set_xticks(range(5),['Clean','IAT','Payload','Activity','Flags'],rotation=30);ax.set_title(['12:40 to 12:55','12:50 to 13:05','13:00 to 13:15'][w]+' UTC');ax.grid(alpha=.2)
axes[0].set_ylabel('Mean Macro-F1');axes[-1].legend(fontsize=7);fig.tight_layout();fig.savefig(R/'figures/temporal.png',dpi=220);fig.savefig(R/'figures/temporal.pdf');plt.close(fig)
print('Validated',len(d),'records;',len(f),'fits; strict chronology in all',len(s),'splits')
print(m[m.scenario=='semantic'].groupby(['window','method'])[['macro_f1','auroc','ap']].mean().round(4).to_string())
