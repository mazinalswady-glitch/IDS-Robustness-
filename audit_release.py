from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent
counts=[]
for directory,file,expected in [('grouped_results','semantic_raw.csv',3888),('temporal_results','temporal_raw.csv',1872),('control_results','raw.csv',14700),('thursday_controls','raw.csv',14700)]:
 d=pd.read_csv(R/directory/file);f=pd.read_csv(R/directory/'fits.csv');assert len(d)==expected
 keys=['split_seed','method','scenario','group','replicate'] if directory=='grouped_results' else ['window','seed','method','scenario','group','replicate'] if directory=='temporal_results' else ['seed','method','family','control','replicate'];assert not d.duplicated(keys).any()
 for c in ['auroc','ap']:assert d[c].between(-1e-12,1+1e-12).all()
 
 if directory in ['control_results','thursday_controls']:assert d.groupby(['seed','method']).size().eq(245).all()
 counts.append(dict(component=directory,fits=len(f),metric_records=len(d)))
assert sum(x['fits'] for x in counts)==408 and sum(x['metric_records'] for x in counts)==35160
m=json.load(open(R/'thursday_results/protocol_manifest.json'))
for x in m['splits']:
 assert x['train_end_max']<x['cal_start_min'] and x['cal_end_max']<x['test_start_min']
 ids=np.load(R/f"thursday_results/split_{x['seed']}.npz")
 for a,b in [('train','test'),('calibration','test'),('train','calibration')]:assert not set(ids[a])&set(ids[b])
for name in ['control_results','thursday_controls']:
 draws=json.load(open(R/name/'draws.json'));meta=json.load(open(R/'grouped_results/protocol_manifest.json'))
 if name=='control_results':groups=meta['semantic_groups']
 else:
  cols=m['features'];groups={g:[c for c in cols if ('iat_' in c if g=='interarrival' else 'pkt_len_' in c if g=='payload' else c.startswith(('active_','idle_')) if g=='activity' else 'flag_' in c)] for g in meta['semantic_groups']}
 for draw in draws:
  assert len(draw['columns'])==len(groups[draw['family']]);assert len(draw['columns'])==len(set(draw['columns']))
  if draw['control']!='semantic':assert set(draw['columns'])!=set(groups[draw['family']])
q=pd.read_csv(R/'results/expanded_statistics_120.csv');assert len(q)==120 and int((q.p_holm_global_120<.05).sum())==16
for file,expected in [('data/rtiot.csv',json.load(open(R/'grouped_results/protocol_manifest.json'))['source_sha256']),('data/Thursday-LYCOS.zip',m['source']['sha256'])]:
 p=R/file
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
result={'checks':'passed','components':counts,'total_fits':408,'total_metric_records':35160,'expanded_tests':120,'expanded_holm_findings':16,'scope':'Conditional exploratory comparisons; no causal semantic claim; no public repository or DOI issued'}
result['diagnostic_refits']=len(pd.read_csv(R/'mechanism_results/fits.csv'));result['diagnostic_replacement_evaluations']=len(pd.read_csv(R/'mechanism_results/replacement_raw.csv'));result['diagnostic_single_column_evaluations']=len(pd.read_csv(R/'mechanism_results/single_column_raw.csv'));assert result['diagnostic_refits']==84
result['additional_operating_point_refits']=12;result['additional_operating_point_evaluations']=len(pd.read_csv(R/'mechanism_results/thursday_operating_points.csv'));assert result['additional_operating_point_evaluations']==60
result['membership_diagnostic_draws']=len(pd.read_csv(R/'mechanism_results/payload_membership_draws.csv'));assert result['membership_diagnostic_draws']==240
rank=pd.read_csv(R/'results/ranking_contrasts_secondary.csv');assert len(rank)==504;result['secondary_outcome_contrasts']=504;result['secondary_ranking_contrasts']=336;result['secondary_p_values_computed']=False;result['secondary_extra_fits']=0
(R/'results/release_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
