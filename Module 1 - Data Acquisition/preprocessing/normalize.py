from pathlib import Path
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ==========================================================
# Project Paths
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

CLEANED_DATA_DIR = PROJECT_DIR / "outputs" / "cleaned_data"
NORMALIZED_DATA_DIR = PROJECT_DIR / "outputs" / "normalized_data"
LOG_DIR = PROJECT_DIR / "outputs" / "logs"

NORMALIZED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "normalization_report.log"

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
    log.write("NORMALIZATION REPORT\n")
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

            # ------------------------------------------
            # Numeric Columns
            # ------------------------------------------

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

            # Columns that should NOT be normalized
            exclude_cols = [
                "hour",
                "day",
                "month",
                "day_of_week",
                "is_weekend"
            ]

            numeric_cols = [
                col for col in numeric_cols
                if col not in exclude_cols
            ]

            if numeric_cols:

                scaler = MinMaxScaler()

                df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

            # ------------------------------------------
            # Save
            # ------------------------------------------

            output_path = NORMALIZED_DATA_DIR / dataset
            df.to_csv(output_path, index=False)

            log.write(f"Normalized Columns : {len(numeric_cols)}\n")
            log.write("STATUS             : PASSED\n\n")

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
print("NORMALIZATION COMPLETED")
print("=" * 60)
print(f"Processed : {processed}")
print(f"Failed    : {failed}")
print(f"\nNormalized datasets saved in:\n{NORMALIZED_DATA_DIR}")
print(f"\nReport saved at:\n{LOG_FILE}")