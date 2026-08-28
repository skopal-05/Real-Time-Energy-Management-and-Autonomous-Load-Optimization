# Module 7 - Explainable AI & Performance Evaluation

Module 7 is the final evaluation, explainability, anomaly detection, performance monitoring, and integration layer of the Digital Twin system.

It integrates the outputs of Modules 3–6 and evaluates the complete decision pipeline:

Module 3 - Forecasting
        ↓
Module 4 - Multi-Agent Intelligence
        ↓
Module 5 - Scenario Simulation
        ↓
Module 6 - Optimization Engine
        ↓
Module 7 - Explainable AI & Performance Evaluation


## Objectives

The main objectives of Module 7 are:

- Evaluate forecasting model performance.
- Compare baseline and optimized operating states.
- Benchmark energy, cost, and carbon improvements.
- Monitor forecasting model degradation.
- Detect numerical feature drift.
- Generate SHAP-based local explanations.
- Calculate global feature importance.
- Detect abnormal operating conditions using Isolation Forest.
- Support safe candidate-model retraining.
- Validate the complete Module 3 → Module 7 pipeline.
- Generate structured JSON reports for downstream use.


## Module Architecture

Module 7 - Explainable AI & Performance Evaluation
│
├── evaluation/
│   ├── benchmark.py
│   ├── evaluation_validator.py
│   ├── metrics.py
│   ├── performance_evaluator.py
│   └── __init__.py
│
├── explainability/
│   ├── explanation_generator.py
│   ├── feature_importance.py
│   ├── shap_analyzer.py
│   └── __init__.py
│
├── anomaly_detection/
│   ├── anomaly_detector.py
│   ├── anomaly_validator.py
│   ├── isolation_forest.py
│   └── __init__.py
│
├── retraining/
│   ├── model_monitor.py
│   ├── retraining_pipeline.py
│   ├── retraining_validator.py
│   └── __init__.py
│
├── integration/
│   ├── final_controller.py
│   ├── integration_test.py
│   ├── integration_validator.py
│   └── __init__.py
│
├── tests/
│   ├── test_person_1.py
│   ├── test_person_2.py
│   └── __init__.py
│
├── outputs/
│   ├── performance/
│   ├── explanations/
│   ├── anomalies/
│   └── reports/
│
├── README.md
├── RESEARCH.md
├── MANUAL_CHECKS.md
├── requirements.txt
├── run_person_1_2.py
└── __init__.py


# 1. Performance Evaluation

The evaluation package evaluates forecasting outputs and compares optimized system performance against the baseline.

## Regression Metrics

metrics.py provides the following forecasting metrics:

- MAE
- MSE
- RMSE
- MAPE
- SMAPE
- WAPE
- R²
- Bias
- Maximum Error

The implementation validates:

- Non-empty actual values.
- Matching actual and predicted shapes.
- Finite numerical values.

Example metric structure:

{
    "sample_count": 10,
    "mae": 1.23,
    "mse": 2.14,
    "rmse": 1.46,
    "mape_percent": 2.31,
    "smape_percent": 2.27,
    "wape_percent": 2.18,
    "r2": 0.94,
    "bias": 0.12,
    "max_error": 3.21
}


# 2. Optimization Benchmarking

benchmark.py compares Module 6 baseline and optimized operating states.

The benchmark evaluates:

### Energy

- Energy objective
- Site consumption
- Grid import
- Grid export
- Curtailed energy

### Cost

- Net operating cost

### Carbon

- Total CO₂e emissions

Each metric is classified as:

- improved
- regressed
- unchanged

The benchmark also calculates:

- Absolute change
- Relative percentage change
- Direction of improvement
- Total metric count

For the current integrated pipeline:

Benchmark improved  : 3
Benchmark regressed : 0
Benchmark unchanged  : 4


# 3. Explainable AI

The explainability package provides tools for interpreting forecasting models.

## SHAP Analysis

shap_analyzer.py implements exact single-reference Shapley value calculation.

The implementation:

1. Creates a reference point from the background data.
2. Enumerates feature coalitions.
3. Generates model predictions for each coalition.
4. Calculates each feature's Shapley contribution.
5. Verifies the additivity relationship.

