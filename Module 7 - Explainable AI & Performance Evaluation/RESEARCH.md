# Module 7 Research Notes

## Performance evaluation

RMSE emphasizes larger errors, MAE measures typical absolute error, and R2
measures explained variance relative to a mean baseline. Percentage errors need
care around zero actual values, so this module reports MAPE together with SMAPE
and WAPE. Bias is included to reveal systematic over- or under-prediction that
aggregate absolute errors can hide.

Decision-pipeline evaluation cannot use forecasting metrics alone. Module 7
therefore measures agent recommendation coverage, scenario ranking quality,
and the energy/cost/carbon changes produced by optimization.

## Monitoring and retraining

Monitoring compares current metrics with an approved reference and evaluates
feature drift separately. A model is not retrained simply because a timer
expired; the trigger records the metric degradation or drift that justified
the action. This supports traceable operation in line with NIST's emphasis on
measuring deployed performance and monitoring models:
https://doi.org/10.6028/NIST.AI.100-1

Candidate retraining uses a holdout comparison and explicit promotion. Existing
models are not overwritten automatically. This is important here because the
provided Joblib models were serialized using scikit-learn 1.9.0 while the local
runtime uses 1.7.1. Scikit-learn documents cross-version Joblib/pickle loading
as unsupported and recommends preserving the training recipe, data reference,
scores, and dependency versions:
https://scikit-learn.org/stable/model_persistence.html

## SHAP and feature importance

Lundberg and Lee describe SHAP as additive feature attribution based on Shapley
values, assigning each feature a contribution to an individual prediction:
https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html

The project models use at most six features. Instead of depending on an
external SHAP package, `shap_analyzer.py` enumerates every coalition and applies
the Shapley weighting formula exactly against a mean reference record. It then
verifies that the base value plus all contributions reproduces the prediction.

Random Forest `feature_importances_` supplies a fast global ranking. Optional
permutation importance measures how much prediction RMSE worsens when a feature
is shuffled. The two methods answer different questions:

- native/permutation importance: which features matter across the dataset;
- SHAP: why this individual prediction differs from its reference value.

## Isolation Forest

Isolation Forest directly isolates unusual observations through randomized
partitioning rather than first estimating a normal-data density. The original
method was introduced by Liu, Ting, and Zhou at ICDM 2008:
https://doi.org/10.1109/ICDM.2008.17

It suits this project because historical operating data exists but confirmed
fault labels do not. The detector reports both model labels and continuous
scores; engineers should treat these as investigation signals, not automatic
proof of equipment failure.

## Limitations and next steps

- The initial monitoring run establishes a baseline; genuine degradation
  monitoring requires future labeled outcomes.
- Mean-shift drift detects location changes but not every distribution change.
- Single-reference SHAP is exact for its chosen reference but differs from
  distributional SHAP using many conditional background samples.
- Isolation Forest contamination is an operating assumption and should be
  calibrated using reviewed plant events.
- Person 3 must connect these components to a scheduled final controller.
