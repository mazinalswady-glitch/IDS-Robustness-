# Model dependent sensitivity to feature family outages

Version 0.8.0 — Mazin Mohammed Hamid, Northern Technical University, Iraq.

This study compares coherent feature-family outages with equal-cardinality random losses. The interpretation is **model dependent**, not a universal claim that random losses understate damage. Additional controls approximately match training-label information, constant-column fraction and within-group correlation. Matching is imperfect and cannot establish semantic causality.

## Evidence and scope
The original RT-IoT2022 experiment uses 12 grouped partitions and 12 configurations. It has four Holm-adjusted findings among 48 contrasts, including a borderline result. Five representative configurations are refitted with 20 uniform subsets, 20 information-matched subsets and 20 joint information/correlation matches per family. A separate-day replication uses the full official corrected LYCOS Thursday archive, strict temporal boundaries and 12 sampling/training seeds. The retained morning population contains web brute-force, XSS and only 12 SQL-injection flows; some sampled tests contain no SQL flow. The earlier Tuesday case covers FTP/benign traffic. These are limited laboratory environments, not independent network deployments.

The complete executed release contains 408 fits/refits and 35,160 evaluation records: original RT 144 / 3,888; Tuesday 144 / 1,872; RT controls 60 / 14,700; Thursday 60 / 14,700. Refits are not additional independent datasets. Twenty candidate subsets are averaged within a split, not treated as independent model runs. The expanded analysis is exploratory and reports a pooled Holm family of 120 contrasts, alongside corrected pointwise intervals and matching diagnostics.

## Evidence audit and accompanying supplement
A standalone IDS_Robustness_Supplement_S1_S12.docx contains all 48 original and 120 expanded tests, matching summaries, all Thursday per-seed attack counts, probability summaries and feature/diagnostic tables. Full electronic records are in supplement/. The RT expanded clean condition was missing from the earlier export and has been recomputed and restored; each fit now has 245 conditions, matching Thursday. All 120 outage contrasts/p-values are unchanged.

An additional84 diagnostic refits produce84 clean rechecks,8064 replacement interventions and3696 single-column interventions, stored separately in mechanism_results/. These post hoc diagnostics do not add independent environments. Thursday activity columns are neither constant nor >=99% modal; unchanged F1 reflects unchanged thresholded predictions under median filling despite probability movement. See the paper and S6–S8. The future-validation protocol is unregistered and was written after current outcomes.

## Reproduce
Python 3.12 and CPU scikit-learn; pinned versions are in requirements.txt. Use an isolated environment. On Windows activate with `.venv\Scripts\activate` instead of the Unix activation below.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fetch_data.py
python prepare_temporal.py
python run_semantic.py
python run_temporal.py
python prepare_thursday.py
python run_controls.py
python run_controls_v2.py --dataset thursday
python analyze_semantic.py
python analyze_temporal.py
python run_mechanism.py
python analyze_controls.py
python analyze_mechanism.py
python make_supplement.py
python build_supplement.py
```

Official university downloads can be slow. Raw archives and expanded CSVs require several hundred MB. Data bytes are not redistributed. SHA-256 and archive CRC checks document the exact sources used. Original provider terms continue to apply.

For fresh primary training, move the included grouped_results directory aside first: run_semantic.py resumes completed split/method checkpoints. Other training scripts overwrite their own outputs and must not run concurrently against the same output directory. To audit shipped results and regenerate charts without retraining, run only the analysis scripts and make_supplement.py (and build_supplement.py for the Word supplement). Source checks occur in fetch_data.py; record and reject unexpected provider changes.

Optional manuscript generation requires python-docx:

```bash
pip install python-docx
python build_manuscript.py
```

## Supplementary material
See `supplement/INDEX.md` for Tables S1–S12. Raw metric records, split indices, executable group membership, selected control subsets, matching discrepancies, fit warnings and source provenance are retained in the corresponding result directories. Five original figures and two expanded-control figures are supplied as PNG and vector PDF. Noise interventions are displayed as grouped bars because the categories are unordered.

`PROTOCOL.md` gives exact methods and statistical limits. `sources/references_verified.json` contains the bibliographic audit; failed unused candidates remain explicitly marked failed. `references_numbered.json` maps the final 41 IEEE references. Unused XGBoost/LightGBM and unused-test citations were removed from the manuscript. Their metadata may remain in the historical audit and does not imply execution.

## Access and publication
Reference 24 was verified against the publisher record and DOI 10.1177/0926227X261487917; full text remains restricted and no faithful MaskAug reproduction is claimed. Generic masking is not labeled MaskAug.

The submission archive supplies code and evaluation records as Supplementary Software. No Zenodo DOI has been issued. The GitHub repository created by the author was empty when checked on 2026-11-13; it must receive the release before its URL can substantiate public code availability. Original dataset bytes are not redistributed.

## Revision 0.8.0 diagnostics

## Secondary ranking analysis
Run `python analyze_ranking_contrasts.py` to regenerate all 48 original and 120 expanded semantic-minus-comparator contrasts for Macro-F1, AUROC and AP. This analysis reuses existing scores; it adds no fits or new confirmatory p-values. Tables S11 and S12 give corrected pointwise intervals, not simultaneous intervals. Unchanged average AUROC does not establish equivalence, unchanged AP, or purely threshold-mediated damage.
