from pathlib import Path
import urllib.request,time,hashlib,json,zipfile
r=Path(__file__).resolve().parent;p=r/'data/Thursday-LYCOS.zip';url='https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/pcap_lycos/Thursday-WorkingHours.pcap_lycos.zip'
start=time.time();n=0
with urllib.request.urlopen(url,timeout=120) as a,open(p.with_suffix('.partial'),'wb') as f:
 while b:=a.read(1024*1024):
  f.write(b);n+=len(b)
  if n%(5*1024*1024)==0:print(n,round(time.time()-start),flush=True)
p.with_suffix('.partial').rename(p)
with zipfile.ZipFile(p) as z:assert z.testzip() is None;print(z.namelist(),flush=True)
(r/'results/thursday_download.json').write_text(json.dumps({'url':url,'bytes':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'crc_verified':True},indent=2));print('COMPLETE',n,flush=True)
