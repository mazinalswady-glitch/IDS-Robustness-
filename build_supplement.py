from pathlib import Path
import pandas as pd,numpy as np,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
R=Path(__file__).resolve().parent
source=(R/'build_manuscript.py').read_text();setup=source[source.index('doc=Document();'):source.index("doc.add_paragraph('Model Dependent")];setup=setup.replace("z.set(qn('w:w'),'70')","z.set(qn('w:w'),'45')");exec(setup)
sec.page_width=Inches(11);sec.page_height=Inches(8.5);sec.left_margin=sec.right_margin=Inches(.65);sec.top_margin=sec.bottom_margin=Inches(.6);doc.styles['Normal'].font.size=Pt(10.5);doc.styles['Normal'].paragraph_format.line_spacing=1.02
sec.header.paragraphs[0].text='Supplementary evidence for feature family outage sensitivity'
sec.footer.paragraphs[0].runs[0].text='Supplementary evidence  |  '
def page():doc.add_page_break()
def number(v):return f'{v:.4f}'
def prob(v):return f'{v:.3g}'
def smalltable(headers,rows,widths):return table(headers,rows,widths)
def label(v):return {'control_results':'RT','thursday_controls':'Thursday','rt':'RT','thursday':'Thursday','importance':'Info','importance_correlation':'InfoCorr','uniform':'Uniform','semantic':'Semantic'}.get(v,v)
doc.add_paragraph('Supplementary Tables S1 to S12 for Feature Family Outage Sensitivity','Title')
p('Mazin Mohammed Hamid | Northern Technical University, Iraq | mazin.mohammed@ntu.edu.iq')
p('This supplement accompanies Model Dependent Sensitivity to Semantic Feature Group Outages in Network Intrusion Detection. Tables S1 and S2 contain all 48 original and all 120 expanded comparisons. S3 reports matching diagnostics, S4 every Thursday sample and attack count, and S5 probability summaries. S6–S12 contain feature-variation and mechanism diagnostics, membership stratification and operating-point checks. S11–S12 report secondary AUROC/AP contrasts alongside Macro-F1. Full precision, per-split and per-evaluation electronic tables accompany this document in the research package; the 35,160 benchmark records are not independent network captures.')
p('The original 48-comparison family and expanded exploratory 120-comparison family are separate. Confidence intervals are corrected pointwise 95% intervals, not simultaneous family intervals. Positive contrasts mean semantic outages are less damaging than the comparator. Info matches summed marginal training-label information and constant-column fraction; InfoCorr also matches mean within-group absolute Spearman correlation. Matching is approximate and does not establish semantic causality. Mechanism results are descriptive post hoc diagnostics and do not add confirmatory p-values.')
h('Table S1 All original 48 comparisons')
a=pd.read_csv(R/'grouped_results/semantic_statistics.csv');assert len(a)==48
p('Twelve RT-IoT2022 grouped partitions; fixed probability threshold 0.5; semantic minus the mean of three equal-cardinality random-column outages. Corrected resampled t approximation with 11 degrees of freedom and test/train ratio 0.5. Holm correction across all 48 tests.')
table(['Model','Family','Difference','Lower 95%','Upper 95%','Raw p','Holm p n48'],[[r.method,r.family,number(r.difference_semantic_minus_random),number(r.ci95_lower),number(r.ci95_upper),prob(r.p_raw),prob(r.p_holm)] for r in a.itertuples()],[1.6,1.3,1.05,1.05,1.05,1.1,1.2])
h('Table S2 All expanded 120 exploratory comparisons')
a=pd.read_csv(R/'results/expanded_statistics_120.csv');assert len(a)==120
p('Twenty subsets per family and comparator are averaged within each of twelve seeds. The single pooled 120-test Holm adjustment is reported below. Corrected pointwise intervals use the same dependence approximation as S1. Dataset RT denotes RT-IoT2022; Thursday denotes the strict chronological LYCOS construction. No across-site confidence claim is made.')
table(['Dataset','Model','Family','Control','Difference','Lower 95%','Upper 95%','Holm p n120'],[[label(r.dataset),r.method,r.family,label(r.control),number(r.difference),number(r.ci95_lower),number(r.ci95_upper),prob(r.p_holm_global_120)] for r in a.itertuples()],[.8,1.45,1.2,1.05,1.0,1.0,1.0,1.25])
h('Table S3 Matching diagnostics')
p('Mean descriptors and absolute standardized discrepancies across selected subsets. Column information is mutual information with training labels after unique-decile discretization; correlation is the mean absolute pairwise training Spearman correlation. Constant denotes the fraction of exactly constant training columns. Standardization uses the 20,000-candidate pool SD. Semantic rows describe the target and therefore have zero discrepancy. Exact selected column lists and every unaggregated discrepancy are supplied electronically.')
parts=[]
for folder in ['control_results','thursday_controls']:
 d=pd.read_csv(R/folder/'matching_diagnostics.csv');d['dataset']=label(folder);parts.append(d)
