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

LOG_FILE = LOG_DIR / "missing_validation.log"

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
    log.write("MISSING VALUES VALIDATION REPORT\n")
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

            total_rows = len(df)
            total_cells = df.size

            # Missing values
            missing_per_column = df.isnull().sum()
            total_missing = missing_per_column.sum()

            # Duplicate rows
            duplicate_rows = df.duplicated().sum()

            log.write(f"Rows             : {total_rows}\n")
            log.write(f"Columns          : {len(df.columns)}\n")
            log.write(f"Total Cells      : {total_cells}\n")
            log.write(f"Missing Values   : {total_missing}\n")
            log.write(f"Duplicate Rows   : {duplicate_rows}\n\n")

            log.write("Missing Values by Column\n")
            log.write("-" * 35 + "\n")

            for column in df.columns:
                missing = missing_per_column[column]
                percent = (missing / total_rows) * 100 if total_rows else 0

                log.write(
                    f"{column:<35}"
                    f"{missing:>6} ({percent:.2f}%)\n"
                )

            if total_missing == 0 and duplicate_rows == 0:
                log.write("\nSTATUS : PASSED\n\n")
                passed += 1
            else:
                log.write("\nSTATUS : ATTENTION REQUIRED\n\n")
                failed += 1

        except Exception as e:
            log.write(f"[FAIL] {e}\n\n")
            failed += 1

    log.write("=" * 70 + "\n")
    log.write("SUMMARY\n")
    log.write("=" * 70 + "\n")

    log.write(f"Total Datasets : {len(DATASETS)}\n")
    log.write(f"Passed         : {passed}\n")
    log.write(f"Attention      : {failed}\n")

print("=" * 60)
print("MISSING VALUE VALIDATION COMPLETED")
print("=" * 60)
print(f"Passed    : {passed}")
print(f"Attention : {failed}")
print(f"\nReport saved at:\n{LOG_FILE}")