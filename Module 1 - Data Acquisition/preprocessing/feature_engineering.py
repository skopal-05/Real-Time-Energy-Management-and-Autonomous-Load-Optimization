from pathlib import Path
import pandas as pd
import numpy as np

# ==========================================================
# Project Paths
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

CLEANED_DATA_DIR = PROJECT_DIR / "outputs" / "cleaned_data"
LOG_DIR = PROJECT_DIR / "outputs" / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "feature_engineering_report.log"

# ==========================================================
# Datasets
# ==========================================================

DATASETS = [
    "compressor.csv",
    "hvac.csv",
    "battery_storage.csv",
    "boiler.csv",
    "grid.csv",
    "production_line_a_production.csv",
    "production_line_b_production.csv",
    "solar_plant.csv",
    "weather.csv",
]

processed = 0
failed = 0

with open(LOG_FILE, "w", encoding="utf-8") as log:

    log.write("=" * 70 + "\n")
    log.write("FEATURE ENGINEERING REPORT\n")
    log.write("=" * 70 + "\n\n")

    for dataset in DATASETS:

        log.write("-" * 70 + "\n")
        log.write(f"Dataset : {dataset}\n")
        log.write("-" * 70 + "\n")

        file_path = CLEANED_DATA_DIR / dataset

        if not file_path.exists():
            log.write("[FAIL] File not found\n\n")
            failed += 1
            continue

        try:

            df = pd.read_csv(file_path)

            if "timestamp" not in df.columns:
                log.write("[FAIL] Timestamp column not found\n\n")
                failed += 1
                continue

            # ------------------------------------------
            # Timestamp Conversion
            # ------------------------------------------

            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # ------------------------------------------
            # Time Features
            # ------------------------------------------

            df["hour"] = df["timestamp"].dt.hour
            df["day"] = df["timestamp"].dt.day
            df["month"] = df["timestamp"].dt.month
            df["day_of_week"] = df["timestamp"].dt.dayofweek
            df["is_weekend"] = (
                df["day_of_week"] >= 5
            ).astype(int)

            # ------------------------------------------
            # Cyclic Encoding
            # ------------------------------------------

            df["hour_sin"] = np.sin(
                2 * np.pi * df["hour"] / 24
            )

            df["hour_cos"] = np.cos(
                2 * np.pi * df["hour"] / 24
            )

            # ------------------------------------------
            # Lag & Rolling Features
            # ------------------------------------------

            numeric_cols = df.select_dtypes(
                include=["number"]
            ).columns.tolist()

            ignore_cols = [
                "hour",
                "day",
                "month",
                "day_of_week",
                "is_weekend",
                "hour_sin",
                "hour_cos"
            ]

            numeric_cols = [
                c for c in numeric_cols
                if c not in ignore_cols
            ]

            for col in numeric_cols:

                df[f"{col}_lag1"] = df[col].shift(1)

                df[f"{col}_lag3"] = df[col].shift(3)

                df[f"{col}_rolling_mean3"] = (
                    df[col]
                    .rolling(window=3)
                    .mean()
                )

                df[f"{col}_rolling_std3"] = (
                    df[col]
                    .rolling(window=3)
                    .std()
                )

            # ------------------------------------------
            # Fill NaNs created by lag/rolling
            # ------------------------------------------

            df = df.bfill().ffill()

            # ------------------------------------------
            # Save
            # ------------------------------------------

            df.to_csv(file_path, index=False)

            log.write(f"Original Columns : {len(df.columns)}\n")
            log.write("Feature Engineering : SUCCESS\n\n")

            processed += 1

        except Exception as e:

            log.write(f"[FAIL] {e}\n\n")
            failed += 1

    log.write("=" * 70 + "\n")
    log.write("SUMMARY\n")
    log.write("=" * 70 + "\n")
    log.write(f"Processed : {processed}\n")
    log.write(f"Failed    : {failed}\n")

print("=" * 60)
print("FEATURE ENGINEERING COMPLETED")
print("=" * 60)
print(f"Processed : {processed}")
print(f"Failed    : {failed}")
print(f"\nReport saved at:\n{LOG_FILE}")