a=pd.concat(parts);a['MI error']=a.mi_standardized_error.abs();a['Corr error']=a.correlation_standardized_error.abs();g=a.groupby(['dataset','family','control']).agg(n=('mi_sum','size'),mi=('mi_sum','mean'),corr=('mean_abs_spearman','mean'),constant=('constant_fraction','mean'),mierr=('MI error','mean'),correrr=('Corr error','mean')).reset_index()
table(['Dataset','Family','Control','N sets','MI sum','Mean corr','Constant','Abs MI error','Abs corr error'],[[r.dataset,r.family,label(r.control),r.n,number(r.mi),number(r.corr),number(r.constant),number(r.mierr),number(r.correrr)] for r in g.itertuples()],[.8,1.15,1.05,.65,1.0,1.0,.95,1.1,1.1])
h('Table S4 Thursday partitions and attack counts')
x=json.load(open(R/'thursday_results/protocol_manifest.json'))
p('Official archive rows 361,527; retained corrected morning rows 112,481. Full retained population: benign 110,448; web brute-force 1360; XSS 661; SQL injection 12. Training flow ends precede 12:45 UTC on 6 July 2017; calibration starts at 12:45 and ends before 13:20; test starts at 13:20 and ends before 14:00. All selected flows remain within their partition. Every seed uses 6000 training, 1500 calibration and 3000 test rows. Times and row indices are supplied electronically. BF denotes web brute-force. Three tests contain zero SQL flows; no SQL-specific accuracy claim is supported.')
rows=[]
for s in x['splits']:
 tr=s['train_attack_counts'];ca=s['cal_attack_counts'];te=s['test_attack_counts'];assert s['train_end_max']<s['cal_start_min'] and s['cal_end_max']<s['test_start_min'];rows.append([s['seed'],tr.get('benign',0),tr.get('web_bruteforce',0),ca.get('benign',0),ca.get('web_bruteforce',0),ca.get('web_xss',0),te.get('benign',0),te.get('web_xss',0),te.get('web_sql',0)])
table(['Seed','Train benign','Train BF','Cal benign','Cal BF','Cal XSS','Test benign','Test XSS','Test SQL'],rows,[.65,1.15,1.05,1.15,1.05,1.0,1.15,1.05,1.05])
h('Table S5 Probability and operating summaries')
p('The summaries below distinguish clean data from the equally weighted mean of four semantic outages. They do not aggregate natural outage probabilities. Full electronic S5 tables contain every tested condition, all comparator draws, noise/projection conditions, calibrated metrics where executed, and split-level variability. AP is scikit-learn average precision. Lower Brier is better. The expanded controls use frozen raw threshold 0.5 and do not refit calibration under corruption.')
rows=[]
for folder,file,f1,brier in [('grouped_results','semantic_raw.csv','fixed_f1','brier_raw'),('temporal_results','temporal_raw.csv','macro_f1','brier'),('control_results','raw.csv','macro_f1','brier'),('thursday_controls','raw.csv','macro_f1','brier')]:
 d=pd.read_csv(R/folder/file);scenario='scenario' if 'scenario' in d else 'control';d=d[d[scenario].isin(['clean','semantic'])].copy();d['condition']=d[scenario];d['F1']=d[f1];d['Brier']=d[brier]
 if folder=='temporal_results':d['Component']=d.window.map(lambda w:f'Tuesday W{w+1}')
 else:d['Component']={'grouped_results':'RT original','control_results':'RT expanded','thursday_controls':'Thursday'}[folder]
 g=d.groupby(['Component','method','condition'])[['F1','auroc','ap','Brier']].mean().reset_index()
 rows += [[r.Component,r.method,r.condition,number(r.F1),number(r.auroc),number(r.ap),number(r.Brier)] for r in g.itertuples()]
