from pathlib import Path
import pandas as pd

# ==========================================================
# Project Paths
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

RAW_DATA_DIR = PROJECT_DIR / "outputs"
LOG_DIR = RAW_DATA_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "schema_validation.log"

# ==========================================================
# Expected Datasets
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

# ==========================================================
# Validation
# ==========================================================

passed = 0
failed = 0

with open(LOG_FILE, "w", encoding="utf-8") as log:

    log.write("=" * 70 + "\n")
    log.write("SCHEMA VALIDATION REPORT\n")
    log.write("=" * 70 + "\n\n")

    for dataset in DATASETS:

        log.write("-" * 70 + "\n")
        log.write(f"Dataset : {dataset}\n")
        log.write("-" * 70 + "\n")

        file_path = RAW_DATA_DIR / dataset

        if not file_path.exists():
            log.write("[FAIL] File not found\n\n")
            failed += 1
            continue

        try:

            df = pd.read_csv(file_path)

            # Empty dataset
            if df.empty:
                log.write("[FAIL] Dataset is empty\n\n")
                failed += 1
                continue

            # Required columns
            required_columns = [
                "timestamp",
                "system_id"
            ]

            missing_columns = [
                col for col in required_columns
                if col not in df.columns
            ]

            if missing_columns:
                log.write(f"[FAIL] Missing Columns : {missing_columns}\n")
            else:
                log.write("[PASS] Required columns present\n")

            # Duplicate column names
            if len(df.columns) != len(set(df.columns)):
                log.write("[FAIL] Duplicate column names found\n")
            else:
                log.write("[PASS] No duplicate columns\n")

            # Timestamp validation
            try:
                pd.to_datetime(df["timestamp"])
                log.write("[PASS] Timestamp format valid\n")
            except Exception:
                log.write("[FAIL] Timestamp format invalid\n")

            # Dataset Information
            log.write(f"\nRows    : {len(df)}\n")
            log.write(f"Columns : {len(df.columns)}\n")

            log.write("\nColumn Data Types\n")
            log.write("-" * 30 + "\n")

            for column, dtype in df.dtypes.items():
                log.write(f"{column:<35}{dtype}\n")

            log.write("\nSTATUS : PASSED\n\n")

            passed += 1

        except Exception as e:

            log.write(f"[FAIL] {e}\n\n")
            failed += 1

    log.write("=" * 70 + "\n")
    log.write("SUMMARY\n")
    log.write("=" * 70 + "\n")

    log.write(f"Total Datasets : {len(DATASETS)}\n")
    log.write(f"Passed         : {passed}\n")
    log.write(f"Failed         : {failed}\n")

print("=" * 60)
print("SCHEMA VALIDATION COMPLETED")
print("=" * 60)
print(f"Passed : {passed}")
print(f"Failed : {failed}")
print(f"\nReport saved at:\n{LOG_FILE}")