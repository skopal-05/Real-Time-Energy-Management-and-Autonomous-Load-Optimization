import subprocess
import sys
from pathlib import Path

# ==========================================================
# Project Paths
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PIPELINE = [

    ("Generate Synthetic Data",
     PROJECT_DIR / "data_collection" / "run_all.py"),

    ("Schema Validation",
     PROJECT_DIR / "validation" / "validate_schema.py"),

    ("Missing Value Validation",
     PROJECT_DIR / "validation" / "validate_missing.py"),

    ("Range Validation",
     PROJECT_DIR / "validation" / "validate_ranges.py"),

    ("Data Cleaning",
     PROJECT_DIR / "preprocessing" / "clean_data.py"),

    ("Missing Value Handling",
     PROJECT_DIR / "preprocessing" / "missing_values.py"),

    ("Feature Engineering",
     PROJECT_DIR / "preprocessing" / "feature_engineering.py"),

    ("Normalization",
     PROJECT_DIR / "preprocessing" / "normalize.py"),

]

print("=" * 70)
print("DIGITAL TWIN DATA ACQUISITION PIPELINE")
print("=" * 70)

for step_name, script in PIPELINE:

    print(f"\nRunning : {step_name}")

    result = subprocess.run(
        [sys.executable, str(script)]
    )

    if result.returncode == 0:
        print(f"[SUCCESS] {step_name} Completed")
    else:
        print(f"[FAILED] {step_name}")
        print("Pipeline Stopped.")
        sys.exit(1)

print("\n" + "=" * 70)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nOutputs Generated In:")

print(f"\nRaw Data        : {PROJECT_DIR / 'outputs'}")
print(f"Cleaned Data    : {PROJECT_DIR / 'outputs' / 'cleaned_data'}")
print(f"Normalized Data : {PROJECT_DIR / 'outputs' / 'normalized_data'}")
print(f"Logs            : {PROJECT_DIR / 'outputs' / 'logs'}")