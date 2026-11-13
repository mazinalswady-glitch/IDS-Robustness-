from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.stats import t
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
R=Path(__file__).resolve().parent
for name in ['control_results','thursday_controls']:
 O=R/name
 if not (O/'raw.csv').exists():continue
 d=pd.read_csv(O/'raw.csv');f=pd.read_csv(O/'fits.csv');assert len(f)==60
 expected=14700
 assert len(d)==expected,(name,len(d));assert not d.duplicated(['seed','method','family','control','replicate']).any()
 u=d.groupby(['seed','method','family','control'])[['macro_f1','auroc','ap','brier']].mean().reset_index();u.to_csv(O/'split_means.csv',index=False);u.groupby(['method','family','control'])[['macro_f1','auroc','ap','brier']].agg(['mean','std']).to_csv(O/'summary.csv')
 rows=[]
 for (method,family),a in u[u.control=='semantic'].groupby(['method','family']):
  a=a.set_index('seed')
  for control in ['uniform','importance','importance_correlation']:
   b=u[(u.method==method)&(u.family==family)&(u.control==control)].set_index('seed');v=a.macro_f1-b.macro_f1;n=len(v);se=np.sqrt((1/n+.5)*v.var(ddof=1));mu=v.mean();p=2*t.sf(abs(mu/se),n-1) if se else 1
   rows.append(dict(method=method,family=family,control=control,difference=mu,ci95_lower=mu-t.ppf(.975,11)*se,ci95_upper=mu+t.ppf(.975,11)*se,p_raw=p))
 q=pd.DataFrame(rows);order=np.argsort(q.p_raw.to_numpy());adj=np.empty(len(q));running=0
 for j,i in enumerate(order):running=max(running,(len(q)-j)*q.p_raw.iloc[i]);adj[i]=min(1,running)
 q['p_holm']=adj;q.to_csv(O/'statistics.csv',index=False)
 diag=pd.read_csv(O/'matching_diagnostics.csv');diag.groupby(['family','control'])[['mi_sum','mean_abs_spearman','constant_fraction','mi_standardized_error','correlation_standardized_error']].mean().to_csv(O/'matching_summary.csv')
 if name=='control_results':
  orig=pd.read_csv(R/'grouped_results/semantic_raw.csv');v=d[d.control=='semantic'].merge(orig[orig.scenario=='semantic'],left_on=['seed','method','family'],right_on=['split_seed','method','group']);assert len(v)==240;assert np.max(abs(v.macro_f1-v.fixed_f1))<1e-12,'Refitted semantic score mismatch'
 print(name,'VALID',len(d),'records;',int((q.p_holm<.05).sum()),'of60 exploratory adjusted tests significant',flush=True)
 print(q[q.p_holm<.05].round(5).to_string(index=False),flush=True)
 fig,axes=plt.subplots(2,2,figsize=(8,5.8),sharey=True);methods=['RF_median','RF_mask','Hist_median','Hist_native','MLP_clean']
 for family,ax in zip(['interarrival','payload','activity','flags'],axes.ravel()):
  for j,control in enumerate(['uniform','importance','importance_correlation']):
   v=q[(q.family==family)&(q.control==control)].set_index('method').loc[methods];y=np.arange(5)+(j-1)*.19;ax.errorbar(v.difference,y,xerr=np.array([v.difference-v.ci95_lower,v.ci95_upper-v.difference]),fmt='o',ms=3,capsize=2,label=control)
  ax.axvline(0,color='k',ls='--',lw=.6);ax.set_yticks(range(5),methods,fontsize=8);ax.set_title(family);ax.grid(axis='x',alpha=.2);ax.set_xlabel('Semantic minus comparator Macro-F1',fontsize=8);ax.xaxis.set_major_locator(MaxNLocator(4))
 axes[0,1].legend(fontsize=7);fig.tight_layout();fig.savefig(R/'figures'/('matched_controls.png' if name=='control_results' else 'thursday_controls.png'),dpi=220);fig.savefig(R/'figures'/('matched_controls.pdf' if name=='control_results' else 'thursday_controls.pdf'));plt.close(fig)
if all((R/d/'statistics.csv').exists() for d in ['control_results','thursday_controls']):
 frames=[]
 for name in ['control_results','thursday_controls']:
  v=pd.read_csv(R/name/'statistics.csv');v['dataset']=name;frames.append(v)
 both=pd.concat(frames,ignore_index=True);order=np.argsort(both.p_raw.to_numpy());adj=np.empty(len(both));running=0
 for j,i in enumerate(order):running=max(running,(len(both)-j)*both.p_raw.iloc[i]);adj[i]=min(1,running)
 both['p_holm_global_120']=adj;both.to_csv(R/'results/expanded_statistics_120.csv',index=False)
 print('Pooled exploratory Holm family:120 tests;',int((both.p_holm_global_120<.05).sum()),'adjusted findings',flush=True)
