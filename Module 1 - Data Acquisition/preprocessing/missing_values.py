from pathlib import Path
import pandas as pd

# ==========================================================
# Project Paths
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

CLEANED_DATA_DIR = PROJECT_DIR / "outputs" / "cleaned_data"
LOG_DIR = PROJECT_DIR / "outputs" / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "missing_values_report.log"

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
    log.write("MISSING VALUE HANDLING REPORT\n")
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

            before_missing = df.isna().sum().sum()

            # Numeric Columns
            numeric_cols = df.select_dtypes(include=["number"]).columns

            df[numeric_cols] = df[numeric_cols].interpolate(
                method="linear",
                limit_direction="both"
            )

            df[numeric_cols] = df[numeric_cols].ffill().bfill()

            # Categorical Columns
            categorical_cols = df.select_dtypes(include=["object"]).columns

            for col in categorical_cols:
                if df[col].isnull().any():
                    mode = df[col].mode(dropna=True)
                    if not mode.empty:
                        df[col] = df[col].fillna(mode.iloc[0])

            after_missing = df.isna().sum().sum()

            df.to_csv(file_path, index=False)

            log.write(f"Missing Before : {before_missing}\n")
            log.write(f"Missing After  : {after_missing}\n")
            log.write("STATUS         : PASSED\n\n")

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
print("MISSING VALUE HANDLING COMPLETED")
print("=" * 60)
print(f"Processed : {processed}")
print(f"Failed    : {failed}")
print(f"\nReport saved at:\n{LOG_FILE}")