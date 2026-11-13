from pathlib import Path
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
def plot():
 m=pd.read_csv(R/'grouped_results/means.csv');fig,axes=plt.subplots(1,2,figsize=(9,3.6),sharey=True);methods=['RF_repeat','RF_noise','Hist_native','MLP_clean','MLP_noise'];scenarios=['clean','noise_only','clip_only','clip_noise','project_only','project_noise'];labels=['Clean','Noise','Clip only','Clip + noise','Project only','Project + noise'];x=np.arange(6);width=.15
 for ax,alpha in zip(axes,['0.1','0.3']):
  for j,method in enumerate(methods):
   values=[]
   for sc in scenarios:
    q=m[(m.method==method)&(m.scenario==sc)]
    if sc!='clean':q=q[q.group.astype(str)==alpha]
    values.append(q.fixed_f1.iloc[0])
   ax.bar(x+(j-2)*width,values,width,label=method)
  ax.set_xticks(x,labels,rotation=30,ha='right',fontsize=8);ax.set_ylim(0,1.04);ax.set_title('Noise multiplier '+alpha);ax.grid(axis='y',alpha=.2)
 axes[0].set_ylabel('Mean Macro-F1');axes[-1].legend(fontsize=7,ncol=2,loc='lower left');fig.tight_layout();fig.savefig(R/'figures/noise_ablation.png',dpi=220);fig.savefig(R/'figures/noise_ablation.pdf');plt.close(fig)
if __name__=='__main__':plot()