The implementation is designed for small forecasting models with a limited number of features.

The output contains:

- Base value
- Prediction
- Feature value
- SHAP value
- Feature effect
- Contribution sum
- Additivity error

Example:

{
    "feature": "machine_load_kw",
    "feature_value": 85.0,
    "shap_value": 2.41,
    "effect": "increases"
}


# 4. Global Feature Importance

feature_importance.py provides two approaches.

## Native Feature Importance

For models exposing feature_importances_, the module:

- Extracts model-native importance.
- Normalizes the values.
- Ranks features.

## Permutation Importance

The module also supports permutation-based importance.

For each feature:

1. The feature values are shuffled.
2. Model performance is recalculated.
3. RMSE degradation is measured.
4. Importance is calculated from the performance change.

This provides an additional model-independent interpretation of feature relevance.


# 5. Explanation Generation

explanation_generator.py converts raw SHAP and feature-importance results into structured explanations.

For each explained prediction, the module identifies the most influential features and generates a readable summary.

Example:

machine_load_kw increases the prediction by 2.410;
motor_temperature_c decreases the prediction by 0.830

The generated explanation also verifies SHAP additivity.


# 6. Anomaly Detection

The anomaly_detection package detects unusual operating conditions.

## Isolation Forest

isolation_forest.py provides a validated wrapper around Scikit-learn's Isolation Forest.

The model:

- Learns normal operating patterns.
- Calculates anomaly scores.
- Classifies records as normal or anomaly.

Output includes:

{
    "row_index": 0,
    "raw_score": 0.12,
    "anomaly_score": 0.73,
    "label": "anomaly",
    "is_anomaly": true
}

The anomaly score is normalized to the range:

0 → 1


# 7. Anomaly Validation

anomaly_validator.py validates anomaly detection outputs.

It checks:

- Feature names.
- Record count.
- Anomaly count.
- Record labels.
- Anomaly score range.
- Consistency between anomaly labels and anomaly count.

Valid labels are:

normal
anomaly


# 8. Model Monitoring

The retraining package contains model monitoring utilities.

model_monitor.py detects:

- MAE degradation.
- RMSE degradation.
- R² degradation.
- Low model quality.
- Numeric feature drift.

Default monitoring thresholds include:

Error degradation threshold : 20%
R² drop threshold           : 0.10
Minimum acceptable R²       : 0.50
Feature drift threshold     : 0.75

The monitor returns:

healthy

or:

degraded

and determines whether retraining is required.


# 9. Feature Drift Detection

Feature drift is detected by comparing reference and current feature distributions.

The implementation calculates standardized mean shift:

mean_shift =
abs(current_mean - reference_mean)
/
reference_standard_deviation

A feature is marked as drifted when the shift exceeds the configured threshold.


# 10. Safe Model Retraining

retraining_pipeline.py provides a controlled candidate-model retraining workflow.

The pipeline:

1. Splits available data into training and testing sets.
2. Evaluates the current model.
3. Trains a candidate model.
4. Evaluates the candidate.
5. Calculates RMSE improvement.
6. Accepts or rejects the candidate.
7. Promotes the model only when the acceptance criteria are satisfied.

The current model is not overwritten by default.

This prevents an inferior candidate model from automatically replacing the existing model.


# 11. Retraining Validation

retraining_validator.py validates monitoring and retraining reports.

It checks:

- Monitoring status.
- Retraining requirement.
- Candidate metrics.
- Candidate acceptance.
- Promotion status.

Valid retraining states include:

not_required
candidate_rejected
candidate_accepted


# 12. Final Integration

The integration package connects Modules 3–6 with Module 7.

## Final Controller

final_controller.py loads:

Module 3
forecast_output.json

Module 4
recommendations.json

Module 5
best_scenario.json
scenario_comparison.json

Module 6
optimization_report.json
optimized_state.json

It then produces the Module 7 evaluation output.


# 13. End-to-End Integration Test

integration_test.py validates the complete pipeline in seven stages.

[1/7] Initialize Module 7
        ↓
[2/7] Check Modules 3–6 outputs
        ↓
[3/7] Load artifacts
        ↓