table(['Component','Model','Condition','Macro F1','AUROC','AP','Brier'],rows,[1.4,1.55,1.2,1.1,1.1,1.1,1.1])
h('Table S6 Feature variability by family')
p('Exact constant means a single observed value within the selected partition. Near constant means that at least 99% of rows share the modal value. Fractions below average feature indicators across twelve sampled partitions, not traffic prevalence. Mean modal fraction supplies a continuous view of concentration. No Thursday activity column is exactly or near constant in the evaluated train/test samples; identical fixed-threshold scores must not be interpreted as proof of constant inputs.')
a=pd.read_csv(R/'mechanism_results/variation_summary.csv')
table(['Dataset','Family','Partition','Feature split rows','Constant fraction','Near constant fraction','Mean modal fraction'],[[label(r.dataset),r.family,r.partition,r.n_feature_split_rows,number(r.constant_fraction),number(r.near_constant_fraction),number(r.mean_modal_fraction)] for r in a.itertuples()],[.9,1.25,1.0,1.45,1.4,1.5,1.5])
h('Table S7 Frozen model replacement diagnostics')
p('RF_median and MLP_clean are refitted with the same seeds and checked against semantic reference scores. Only the value inserted into absent columns is changed: training median versus training mean. For MLP, the mean maps to zero after its fitted StandardScaler; the median maps to its fitted standardized median coordinate. Fitted classifiers, scaling statistics and held-out records remain fixed. Effects are descriptive; no new multiplicity-adjusted mechanistic hypothesis test is claimed. Probability change is mean absolute deviation from the same model’s clean probability. Prediction change is the fraction of labels changed relative to clean predictions.')
a=pd.read_csv(R/'mechanism_results/replacement_summary.csv')
table(['Dataset','Model','Family','Fill','Semantic F1','Uniform F1','Contrast','Abs prob change','Prediction change'],[[label(r.dataset),r.method,r.family,r.replacement,number(r.semantic_f1),number(r.random_f1),number(r.contrast),number(r.mean_abs_probability_change),number(r.prediction_change)] for r in a.itertuples()],[.8,1.35,1.15,.75,1.1,1.1,1.0,1.1,1.1])
h('Table S8 Single column diagnostics and source verification')
p('For each dataset and classifier, the ten largest average Macro-F1 losses from replacing one column with its training median are listed. A positive value denotes improved Macro-F1. Effects of removing correlated columns jointly are not assumed to equal sums of single-column effects. Full scores for all retained numerical predictors and every seed accompany the electronic supplement.')
a=pd.read_csv(R/'mechanism_results/single_column_means.csv');g=a.sort_values('f1_change').groupby(['dataset','method']).head(10)
table(['Dataset','Model','Column','Mean F1 change','Mean abs probability change'],[[label(r.dataset),r.method,r.column,number(r.f1_change),number(r.probability_change)] for r in g.itertuples()],[.9,1.45,3.5,1.6,1.8])
h('Table S9 Payload minimum membership stratification')
p('Post hoc analysis of the existing RT MLP interarrival-sized uniform draws. Membership means that at least one of fwd_pkts_payload.min and flow_pkts_payload.min is removed. Each stratum is averaged within a seed before equal weighting across twelve seeds; comparator draws are not treated as independent datasets. All seeds have both strata. This comparison is not randomized with respect to other columns and supplies no confirmatory p-value. Exclusion attenuates the contrast but does not eliminate it.')
a=pd.read_csv(R/'mechanism_results/payload_membership_by_seed.csv')
table(['Seed','Contains either','N draws','Uniform F1','Semantic F1','Contrast'],[[r.seed,str(r.contains_payload_minimum),r.n_draws,number(r.uniform_f1),number(r.semantic_f1),number(r.contrast)] for r in a.itertuples()],[.8,1.5,1.,1.4,1.4,1.4])
p('Equal-seed means: containing either, 89 total draws, uniform F1 0.8204, contrast +0.1396; containing neither, 151 draws, uniform F1 0.8888, contrast +0.0712. Semantic F1 is 0.9600. The no-minimum stratum has a positive contrast in all twelve seeds, range +0.0349 to +0.1185. These columns therefore explain part of the pattern, not its entire cause. Full draw-level membership and scores accompany the electronic supplement.')
h('Table S10 Thursday MLP operating point audit')
p('Twelve further diagnostic refits reproduce all original clean and semantic MLP scores. Every test has 2934 benign and 66 attack flows (2.2% attack prevalence). TN/FP/FN/TP use attack as positive at raw threshold 0.5. An all-benign rule has Macro-F1 0.4944. Interarrival loss is all-benign in eleven seeds and detects three attacks in seed 1009; flag loss is all-benign in every seed. The training samples each contain 142 brute-force flows, but index-level checking finds 732 distinct attack rows across their union, so attack identities vary. These are overlapping conditional samples, not independent temporal replications. Calibration contains XSS; testing contains XSS/SQL whereas training attacks are brute-force only. These facts confound interpretation as temporal shift or outages alone.')
a=pd.read_csv(R/'mechanism_results/thursday_operating_points.csv')
table(['Seed','Condition','TN','FP','FN','TP','Macro F1','Attack recall'],[[r.seed,r.family,r.tn,r.fp,r.fn,r.tp,number(r.macro_f1),number(r.attack_recall)] for r in a.itertuples()],[.8,1.3,.85,.85,.85,.85,1.35,1.35])
h('Table S11 Secondary threshold and ranking contrasts for the original 48 comparisons')
p('Each cell reports semantic minus comparator mean [corrected pointwise 95% interval]. These are secondary descriptive comparisons on already computed scores, not new confirmatory tests. The 12 seed differences are formed after averaging the three random draws within seed. Intervals use the same corrected resampling approximation, test/train ratio 0.5 and 11 degrees of freedom. They are not simultaneous or multiplicity-adjusted; no secondary p-values are computed. AP is non-interpolated average precision. All raw values and per-seed differences are supplied electronically. Different metrics measure different properties, and a point-estimate sign reversal does not establish a statistically resolved ranking reversal.')
rank=pd.read_csv(R/'results/ranking_contrasts_secondary.csv')
def effect_cell(z,metric):
 v=z.loc[metric];return f"{v.difference:.4f} [{v.ci95_lower:.4f}, {v.ci95_upper:.4f}]"
