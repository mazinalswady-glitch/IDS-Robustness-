"""Download official sources and verify the exact bytes used by this release."""
from pathlib import Path
import hashlib,urllib.request,time,os
R=Path(__file__).resolve().parent;(R/'data').mkdir(exist_ok=True);(R/'sources').mkdir(exist_ok=True)
SOURCES=[('data/rtiot.csv','https://archive.ics.uci.edu/static/public/942/data.csv','289632f1b01a317e86a3cce5e276246ad64e1e6ac03ffd3b16202b9d016d7d90'),('data/Tuesday-LYCOS.zip','https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/pcap_lycos/Tuesday-WorkingHours.pcap_lycos.zip','f86c47defd159772dc717ce5b717369c04d0ad460d4e76fd6056ec38fbaa7405'),('sources/lycos_labelling.py','https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/labelling.py','0e9d08f69657e73b5e24e707f2ddcc06cd5e40fbdf8e64be61ea1836d96aa9a1')]
SOURCES.append(('data/Thursday-LYCOS.zip','https://maupiti-git.univ-lemans.fr/lycos/lycos-ids2017/raw/master/pcap_lycos/Thursday-WorkingHours.pcap_lycos.zip','81e98ffcc0141c9a7bb2686c31af57367fbbb33401f03e78dfdc6a9fd47b6c2f'))
for relative,url,expected in SOURCES:
 dest=R/relative
 if dest.exists():
  if hashlib.sha256(dest.read_bytes()).hexdigest()!=expected:raise ValueError('Existing source hash mismatch: '+relative)
  print('Verified',relative);continue
 for attempt in range(3):
  temp=dest.with_suffix(dest.suffix+'.partial')
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'IDS-Semantic-Outage-Reproducibility/0.3'})
   with urllib.request.urlopen(req,timeout=120) as response,open(temp,'wb') as out:
    while block:=response.read(1024*1024):out.write(block)
   if hashlib.sha256(temp.read_bytes()).hexdigest()!=expected:raise ValueError('Downloaded source hash mismatch: '+relative)
   os.replace(temp,dest);print('Downloaded and verified',relative);break
  except Exception:
   temp.unlink(missing_ok=True)
   if attempt==2:raise
   time.sleep(5)
