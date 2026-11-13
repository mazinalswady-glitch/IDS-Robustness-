from pathlib import Path
import zipfile,hashlib,json
import pandas as pd,numpy as np
from sklearn.model_selection import train_test_split
R=Path(__file__).resolve().parent;P=R/'data/Thursday-LYCOS.zip'
with zipfile.ZipFile(P) as z:
 assert z.testzip() is None;a=pd.read_csv(z.open('Thursday-WorkingHours.pcap_lycos.csv'))
raw=len(a);a=a[a.timestamp<1499353200000000].copy();a['attack']='benign';common=a.src_addr.eq('172.16.0.1')&a.dst_addr.eq('192.168.10.50')&a.ip_prot.eq(6)
for name,lo,hi in [('web_bruteforce',1499343300000000,1499346000000000),('web_xss',1499346935000000,1499348100000000),('web_sql',1499348400000000,1499348576000000)]:a.loc[common&a.timestamp.between(lo,hi),'attack']=name
a['label']=a.attack.ne('benign').astype(int);cols=[c for c in a.select_dtypes('number') if c not in ['flow_id','src_addr','src_port','dst_addr','dst_port','ip_prot','timestamp','label']];a=a[np.isfinite(a[cols]).all(1)&a.flow_duration.ge(0)].sort_values('timestamp',kind='stable').reset_index(drop=True)
a.to_csv(R/'data/lycos_thursday_labelled.csv',index=False);out=R/'thursday_results';out.mkdir(exist_ok=True)
start=a.timestamp.to_numpy();end=start+a.flow_duration.to_numpy();t0=pd.Timestamp('2017-07-06T12:45:00Z').value//1000;t1=pd.Timestamp('2017-07-06T13:20:00Z').value//1000;t2=pd.Timestamp('2017-07-06T14:00:00Z').value//1000
parts=[np.flatnonzero(end<t0),np.flatnonzero((start>=t0)&(end<t1)),np.flatnonzero((start>=t1)&(end<t2))];splits=[]
for seed in range(1001,1013):
 p=[train_test_split(ids,train_size=n,stratify=a.label.to_numpy()[ids],random_state=seed)[0] if len(ids)>n else ids for ids,n in zip(parts,[6000,1500,3000])];assert end[p[0]].max()<start[p[1]].min() and end[p[1]].max()<start[p[2]].min();np.savez_compressed(out/f'split_{seed}.npz',train=p[0],calibration=p[1],test=p[2]);splits.append(dict(seed=seed,train=len(p[0]),calibration=len(p[1]),test=len(p[2]),train_end_max=float(end[p[0]].max()),cal_start_min=int(start[p[1]].min()),cal_end_max=float(end[p[1]].max()),test_start_min=int(start[p[2]].min()),train_attack_counts=a.iloc[p[0]].attack.value_counts().to_dict(),cal_attack_counts=a.iloc[p[1]].attack.value_counts().to_dict(),test_attack_counts=a.iloc[p[2]].attack.value_counts().to_dict()))
meta={'features':cols,'raw_archive_rows':raw,'retained_morning_rows':len(a),'attack_counts':a.attack.value_counts().to_dict(),'partitions_available':[{ 'rows':len(ids),'attack_counts':a.iloc[ids].attack.value_counts().to_dict()} for ids in parts],'source':json.load(open(R/'results/thursday_download.json')),'splits':splits,'scope':'Official LYCOS Thursday morning; authors exclude afternoon; training brute-force, calibration brute-force and XSS, test XSS and SQL; not independent network/site'};(out/'protocol_manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps({k:v for k,v in meta.items() if k not in ['features','splits']},indent=2),flush=True)
