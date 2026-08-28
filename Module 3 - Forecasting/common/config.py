"""
Configuration for AI Forecasting Module.
"""

from __future__ import annotations

MODULE_CONFIG = {

    # =====================================================
    # Production
    # =====================================================

    "production": {

        "model": "production_rf",

        "target": "units_per_hour",

        "features": [
            "machine_load_kw",
            "motor_temperature_c",
            "vibration_mm_s",
            "status",
        ],

        "encoders": {
            "status": "production_encoder",
        },
    },

    # =====================================================
    # Boiler
    # =====================================================

    "boiler": {

        "model": "boiler_rf",

        # Changed target
        "target": "fuel_flow_m3_hr",

        "features": [
            "steam_pressure_bar",
            "feedwater_temperature_c",
            "flue_gas_temperature_c",
            "efficiency_percent",
        ],

        "encoders": {},
    },

    # =====================================================
    # Compressor
    # =====================================================

    "compressor": {

        "model": "compressor_rf",

        # Changed target
        "target": "power_kw",

        "features": [
            "air_pressure_bar",
            "motor_temperature_c",
            "vibration_mm_s",
            "efficiency_percent",
            "status",
        ],

        "encoders": {
            "status": "compressor_encoder",
        },
    },

    # =====================================================
    # HVAC
    # =====================================================

    "hvac": {

        "model": "hvac_rf",

        "target": "power_kw",

        "features": [
            "temperature_c",
            "airflow_m3_min",
            "humidity_percent",
            "setpoint_temperature_c",
            "efficiency_percent",
            "status",
        ],

        "encoders": {
            "status": "hvac_encoder",
        },
    },

    # =====================================================
    # Battery
    # =====================================================

    "battery": {

        "model": "battery_rf",

        # Changed target
        "target": "battery_power_kw",

        "features": [
            "voltage_v",
            "current_a",
            "temperature_c",
            "mode",
            "state_of_charge_percent",
        ],

        "encoders": {
            "mode": "battery_encoder",
        },
    },

    # =====================================================
    # Grid
    # =====================================================

    "grid": {

        "model": "grid_rf",

        "target": "grid_import_kw",

        "features": [
            "grid_export_kw",
            "frequency_hz",
            "voltage_v",
            "power_factor",
            "tariff_inr_kwh",
        ],

        "encoders": {},
    },

    # =====================================================
    # Solar
    # =====================================================

    "solar": {

        "model": "solar_rf",

        # Changed target
        "target": "inverter_power_kw",

        "features": [
            "irradiance_w_m2",
            "panel_temperature_c",
            "inverter_status",
        ],

        "encoders": {
            "inverter_status": "solar_encoder",
        },
    },
}