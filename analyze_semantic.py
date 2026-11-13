from pathlib import Path
import json,itertools
import numpy as np,pandas as pd
from scipy import stats
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;O=R/'grouped_results';F=R/'figures';F.mkdir(exist_ok=True)
d=pd.read_csv(O/'semantic_raw.csv');fit=pd.read_csv(O/'fits.csv');m=json.load(open(O/'protocol_manifest.json'))
assert len(d)==3888 and len(fit)==144,(len(d),len(fit));assert not d.duplicated(['split_seed','method','scenario','group','replicate']).any()
assert d.groupby(['split_seed','method']).size().eq(27).all()
for metric in ['auroc','ap','brier_raw','brier_calibrated','ece_raw','ece_calibrated','fixed_f1','calibrated_f1']:assert d[metric].between(0,1).all()
# Calibration/test/train rows disjoint per split. Repeated splits themselves overlap and are not independent.
for s in range(1001,1013):
 a=np.load(O/f'split_{s}.npz');assert not(set(a['train_groups'])&set(a['test_groups']));assert not(set(a['calibration_groups'])&set(a['test_groups']));assert not(set(a['train_groups'])&set(a['calibration_groups']));assert not(set(a['train'])&set(a['test']));assert not(set(a['calibration'])&set(a['test']));assert not(set(a['train'])&set(a['calibration']))
metrics=['fixed_f1','calibrated_f1','fixed_recall','fixed_fpr','calibrated_recall','calibrated_fpr','auroc','ap','brier_raw','brier_calibrated','ece_raw','ece_calibrated']
unit=d.groupby(['split_seed','method','scenario','group'])[metrics].mean().reset_index();unit.to_csv(O/'split_means.csv',index=False)
unit.groupby(['method','scenario','group'])[metrics].agg(['mean','std']).to_csv(O/'summary.csv')
mean=unit.groupby(['method','scenario','group'])[metrics].mean().reset_index();mean.to_csv(O/'means.csv',index=False)
# Primary family of comparisons: semantic minus cardinality-matched random outages (all 4 families, all 12 methods).
# Nadeau-Bengio corrected resampled t approximation, df=11; ratio is actual evaluated test/train sample ratio.
rows=[];ratio=.5;n=12;crit=stats.t.ppf(.975,n-1)
for method in m['methods']:
 for family in m['semantic_groups']:
  a=unit[(unit.method==method)&(unit.scenario=='semantic')&(unit.group==family)].set_index('split_seed')
  b=unit[(unit.method==method)&(unit.scenario=='matched_random')&(unit.group==family)].set_index('split_seed')
  diff=(a.fixed_f1-b.fixed_f1).to_numpy();mu=diff.mean();sd=diff.std(ddof=1);se=np.sqrt((1/n+ratio)*sd**2)
  t=mu/se if se else (0 if mu==0 else np.sign(mu)*np.inf);p=2*stats.t.sf(abs(t),n-1)
  rows.append({'method':method,'family':family,'difference_semantic_minus_random':mu,'sd_split':sd,'corrected_se':se,'ci95_lower':mu-crit*se,'ci95_upper':mu+crit*se,'t':t,'df':11,'p_raw':p,'test_train_ratio':ratio,'n_splits':n})
s=pd.DataFrame(rows);order=np.argsort(s.p_raw.to_numpy());p=s.p_raw.to_numpy();adjusted=np.empty(len(p));running=0
for j,i in enumerate(order):running=max(running,(len(p)-j)*p[i]);adjusted[i]=min(1,running)
s['p_holm']=adjusted;s.to_csv(O/'semantic_statistics.csv',index=False)
# Secondary noise and calibration effects: descriptive only, outside primary multiplicity family.
secondary=[]
for method in m['methods']:
 for alpha in ['0.1','0.3']:
  vals=unit[(unit.method==method)&(unit.group==alpha)].set_index(['split_seed','scenario'])
  for a,b in [('clip_noise','noise_only'),('clip_noise','clip_only'),('project_noise','project_only')]:
   aa=vals.xs(a,level='scenario').fixed_f1;bb=vals.xs(b,level='scenario').fixed_f1;delta=aa-bb
   secondary.append(dict(method=method,alpha=alpha,contrast=a+' minus '+b,mean=delta.mean(),sd=delta.std(ddof=1)))
