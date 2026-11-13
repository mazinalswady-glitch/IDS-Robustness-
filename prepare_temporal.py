from pathlib import Path
import hashlib,zipfile,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;src=R/'data/Tuesday-LYCOS.zip'
with zipfile.ZipFile(src) as z:
 assert z.testzip() is None
 member='Tuesday-WorkingHours.pcap_lycos.csv';a=pd.read_csv(z.open(member))
assert a.label.eq('NeedLabel').all()
positive=a.src_addr.eq('172.16.0.1')&a.dst_addr.eq('192.168.10.50')&(a.timestamp.between(1499170620000000,1499175000000000)|a.timestamp.between(1499188140000000,1499191860000000))
a['label']=positive.astype(int)
drop=['flow_id','src_addr','src_port','dst_addr','dst_port','ip_prot','timestamp','label'];features=[c for c in a.select_dtypes('number') if c not in drop]
keep=np.isfinite(a[features]).all(1)&a.flow_duration.ge(0);a=a[keep].sort_values('timestamp',kind='stable').reset_index(drop=True)
a.to_csv(R/'data/lycos_tuesday_labelled.csv',index=False)
meta={'source_url':'https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/pcap_lycos/Tuesday-WorkingHours.pcap_lycos.zip','complete_archive_bytes':src.stat().st_size,'complete_archive_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'complete_archive_crc_verified':True,'selected_member':member,'full_csv_rows':len(positive),'retained_rows':len(a),'min_timestamp_us':int(a.timestamp.min()),'max_timestamp_us':int(a.timestamp.max()),'label_code_url':'https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/labelling.py','label_code_sha256':hashlib.sha256((R/'sources/lycos_labelling.py').read_bytes()).hexdigest(),'features':features,'positive_rows':int(a.label.sum()),'scope':'Complete official author-hosted LYCOS regenerated CICIDS2017 Tuesday CSV; temporal test windows cover FTP brute-force/benign traffic; not Engelen/Liu release or all capture days'}
(R/'results/temporal_source.json').write_text(json.dumps(meta,indent=2));print('Full Tuesday source prepared',len(a),'positive',a.label.sum())