rows=[]
for (method,family,control),v in rank[rank.component=='primary_RT'].groupby(['method','family','control']):
 z=v.set_index('metric');rows.append([method,family]+[effect_cell(z,k) for k in ['macro_f1','auroc','ap']])
assert len(rows)==48
table(['Model','Family','Delta Macro F1 [95%]','Delta AUROC [95%]','Delta AP [95%]'],rows,[1.45,1.2,2.3,2.3,2.3])
h('Table S12 Secondary threshold and ranking contrasts for all 120 expanded comparisons')
p('Same interval convention and descriptive status as S11. Twenty comparator draws are averaged per seed for uniform, information-matched (Info), or information-and-correlation-matched (InfoCorr) controls. The 120 Macro-F1 comparisons and their previously reported pooled Holm adjustment are unchanged; the added AUROC/AP comparisons are not included in that existing Macro-F1 test family or presented as further adjusted findings. Thursday intervals are conditional on one chronological construction with overlapping resampling, subtype shift and fixed 2.2% test attack prevalence. AP is prevalence dependent, so within-split comparisons do not justify comparing raw AP across datasets.')
rows=[]
for (dataset,method,family,control),v in rank[rank.component!='primary_RT'].groupby(['component','method','family','control']):
 z=v.set_index('metric');rows.append(['RT' if dataset=='expanded_RT' else dataset,method,family,label(control)]+[effect_cell(z,k) for k in ['macro_f1','auroc','ap']])
assert len(rows)==120
table(['Dataset','Model','Family','Control','Delta Macro F1 [95%]','Delta AUROC [95%]','Delta AP [95%]'],rows,[.7,1.25,1.05,.9,1.85,1.85,1.85])
h('Verification of reference 24',2)
p('Reference [24] was verified against publisher metadata and the public abstract on 13 November 2026: https://journals.sagepub.com/doi/10.1177/0926227X261487917 . Full text remains restricted; no full reading or faithful reproduction is claimed.')
doc.save(R/'IDS_Robustness_Supplement_S1_S12.docx');print('Saved supplement',len(doc.tables),'tables;',len(doc.paragraphs),'paragraphs')