pd.DataFrame(secondary).to_csv(O/'noise_ablation.csv',index=False)
fig,axes=plt.subplots(2,2,figsize=(8,6),sharey=True)
show=['RF_median','RF_knn','RF_iterative','Hist_median','Hist_native','Hist_native_mask','MLP_clean','MLP_mask']
for ax,fam in zip(axes.ravel(),m['semantic_groups']):
 gg=s[(s.family==fam)&(s.method.isin(show))].set_index('method').loc[show];y=np.arange(len(show));ax.errorbar(gg.difference_semantic_minus_random,y,xerr=np.array([gg.difference_semantic_minus_random-gg.ci95_lower,gg.ci95_upper-gg.difference_semantic_minus_random]),fmt='o',capsize=2);ax.axvline(0,color='k',ls='--',lw=.7);ax.set_title(fam+' ('+str(len(m['semantic_groups'][fam]))+' columns)');ax.set_yticks(y,show,fontsize=8);ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.set_xlabel('Semantic minus matched-random Macro-F1',fontsize=8)
fig.tight_layout();fig.savefig(F/'semantic_gap.png',dpi=220);fig.savefig(F/'semantic_gap.pdf');plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(9,3.5),sharey=True)
for ax,methods,title in zip(axes,[['RF_median','RF_repeat','RF_mask','RF_noise'],['Hist_median','Hist_native','Hist_native_mask'],['MLP_clean','MLP_mask','MLP_noise']],['Random forest','Histogram boosting','Neural baseline']):
 x=np.arange(5)
 for method in methods:
  v=[float(mean[(mean.method==method)&(mean.scenario=='clean')].fixed_f1.iloc[0])]+[float(mean[(mean.method==method)&(mean.scenario=='semantic')&(mean.group==fam)].fixed_f1.iloc[0]) for fam in m['semantic_groups']];ax.plot(x,v,'o-',label=method,ms=3)
 ax.set_xticks(x,['Clean','IAT','Payload','Activity','Flags'],rotation=30);ax.set_title(title);ax.grid(alpha=.2);ax.legend(fontsize=7,loc='lower left')
axes[0].set_ylabel('Mean Macro-F1 at fixed threshold');fig.tight_layout();fig.savefig(F/'method_comparison.png',dpi=220);fig.savefig(F/'method_comparison.pdf');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(8,3.5),sharey=True)
for ax,alpha in zip(axes,['0.1','0.3']):
 labels=['Clean','Noise','Clip only','Clip + noise','Project only','Project + noise'];sc=['clean','noise_only','clip_only','clip_noise','project_only','project_noise']
 for method in ['RF_repeat','RF_noise','Hist_native','MLP_clean','MLP_noise']:
  vals=[]
  for scenario in sc:
   q=mean[(mean.method==method)&(mean.scenario==scenario)]
   if scenario!='clean':q=q[q.group==alpha]
   vals.append(q.fixed_f1.iloc[0])
  ax.plot(range(6),vals,'o-',label=method,ms=3)
 ax.set_title('Noise multiplier '+alpha);ax.set_xticks(range(6),labels,rotation=30,ha='right',fontsize=8);ax.grid(alpha=.2)
axes[0].set_ylabel('Mean Macro-F1');axes[1].legend(fontsize=7);fig.tight_layout();fig.savefig(F/'noise_ablation.png',dpi=220);fig.savefig(F/'noise_ablation.pdf');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(8,3.5))
g=mean[mean.scenario=='semantic'].groupby('method').mean(numeric_only=True).reindex(m['methods']);x=np.arange(len(g));axes[0].bar(x-.18,g.brier_raw,.36,label='Raw');axes[0].bar(x+.18,g.brier_calibrated,.36,label='Platt');axes[1].bar(x-.18,g.fixed_f1,.36,label='Fixed 0.5');axes[1].bar(x+.18,g.calibrated_f1,.36,label='Validation threshold')
for ax in axes:ax.set_xticks(x,m['methods'],rotation=75,fontsize=7);ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Mean Brier across semantic outages');axes[1].set_ylabel('Mean Macro-F1 across semantic outages');fig.tight_layout();fig.savefig(F/'probability_thresholds.png',dpi=220);fig.savefig(F/'probability_thresholds.pdf');plt.close(fig)
print('Validated',len(d),'rows;',len(s),'primary tests; significant after Holm',int((s.p_holm<.05).sum()))
print(s[['method','family','difference_semantic_minus_random','ci95_lower','ci95_upper','p_holm']].round(5).to_string(index=False))

# Unordered intervention categories use grouped bars.
from plot_noise_bars import plot
plot()
