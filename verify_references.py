from pathlib import Path
import urllib.request,urllib.parse,json,concurrent.futures,time
R=Path(__file__).resolve().parent;O=R/'sources';O.mkdir(exist_ok=True)
D={
'denning':'10.1109/TSE.1987.232894','sommer':'10.1109/SP.2010.25','buczak':'10.1109/COMST.2015.2494502','ring':'10.1016/j.cose.2019.06.005','cic2017':'10.5220/0006639801080116','engelen':'10.1109/SPW53761.2021.00009','ciciot':'10.3390/s23135941','unsw':'10.1109/MILCIS.2015.7348942','nsl':'10.1109/CISDA.2009.5356528','rtiotpaper':'10.1186/s42400-023-00178-5','maskaug':'10.1177/0926227X261487917','rubin':'10.1093/biomet/63.3.581','little':'10.1002/9781119482260','mice':'10.18637/jss.v045.i03','missforest':'10.1093/bioinformatics/btr597','knnimpute':'10.1093/bioinformatics/17.6.520','rf':'10.1023/A:1010933404324','extra':'10.1007/s10994-006-6226-1','gb':'10.1214/aos/1013203451','xgboost':'10.1145/2939672.2939785','niculescu':'10.1145/1102351.1102430','saito':'10.1371/journal.pone.0118432','fawcett':'10.1016/j.patrec.2005.10.010','davis':'10.1145/1143844.1143874','delong':'10.2307/2531595','holm':'10.2307/4615733','nadeau':'10.1023/A:1024068626366','wilcoxon':'10.2307/3001968','efron':'10.1214/aos/1176344552','leakage':'10.1016/j.patter.2023.100804','tabnet':'10.1609/aaai.v35i8.16826','shwartz':'10.1016/j.inffus.2021.11.011'}
queries={'liu':'Error Prevalence in NIDS datasets A Case Study on CIC IDS 2017 and CSE CIC IDS 2018 Liu Engelen','missingids':'The application of deep learning imputation and other advanced methods for handling missing values in network intrusion detection','missing2025':'A novel approach for handling missing data to enhance network intrusion detection system','lycos':'From CIC IDS2017 to LYCOS IDS2017 A corrected dataset for better performance'}

def get(item):
 key,val=item
 try:
  u='https://api.crossref.org/works/'+urllib.parse.quote(val,safe='/') if key in D else 'https://api.crossref.org/works?rows=1&query.bibliographic='+urllib.parse.quote(val)
  data=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ResearchBibliographyAudit/1.0'}),timeout=30))['message']
  if key not in D:data=data['items'][0]
  return key,{'status':'metadata_verified','source':'Crossref','metadata':data}
 except Exception as e:return key,{'status':'failed','error':str(e),'candidate':val}
out={}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for key,result in ex.map(get,list(D.items())+list(queries.items())):out[key]=result;print(key,result['status'],result.get('metadata',{}).get('title'),flush=True)
# Primary publisher/repository pages for sources without Crossref registration.
P={
'sklearn':('F. Pedregosa et al.','Scikit-learn: Machine learning in Python','Journal of Machine Learning Research','2011','12','2825–2830','https://jmlr.org/papers/v12/pedregosa11a.html'),
'guo':('C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger','On calibration of modern neural networks','Proc. ICML, PMLR','2017','70','1321–1330','https://proceedings.mlr.press/v70/guo17a.html'),
'demsar':('J. Demšar','Statistical comparisons of classifiers over multiple data sets','Journal of Machine Learning Research','2006','7','1–30','https://jmlr.org/papers/v7/demsar06a.html'),
'grandvalet':('Y. Bengio and Y. Grandvalet','No unbiased estimator of the variance of k-fold cross-validation','Journal of Machine Learning Research','2004','5','1089–1105','https://jmlr.org/papers/v5/grandvalet04a.html'),
'gain':('J. Yoon, J. Jordon, and M. van der Schaar','GAIN: Missing data imputation using generative adversarial nets','Proc. ICML, PMLR','2018','80','5689–5698','https://proceedings.mlr.press/v80/yoon18a.html'),
'hendrycks':('D. Hendrycks and T. Dietterich','Benchmarking neural network robustness to common corruptions and perturbations','Proc. ICLR','2019','','','https://arxiv.org/abs/1903.12261'),
'ovadia':('Y. Ovadia et al.','Can you trust your model’s uncertainty? Evaluating predictive uncertainty under dataset shift','Advances in Neural Information Processing Systems','2019','32','','https://arxiv.org/abs/1906.02530'),
'vime':('J. Yoon, Y. Zhang, J. Jordon, and M. van der Schaar','VIME: Extending the success of self- and semi-supervised learning to tabular domain','Advances in Neural Information Processing Systems','2020','33','11033–11043','https://proceedings.neurips.cc/paper/2020/hash/7d97667a3e056acab9aaf653807b4a03-Abstract.html'),
'gorishniy':('Y. Gorishniy, I. Rubachev, V. Khrulkov, and A. Babenko','Revisiting deep learning models for tabular data','Advances in Neural Information Processing Systems','2021','34','18932–18943','https://arxiv.org/abs/2106.11959'),
'grinsztajn':('L. Grinsztajn, E. Oyallon, and G. Varoquaux','Why do tree-based models still outperform deep learning on typical tabular data?','Advances in Neural Information Processing Systems','2022','35','507–520','https://arxiv.org/abs/2207.08815'),
'arp':('D. Arp et al.','Dos and don’ts of machine learning in computer security','Proc. USENIX Security','2022','','3971–3988','https://www.usenix.org/conference/usenixsecurity22/presentation/arp'),
'lightgbm':('G. Ke et al.','LightGBM: A highly efficient gradient boosting decision tree','Advances in Neural Information Processing Systems','2017','30','','https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html')}
for key,(au,title,venue,year,vol,pages,url) in P.items():
 try:
  r=urllib.request.urlopen(url,timeout=20);body=r.read();(O/(key+'_page.html')).write_bytes(body)
  out[key]={'status':'primary_page_retrieved','author_text':au,'title':title,'venue':venue,'year':year,'volume':vol,'pages':pages,'url':url,'bytes':len(body)}
 except Exception as e:out[key]={'status':'failed','error':str(e),'url':url}
(O/'references_verified.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print('TOTAL',len(out),'OK',sum(v['status']!='failed' for v in out.values()),flush=True)
