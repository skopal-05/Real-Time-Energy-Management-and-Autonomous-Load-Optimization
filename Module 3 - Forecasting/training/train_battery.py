"""
Training script for Battery Forecasting Model.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from common.config import MODULE_CONFIG
from common.metrics import ForecastMetrics
from common.model_manager import ModelManager


# =====================================================
# Project Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "Module 1 - Data Acquisition"
    / "outputs"
    / "cleaned_data"
)

DATA_FILE = (
    DATASET_DIR
    / "battery_storage.csv"
)


# =====================================================
# Configuration
# =====================================================

CONFIG = MODULE_CONFIG["battery"]

FEATURES = CONFIG["features"]

TARGET = CONFIG["target"]

MODEL_NAME = CONFIG["model"]

ENCODERS = CONFIG["encoders"]


# =====================================================
# Main
# =====================================================

def main() -> None:

    print("=" * 60)
    print("Battery Forecast Model Training")
    print("=" * 60)

    # -------------------------------------------------
    # Load Dataset
    # -------------------------------------------------

    print("\nLoading battery dataset...")

    dataset = pd.read_csv(
        DATA_FILE,
    )

    print(
        f"Total Samples : {len(dataset)}"
    )

    # -------------------------------------------------
    # Prepare Features
    # -------------------------------------------------

    X = dataset[
        FEATURES
    ].copy()

    y = dataset[
        TARGET
    ].copy()

    # -------------------------------------------------
    # Initialize Model Manager
    # -------------------------------------------------

    manager = ModelManager()

    # -------------------------------------------------
    # Encode Categorical Features
    # -------------------------------------------------

    for column, encoder_name in ENCODERS.items():

        encoder = LabelEncoder()

        X[column] = encoder.fit_transform(
            X[column]
        )

        manager.save_encoder(
            encoder_name,
            encoder,
        )

        print(
            f"Encoder Saved : {encoder_name}"
        )

    # -------------------------------------------------
    # Train-Test Split
    # -------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,

        y,

        test_size=0.20,

        random_state=42,

        shuffle=True,

    )

    print(
        f"\nTraining Samples : {len(X_train)}"
    )

    print(
        f"Testing Samples  : {len(X_test)}"
    )

    # -------------------------------------------------
    # Train Model
    # -------------------------------------------------

    print("\nTraining Random Forest model...")

    manager.train(
        model_name=MODEL_NAME,
        X_train=X_train,
        y_train=y_train,
    )

    print("Training completed successfully.")

    # -------------------------------------------------
    # Evaluate Model
    # -------------------------------------------------

    print("\nEvaluating model...")

    predictions = manager.predict(
        MODEL_NAME,
        X_test,
    )

    metrics = ForecastMetrics(
        y_true=y_test,
        y_pred=predictions,
    )

    metrics.print_summary()

    # -------------------------------------------------
    # Save Model
    # -------------------------------------------------

    model_path = manager.save_model(
        MODEL_NAME,
    )

    print(
        f"\nModel saved to:\n{model_path}"
    )

    # -------------------------------------------------
    # Feature Importance
    # -------------------------------------------------

    print("\nFeature Importance")
    print("-" * 40)

    importance = manager.feature_importance(
        MODEL_NAME,
        FEATURES,
    )

    for feature, score in sorted(
        importance.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{feature:<35}{score:.4f}"
        )

    # -------------------------------------------------
    # Training Summary
    # -------------------------------------------------

    print("\nTraining Summary")
    print("-" * 40)

    print(f"Model Name       : {MODEL_NAME}")
    print(f"Target Column    : {TARGET}")
    print(f"Feature Count    : {len(FEATURES)}")
    print(f"Training Samples : {len(X_train)}")
    print(f"Testing Samples  : {len(X_test)}")

    if ENCODERS:

        print(
            "Encoders         : "
            + ", ".join(ENCODERS.values())
        )

    else:

        print("Encoders         : None")

    print(f"Saved Model      : {model_path.name}")

    print("\nBattery model training completed successfully.")


# =====================================================
# Entry Point
# =====================================================

if __name__ == "__main__":

    main()