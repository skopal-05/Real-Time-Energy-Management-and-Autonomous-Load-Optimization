"""Convert SHAP and global importance outputs into structured explanations."""

from __future__ import annotations

from typing import Any, Mapping


class ExplanationGenerator:
    def generate(
        self,
        model_name: str,
        target: str,
        shap_output: Mapping[str, Any],
        importance_output: Mapping[str, Any],
        *,
        top_n: int = 3,
    ) -> dict[str, Any]:
        explanations = []
        for sample in shap_output.get("explanations", []):
            leading = list(sample.get("features", []))[:top_n]
            phrases = [
                f"{item['feature']} {item['effect']} the prediction by {abs(float(item['shap_value'])):.3f}"
                for item in leading
            ]
            explanations.append(
                {
                    "sample_index": sample["sample_index"],
                    "prediction": sample["prediction"],
                    "base_value": sample["base_value"],
                    "top_factors": leading,
                    "summary": "; ".join(phrases) if phrases else "No material feature effect.",
                    "additivity_verified": float(sample.get("additivity_error", 1.0)) <= 1e-6,
                }
            )
        global_features = list(importance_output.get("features", []))[:top_n]
        result = {
            "model": model_name,
            "target": target,
            "shap_method": shap_output.get("method"),
            "global_feature_importance": global_features,
            "local_explanations": explanations,
        }
        self.require_valid(result)
        return result

    @staticmethod
    def validate(output: Mapping[str, Any]) -> list[str]:
        errors = []
        for field in ("model", "target", "shap_method", "global_feature_importance", "local_explanations"):
            if field not in output:
                errors.append(f"missing explanation field: {field}")
        if output.get("shap_method") != "exact_single_reference_shapley":
            errors.append("unsupported or missing SHAP method")
        local = output.get("local_explanations", [])
        if not local:
            errors.append("at least one local explanation is required")
        elif not all(item.get("additivity_verified") for item in local):
            errors.append("SHAP additivity verification failed")
        return errors

    def require_valid(self, output: Mapping[str, Any]) -> None:
        errors = self.validate(output)
        if errors:
            raise ValueError("invalid explanation output: " + "; ".join(errors))

