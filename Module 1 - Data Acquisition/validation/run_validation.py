import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

scripts = [
    "validate_schema.py",
    "validate_missing.py",
    "validate_ranges.py"
]

print("=" * 60)
print("RUNNING VALIDATION PIPELINE")
print("=" * 60)

for script in scripts:
    print(f"\nRunning {script}...\n")

    result = subprocess.run(
        [sys.executable, str(CURRENT_DIR / script)]
    )

    if result.returncode != 0:
        print(f"\nERROR: {script} failed.")
        break

print("\nValidation Pipeline Finished.")