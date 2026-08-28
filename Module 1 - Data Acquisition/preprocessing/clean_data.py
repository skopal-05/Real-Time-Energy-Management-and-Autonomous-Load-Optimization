from pathlib import Path
import pandas as pd

# ==========================================================
# Project Paths
# ==========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

RAW_DATA_DIR = PROJECT_DIR / "outputs"
CLEANED_DATA_DIR = RAW_DATA_DIR / "cleaned_data"
LOG_DIR = RAW_DATA_DIR / "logs"

CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "cleaning_report.log"

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

# ==========================================================
# Cleaning
# ==========================================================

processed = 0
failed = 0

with open(LOG_FILE, "w", encoding="utf-8") as log:

    log.write("=" * 70 + "\n")
    log.write("DATA CLEANING REPORT\n")
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

            original_rows = len(df)

            # ------------------------------------
            # Clean column names
            # ------------------------------------
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(" ", "_")
            )

            # ------------------------------------
            # Timestamp conversion
            # ------------------------------------
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(
                    df["timestamp"],
                    errors="coerce"
                )

            # ------------------------------------
            # Remove duplicate rows
            # ------------------------------------
            duplicates = df.duplicated().sum()
            df = df.drop_duplicates()

            # ------------------------------------
            # Remove completely empty rows
            # ------------------------------------
            empty_rows = df.isna().all(axis=1).sum()
            df = df.dropna(how="all")

            # ------------------------------------
            # Sort by timestamp
            # ------------------------------------
            if "timestamp" in df.columns:
                df = df.sort_values("timestamp")

            # ------------------------------------
            # Reset index
            # ------------------------------------
            df.reset_index(drop=True, inplace=True)

            # ------------------------------------
            # Save cleaned dataset
            # ------------------------------------
            output_path = CLEANED_DATA_DIR / dataset
            df.to_csv(output_path, index=False)

            log.write(f"Original Rows     : {original_rows}\n")
            log.write(f"Duplicate Removed : {duplicates}\n")
            log.write(f"Empty Rows Removed: {empty_rows}\n")
            log.write(f"Final Rows        : {len(df)}\n")
            log.write("STATUS            : PASSED\n\n")

            processed += 1

        except Exception as e:

            log.write(f"[FAIL] {e}\n\n")
            failed += 1

    log.write("=" * 70 + "\n")
    log.write("SUMMARY\n")
    log.write("=" * 70 + "\n")
    log.write(f"Datasets Processed : {processed}\n")
    log.write(f"Failed             : {failed}\n")

print("=" * 60)
print("DATA CLEANING COMPLETED")
print("=" * 60)
print(f"Processed : {processed}")
print(f"Failed    : {failed}")
print(f"\nCleaned files saved in:\n{CLEANED_DATA_DIR}")
print(f"\nCleaning report saved in:\n{LOG_FILE}")