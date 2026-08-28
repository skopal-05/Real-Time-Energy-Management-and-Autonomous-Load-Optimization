"""Person 2 tests: SHAP, feature importance, explanations, and anomalies."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from anomaly_detection import AnomalyDetector, AnomalyValidator, IsolationForestModel
from explainability import ExplanationGenerator, FeatureImportance, ShapAnalyzer


class ExplainabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(2)
        self.names = ["load_kw", "temperature_c", "vibration_mm_s"]
        self.X = pd.DataFrame(rng.normal(size=(60, 3)), columns=self.names)
        self.y = 5 * self.X["load_kw"] + self.X["temperature_c"]
        self.model = RandomForestRegressor(n_estimators=30, random_state=2).fit(self.X, self.y)

    def test_native_feature_importance_is_ranked_and_normalized(self) -> None:
        output = FeatureImportance().native(self.model, self.names)
        self.assertEqual(output["features"][0]["feature"], "load_kw")
        self.assertAlmostEqual(sum(item["importance"] for item in output["features"]), 1, places=6)

    def test_permutation_importance_identifies_dominant_feature(self) -> None:
        output = FeatureImportance().permutation(
            self.model, self.X.to_numpy(), self.y.to_numpy(), self.names, repeats=3
        )
        self.assertEqual(output["features"][0]["feature"], "load_kw")

    def test_exact_shap_values_satisfy_additivity(self) -> None:
        output = ShapAnalyzer().explain(
            self.model,
            self.X.iloc[:30].to_numpy(),
            self.X.iloc[30:32].to_numpy(),
            self.names,
        )
        self.assertEqual(output["method"], "exact_single_reference_shapley")
        self.assertTrue(
            all(item["additivity_error"] <= 1e-6 for item in output["explanations"])
        )

    def test_explanation_generator_produces_readable_output(self) -> None:
        shap_output = ShapAnalyzer().explain(
            self.model, self.X.iloc[:30].to_numpy(), self.X.iloc[30:31].to_numpy(), self.names
        )
        importance = FeatureImportance().native(self.model, self.names)
        output = ExplanationGenerator().generate(
            "demo_rf", "power_kw", shap_output, importance
        )
        self.assertIn("load_kw", output["local_explanations"][0]["summary"])
        self.assertTrue(output["local_explanations"][0]["additivity_verified"])

    def test_shap_rejects_feature_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            ShapAnalyzer().explain(self.model, [[1, 2, 3]], [[1, 2]], self.names)


class AnomalyDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(8)
        normal = rng.normal(loc=[60, 70, 2], scale=[3, 2, 0.2], size=(100, 3))
        self.features = ["power_kw", "temperature_c", "vibration_mm_s"]
        self.training = [dict(zip(self.features, row)) for row in normal]

    def test_isolation_forest_detects_extreme_operating_state(self) -> None:
        detector = AnomalyDetector(
            IsolationForestModel(contamination=0.05, random_state=42)
        ).fit(self.training, self.features)
        records = self.training[:10] + [
            {"power_kw": 180, "temperature_c": 150, "vibration_mm_s": 15}
        ]
        output = detector.detect(records)
        self.assertTrue(output["records"][-1]["is_anomaly"])
        self.assertFalse(AnomalyValidator().validate(output))

    def test_detector_rejects_missing_feature(self) -> None:
        detector = AnomalyDetector().fit(self.training, self.features)
        with self.assertRaises(ValueError):
            detector.detect([{"power_kw": 50}])

    def test_validator_rejects_bad_count_and_score(self) -> None:
        errors = AnomalyValidator().validate(
            {
                "feature_names": ["x"],
                "record_count": 2,
                "anomaly_count": 0,
                "records": [
                    {"label": "normal", "is_anomaly": False, "anomaly_score": 2.0}
                ],
            }
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()

