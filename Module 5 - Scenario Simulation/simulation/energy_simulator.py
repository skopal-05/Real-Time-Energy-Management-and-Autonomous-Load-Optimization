"""Electrical and fuel energy simulation for operating scenarios."""

from __future__ import annotations

from contracts import Scenario


class EnergySimulator:
    """Apply an auditable one-interval energy balance."""

    def simulate(self, scenario: Scenario) -> dict[str, float]:
        point = scenario.operating_point
        hours = scenario.horizon_hours
        useful_load_kw = (
            point["production_load_kw"]
            + point["compressor_power_kw"]
            + point["hvac_power_kw"]
        )
        charge_kw = point["battery_charge_kw"]
        discharge_kw = point["battery_discharge_kw"]
        renewable_kw = point["renewable_generation_kw"]
        site_consumption_kw = useful_load_kw + charge_kw
        available_supply_kw = renewable_kw + discharge_kw
        grid_import_kw = max(0.0, site_consumption_kw - available_supply_kw)
        surplus_kw = max(0.0, available_supply_kw - site_consumption_kw)
        grid_export_kw = min(point["grid_export_limit_kw"], surplus_kw)
        curtailed_kw = max(0.0, surplus_kw - grid_export_kw)
        renewable_used_kw = min(renewable_kw, site_consumption_kw + grid_export_kw)
        renewable_share = (
            min(100.0, 100.0 * renewable_used_kw / site_consumption_kw)
            if site_consumption_kw
            else 100.0
        )
        return {
            "useful_electrical_load_kwh": round(useful_load_kw * hours, 3),
            "site_consumption_kwh": round(site_consumption_kw * hours, 3),
            "renewable_generation_kwh": round(renewable_kw * hours, 3),
            "renewable_used_kwh": round(renewable_used_kw * hours, 3),
            "renewable_share_percent": round(renewable_share, 2),
            "battery_charge_kwh": round(charge_kw * hours, 3),
            "battery_discharge_kwh": round(discharge_kw * hours, 3),
            "grid_import_kwh": round(grid_import_kw * hours, 3),
            "grid_export_kwh": round(grid_export_kw * hours, 3),
            "curtailed_energy_kwh": round(curtailed_kw * hours, 3),
            "boiler_fuel_m3": round(point["boiler_fuel_m3_hr"] * hours, 3),
        }
