import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

scripts = [
    "clean_data.py",
    "missing_values.py",
    "feature_engineering.py",
    "normalize.py"
]

print("=" * 60)
print("RUNNING PREPROCESSING PIPELINE")
print("=" * 60)

for script in scripts:
    print(f"\nRunning {script}...\n")

    result = subprocess.run(
        [sys.executable, str(CURRENT_DIR / script)]
    )

    if result.returncode != 0:
        print(f"\nERROR: {script} failed.")
        break

print("\nPreprocessing Pipeline Finished.")