[4/7] Validate upstream contracts
        ↓
[5/7] Run final Module 7 controller
        ↓
[6/7] Validate Module 7 outputs
        ↓
[7/7] Generate final integration summary

The complete test verifies:

- Module 3 forecast contract.
- Module 4 recommendation contract.
- Module 5 scenario contract.
- Module 6 optimization contract.
- Module 6 optimized-state contract.
- Module 7 performance output.
- Module 7 monitoring output.
- Module 7 explainability status.
- Module 7 anomaly status.


# 14. Current End-to-End Result

The current Module 3 → Module 7 pipeline successfully passes the complete integration test.

Module 3 → Forecasting       : PASS
Module 4 → Multi-Agent       : PASS
Module 5 → Scenario          : PASS
Module 6 → Optimization      : PASS
Module 7 → Evaluation        : PASS

Current integrated results:

Recommendations              : 14
Scenarios evaluated          : 5
Best scenario                : cost_saver
Best scenario score          : 100.0
Optimization feasible        : True
Benchmark improved           : 3
Benchmark regressed          : 0
Benchmark unchanged          : 4


# 15. Optional Components

The Module 7 architecture includes three optional runtime components:

Model Monitoring
Explainability
Anomaly Detection

In the current end-to-end integration, their status is:

Model monitoring     : not_evaluated
Explainability       : not_executed
Anomaly detection    : not_executed

This is intentional.

The current Module 3 forecast_output.json provides future forecast values but does not contain the historical actual-vs-predicted evaluation data, SHAP background feature matrix, or a dedicated anomaly-detection dataset required to execute these components meaningfully.

Therefore, the integration does not generate fabricated performance, SHAP, or anomaly results.

The corresponding Module 7 utilities are implemented and can be executed when the required datasets and models are connected.


# 16. Generated Outputs

After running the final integration test, Module 7 generates:

outputs/
│
├── anomalies/
│   ├── anomaly_report.json
│   └── anomaly_status.json
│
├── explanations/
│   ├── feature_importance.json
│   ├── shap_explanations.json
│   └── explainability_status.json
│
├── performance/
│   ├── final_performance.json
│   ├── model_monitoring.json
│   ├── performance_report.json
│   └── retraining_report.json
│
└── reports/
    ├── final_integration_report.json
    └── person_1_2_summary.json


# 17. Running Module 7

Open PowerShell and navigate to the Module 7 directory:

cd "E:\Final year Project\DigitalTwin-AI\Module 7 - Explainable AI & Performance Evaluation"

Install the required dependencies:

pip install -r requirements.txt

Run the complete integration test:

py -m integration.integration_test

A successful execution ends with:

✓ MODULE 7 END-TO-END INTEGRATION TEST PASSED


# 18. Requirements

The module uses libraries including:

- NumPy
- Pandas
- Scikit-learn
- Joblib

Install all dependencies using:

pip install -r requirements.txt


# 19. Design Principles

Module 7 follows these principles:

## Validation First

Inputs and outputs are validated before being used in the pipeline.

## No Fabricated Evaluation

Performance metrics are not presented as measured accuracy when actual evaluation data is unavailable.

## Safe Retraining

Candidate models are evaluated before promotion.

## Explainability

SHAP and feature-importance utilities provide both local and global model interpretation.

## Reproducibility

Randomized components use controlled random seeds where applicable.

## Modular Architecture

Evaluation, explainability, anomaly detection, retraining, and integration are separated into independent packages.

## JSON-Based Integration

Module outputs are exchanged through structured JSON artifacts, making the pipeline easy to integrate with other modules and future frontend/dashboard components.


# 20. Final Pipeline

The complete Digital Twin AI pipeline is:

Module 1
Data Acquisition
        ↓
Module 2
Digital Twin
        ↓
Module 3
AI Forecasting
        ↓
Module 4
Multi-Agent Intelligence
        ↓
Module 5
Generative Scenario Simulation
        ↓
Module 6
Optimization Engine
        ↓
Module 7
Explainable AI & Performance Evaluation
        ↓
Final Evaluation Reports

Module 7 acts as the final validation and intelligence-analysis layer of the Digital Twin system.