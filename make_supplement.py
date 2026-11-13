from pathlib import Path
import pandas as pd,json,shutil
R=Path(__file__).resolve().parent;O=R/'supplement';O.mkdir(exist_ok=True)
shutil.copyfile(R/'grouped_results/semantic_statistics.csv',O/'Table_S1_original_48_tests.csv')
shutil.copyfile(R/'results/expanded_statistics_120.csv',O/'Table_S2_expanded_120_tests.csv')
frames=[]
for name in ['control_results','thursday_controls']:
 d=pd.read_csv(R/name/'matching_diagnostics.csv');d['dataset']=name;frames.append(d)
pd.concat(frames,ignore_index=True).to_csv(O/'Table_S3_matching_diagnostics.csv',index=False)
a=json.load(open(R/'thursday_results/protocol_manifest.json'));pd.json_normalize(a['splits']).fillna(0).to_csv(O/'Table_S4_thursday_splits_and_attack_counts.csv',index=False)
for name in ['grouped_results','temporal_results','control_results','thursday_controls']:
 source=R/name/('semantic_raw.csv' if name=='grouped_results' else 'temporal_raw.csv' if name=='temporal_results' else 'raw.csv');shutil.copyfile(source,O/f'Table_S5_{name}_all_metrics.csv')
(O/'INDEX.md').write_text('''# Supplementary tables
S1: all 48 original corrected resampled comparisons and their Holm adjustment.
S2: all 120 expanded exploratory comparisons; p_holm_global_120 is the pooled adjustment used in the manuscript. Per-dataset p_holm values are audit-only.
S3: every selected control subset descriptor and residual information/correlation mismatch. The corresponding exact column lists are in draws.json for each dataset.
S4: chronological split boundaries and per-attack counts for all twelve Thursday samples.
S5: full metric records for each of the four executed experiment components. Each row is an evaluation record, not an independent capture. Clip-only/project-only duplicates across noise multipliers are labeled controls.

All intervals are corrected pointwise intervals, not simultaneous family intervals. Laboratory datasets, overlapping samples and imperfect matching constrain inference. Source data and third-party article copies are not redistributed.
''')
print('Supplementary tables generated')
# Standalone mechanism evidence is part of the current submission supplement.
if (R/'mechanism_results/replacement_summary.csv').exists():
 for dest,src in [('Table_S6_feature_variability.csv','variation_summary.csv'),('Table_S6_feature_variability_all_rows.csv','feature_variation.csv'),('Table_S7_replacement_summary.csv','replacement_summary.csv'),('Table_S7_replacement_all_rows.csv','replacement_raw.csv'),('Table_S8_single_column_means.csv','single_column_means.csv'),('Table_S8_single_column_all_rows.csv','single_column_raw.csv')]:shutil.copyfile(R/'mechanism_results'/src,O/dest)
 (O/'INDEX.md').write_text((O/'INDEX.md').read_text()+'\nS6: all feature variability checks, exact constants and >=99% modal columns.\nS7: frozen-model median/mean replacement diagnostics, descriptive only.\nS8: all single-column interventions.\nThe standalone Word supplement explicitly contains all48/120 tests and all Thursday sample counts. Both expanded benchmark components have245 conditions per fitted model and14,700 rows. Full electronic evaluation records remain attached in this directory.\n')

for dest,src in [('Table_S9_payload_membership_draws.csv','payload_membership_draws.csv'),('Table_S9_payload_membership_by_seed.csv','payload_membership_by_seed.csv'),('Table_S9_payload_membership_summary.csv','payload_membership_summary.csv'),('Table_S10_thursday_operating_points.csv','thursday_operating_points.csv'),('Table_S10_training_overlap.json','thursday_training_overlap.json')]:shutil.copyfile(R/'mechanism_results'/src,O/dest)
(O/'INDEX.md').write_text((O/'INDEX.md').read_text()+'\nS9: post hoc membership strata for the two RT payload minima, including all 240 draws and seed-balanced summaries.\nS10: all 60 Thursday MLP confusion matrices and training attack identity audit from 12 further diagnostic refits.\n\n')

rank=pd.read_csv(R/'results/ranking_contrasts_secondary.csv')
rank[rank.component=='primary_RT'].to_csv(O/'Table_S11_primary_ranking_contrasts.csv',index=False)
rank[rank.component!='primary_RT'].to_csv(O/'Table_S12_expanded_ranking_contrasts.csv',index=False)
shutil.copyfile(R/'results/ranking_contrasts_by_seed.csv',O/'Table_S11_S12_ranking_by_seed.csv')
(O/'INDEX.md').write_text((O/'INDEX.md').read_text()+'\nS11: all 48 original contrasts for Macro-F1, AUROC and AP; corrected pointwise intervals, descriptive.\nS12: all 120 expanded contrasts for those outcomes, including all three control types; secondary AUROC/AP comparisons carry no new confirmatory p-values.\n')
