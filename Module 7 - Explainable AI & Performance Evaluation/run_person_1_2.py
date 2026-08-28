"""Generate all standalone Week 7 outputs assigned to Person 1 and Person 2.

This runner evaluates existing artifacts but is not the Person 3 final pipeline
controller. It never overwrites Module 3 models.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from anomaly_detection import AnomalyDetector, IsolationForestModel
from evaluation import PerformanceEvaluator
from explainability import ExplanationGenerator, FeatureImportance, ShapAnalyzer
from retraining import ModelMonitor, RetrainingPipeline, RetrainingValidator


MODULE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_ROOT.parent
DATA_ROOT = PROJECT_ROOT / "Module 1 - Data Acquisition" / "outputs" / "cleaned_data"
MODEL_ROOT = PROJECT_ROOT / "Module 3 - Forecasting" / "models"
OUTPUT_ROOT = MODULE_ROOT / "outputs"

MODEL_CONFIG = {
    "production": {
        "model": "production_rf",
        "files": ["production_line_a_production.csv", "production_line_b_production.csv"],
        "target": "units_per_hour",
        "features": ["machine_load_kw", "motor_temperature_c", "vibration_mm_s", "status"],
        "encoders": {"status": "production_encoder"},
    },
    "boiler": {
        "model": "boiler_rf",
        "files": ["boiler.csv"],
        "target": "fuel_flow_m3_hr",
        "features": [
            "steam_pressure_bar",
            "feedwater_temperature_c",
            "flue_gas_temperature_c",
            "efficiency_percent",
        ],
        "encoders": {},
    },
    "compressor": {
        "model": "compressor_rf",
        "files": ["compressor.csv"],
        "target": "power_kw",
        "features": [
            "air_pressure_bar",
            "motor_temperature_c",
            "vibration_mm_s",
            "efficiency_percent",
            "status",
        ],
        "encoders": {"status": "compressor_encoder"},
    },
    "hvac": {
        "model": "hvac_rf",
        "files": ["hvac.csv"],
        "target": "power_kw",
        "features": [
            "temperature_c",
            "airflow_m3_min",
            "humidity_percent",
            "setpoint_temperature_c",
            "efficiency_percent",
            "status",
        ],
        "encoders": {"status": "hvac_encoder"},
    },
    "battery": {
        "model": "battery_rf",
        "files": ["battery_storage.csv"],
        "target": "battery_power_kw",
        "features": ["voltage_v", "current_a", "temperature_c", "mode", "state_of_charge_percent"],
        "encoders": {"mode": "battery_encoder"},
    },
    "grid": {
        "model": "grid_rf",
        "files": ["grid.csv"],
        "target": "grid_import_kw",
        "features": ["grid_export_kw", "frequency_hz", "voltage_v", "power_factor", "tariff_inr_kwh"],
        "encoders": {},
    },
    "solar": {
        "model": "solar_rf",
        "files": ["solar_plant.csv"],
        "target": "inverter_power_kw",
        "features": ["irradiance_w_m2", "panel_temperature_c", "inverter_status"],
        "encoders": {"inverter_status": "solar_encoder"},
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def load_model_data(
    config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    frames = [pd.read_csv(DATA_ROOT / filename) for filename in config["files"]]
    data = pd.concat(frames, ignore_index=True)
    X = data[config["features"]].copy()
    compatibility_warnings = []
    for column, encoder_name in config["encoders"].items():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            encoder = joblib.load(MODEL_ROOT / f"{encoder_name}.joblib")
        compatibility_warnings.extend(
            f"{encoder_name}: {item.message}"
            for item in caught
            if "version" in str(item.message)
        )
        X[column] = encoder.transform(X[column].astype(str))
    return X, data[config["target"]].astype(float), compatibility_warnings


def main() -> None:
    evaluator = PerformanceEvaluator()
    monitor = ModelMonitor()
    retraining = RetrainingPipeline()
    importance_analyzer = FeatureImportance()
    shap_analyzer = ShapAnalyzer()
    explanation_generator = ExplanationGenerator()

    forecast_evaluations = {}
    monitoring_models = {}
    retraining_models = {}
    feature_importance_models = {}
    explanation_models = {}
    compatibility_warnings: list[str] = []

    for subsystem, config in MODEL_CONFIG.items():
        X, y, data_warnings = load_model_data(config)
        compatibility_warnings.extend(data_warnings)
        X_train, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = joblib.load(MODEL_ROOT / f"{config['model']}.joblib")
            predictions = model.predict(X_test)
        compatibility_warnings.extend(
            f"{config['model']}: {item.message}" for item in caught if "version" in str(item.message)
        )

        evaluation = evaluator.evaluate_forecast(
            config["model"], y_test, predictions, target=config["target"]
        )
        forecast_evaluations[subsystem] = evaluation
        current_metrics = evaluation["metrics"]

        performance_monitor = monitor.monitor_performance(
            config["model"], current_metrics, current_metrics
        )
        split_index = max(10, int(len(X) * 0.7))
        drift = monitor.feature_drift(
            X.iloc[:split_index].to_numpy(),
            X.iloc[split_index:].to_numpy(),
            config["features"],
        )
        performance_monitor["reference_source"] = "initial_week7_baseline"
        performance_monitor["feature_drift"] = drift
        if drift["drift_detected"]:
            performance_monitor["status"] = "degraded"
            performance_monitor["retraining_required"] = True
            performance_monitor["reasons"].append(
                "feature drift detected: " + ", ".join(drift["drifted_features"])
            )
        RetrainingValidator().require_valid(
            RetrainingValidator().validate_monitoring(performance_monitor),
            f"{config['model']} monitoring report",
        )
        monitoring_models[subsystem] = performance_monitor

        retraining_report, _ = retraining.run(
            model,
            X.to_numpy(),
            y.to_numpy(),
            model_name=config["model"],
            trigger=performance_monitor["retraining_required"],
        )
        retraining_models[subsystem] = retraining_report

        importance_output = importance_analyzer.native(model, config["features"])
        feature_importance_models[subsystem] = {
            "model": config["model"],
            "target": config["target"],
            **importance_output,
        }
        shap_output = shap_analyzer.explain(
            model,
            X_train.iloc[: min(40, len(X_train))].to_numpy(),
            X_test.iloc[: min(2, len(X_test))].to_numpy(),
            config["features"],
        )
        explanation_models[subsystem] = explanation_generator.generate(
            config["model"], config["target"], shap_output, importance_output
        )

    agent_output = read_json(
        PROJECT_ROOT
        / "Module 4 - Multi-Agent Intelligence"
        / "outputs"
        / "recommendations"
        / "recommendations.json"
    )
    scenario_output = read_json(
        PROJECT_ROOT
        / "Module 5 - Scenario Simulation"
        / "outputs"
        / "comparisons"
        / "scenario_comparison.json"
    )
    optimization_report = read_json(
        PROJECT_ROOT
        / "Module 6 - Optimization Engine"
        / "outputs"
        / "reports"
        / "optimization_report.json"
    )
    performance_report = evaluator.build_report(
        forecast_evaluations, agent_output, scenario_output, optimization_report
    )
    performance_report["model_compatibility_warnings"] = sorted(set(compatibility_warnings))

    monitoring_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_count": len(monitoring_models),
        "retraining_required_count": sum(
            item["retraining_required"] for item in monitoring_models.values()
        ),
        "models": monitoring_models,
    }
    retraining_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety_policy": "candidate models are never promoted without an explicit promotion_path",
        "models": retraining_models,
    }
    feature_importance_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": feature_importance_models,
    }
    explanation_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": explanation_models,
    }

    production_data = pd.concat(
        [
            pd.read_csv(DATA_ROOT / "production_line_a_production.csv"),
            pd.read_csv(DATA_ROOT / "production_line_b_production.csv"),
        ],
        ignore_index=True,
    )
    anomaly_features = ["machine_load_kw", "motor_temperature_c", "vibration_mm_s"]
    records = production_data[anomaly_features].to_dict(orient="records")
    training_records = records[: int(len(records) * 0.75)]
    evaluation_records = records[int(len(records) * 0.75) :]
    anomaly_report = AnomalyDetector(
        IsolationForestModel(contamination=0.05, random_state=42)
    ).fit(training_records, anomaly_features).detect(evaluation_records)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Week 7 Person 1 and Person 2",
        "forecast_model_count": len(forecast_evaluations),
        "mean_forecast_wape_percent": performance_report["forecasting_summary"][
            "mean_wape_percent"
        ],
        "mean_forecast_smape_percent": performance_report["forecasting_summary"][
            "mean_smape_percent"
        ],
        "mean_forecast_r2": performance_report["forecasting_summary"]["mean_r2"],
        "models_requiring_retraining": monitoring_report["retraining_required_count"],
        "explained_model_count": len(explanation_models),
        "anomaly_count": anomaly_report["anomaly_count"],
        "optimization_improvements": performance_report["optimization_benchmark"]["summary"],
        "person_3_integration_included": False,
    }

    write_json(OUTPUT_ROOT / "performance" / "performance_report.json", performance_report)
    write_json(OUTPUT_ROOT / "performance" / "model_monitoring.json", monitoring_report)
    write_json(OUTPUT_ROOT / "performance" / "retraining_report.json", retraining_report)
    write_json(OUTPUT_ROOT / "explanations" / "feature_importance.json", feature_importance_report)
    write_json(OUTPUT_ROOT / "explanations" / "shap_explanations.json", explanation_report)
    write_json(OUTPUT_ROOT / "anomalies" / "anomaly_report.json", anomaly_report)
    write_json(OUTPUT_ROOT / "reports" / "person_1_2_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
