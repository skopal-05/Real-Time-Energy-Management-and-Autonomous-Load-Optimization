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

LOG_FILE = LOG_DIR / "range_validation.log"

# ==========================================================
# Range Rules
# ==========================================================

RANGE_RULES = {

    "compressor.csv": {
        "air_flow_m3_min": (20, 150),
        "discharge_pressure_bar": (0, 20),
        "power_consumption_kw": (0, 500),
        "motor_temperature_c": (0, 120),
        "vibration_mm_s": (0, 20),
    },

    "hvac.csv": {
        "power_kw": (0, 100),
        "temperature_c": (15, 35),
        "airflow_m3_min": (0, 3000),
        "humidity_percent": (0, 100),
        "setpoint_temperature_c": (18, 30),
        "efficiency_percent": (0, 100),
    },

    "battery_storage.csv": {
        "state_of_charge_percent": (0, 100),
        "battery_power_kw": (-500, 500),
        "voltage_v": (0, 1000),
        "current_a": (-1000, 1000),
        "temperature_c": (-20, 80),
    },

    "boiler.csv": {
        "steam_pressure_bar": (0, 100),
        "steam_flow_kg_hr": (0, 10000),
        "fuel_flow_m3_hr": (0, 5000),
        "feedwater_temperature_c": (0, 150),
        "flue_gas_temperature_c": (0, 500),
        "efficiency_percent": (0, 100),
    },

    "grid.csv": {
        "grid_import_kw": (0, 10000),
        "grid_export_kw": (0, 10000),
        "frequency_hz": (49, 51),
        "voltage_v": (200, 500),
        "power_factor": (0, 1),
        "tariff_inr_kwh": (0, 100),
    },

    "production_line_a_production.csv": {
        "units_per_hour": (0, 1000),
        "machine_load_kw": (0, 1000),
        "motor_temperature_c": (0, 120),
        "vibration_mm_s": (0, 20),
    },

    "production_line_b_production.csv": {
        "units_per_hour": (0, 1000),
        "machine_load_kw": (0, 1000),
        "motor_temperature_c": (0, 120),
        "vibration_mm_s": (0, 20),
    },

    "solar_plant.csv": {
        "irradiance_w_m2": (0, 1500),
        "dc_power_kw": (0, 5000),
        "inverter_power_kw": (0, 5000),
        "panel_temperature_c": (-20, 100),
    },

    "weather.csv": {
        "ambient_temperature_c": (-20, 60),
        "humidity_percent": (0, 100),
        "wind_speed_m_s": (0, 60),
        "cloud_cover_percent": (0, 100),
        "global_irradiance_w_m2": (0, 1500),
    }
}

# ==========================================================
# Validation
# ==========================================================

passed = 0
failed = 0

with open(LOG_FILE, "w", encoding="utf-8") as log:

    log.write("=" * 70 + "\n")
    log.write("RANGE VALIDATION REPORT\n")
    log.write("=" * 70 + "\n\n")

    for dataset, rules in RANGE_RULES.items():

        log.write("-" * 70 + "\n")
        log.write(f"Dataset : {dataset}\n")
        log.write("-" * 70 + "\n")

        file_path = RAW_DATA_DIR / dataset

        if not file_path.exists():
            log.write("[FAIL] File not found\n\n")
            failed += 1
            continue

        df = pd.read_csv(file_path)

        dataset_pass = True

        for column, (low, high) in rules.items():

            if column not in df.columns:
                log.write(f"[FAIL] Column '{column}' not found\n")
                dataset_pass = False
                continue

            invalid = df[(df[column] < low) | (df[column] > high)]

            if len(invalid) == 0:
                log.write(f"[PASS] {column}\n")
            else:
                dataset_pass = False
                log.write(
                    f"[FAIL] {column} : {len(invalid)} values outside "
                    f"range [{low}, {high}]\n"
                )

        if dataset_pass:
            log.write("\nSTATUS : PASSED\n\n")
            passed += 1
        else:
            log.write("\nSTATUS : FAILED\n\n")
            failed += 1

    log.write("=" * 70 + "\n")
    log.write("SUMMARY\n")
    log.write("=" * 70 + "\n")
    log.write(f"Total Datasets : {len(RANGE_RULES)}\n")
    log.write(f"Passed         : {passed}\n")
    log.write(f"Failed         : {failed}\n")

print("=" * 60)
print("RANGE VALIDATION COMPLETED")
print("=" * 60)
print(f"Passed : {passed}")
print(f"Failed : {failed}")
print(f"\nReport saved at:\n{LOG_FILE}")