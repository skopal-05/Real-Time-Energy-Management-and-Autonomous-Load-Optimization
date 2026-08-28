"""Cost model for scenario energy flows."""

from __future__ import annotations

from typing import Mapping


class CostSimulator:
    """Calculate grid, fuel, battery, and net operating costs in INR."""

    def __init__(
        self,
        *,
        import_tariff_inr_kwh: float = 8.0,
        export_price_inr_kwh: float = 4.0,
        fuel_price_inr_m3: float = 48.0,
        battery_degradation_inr_kwh: float = 1.5,
    ) -> None:
        for name, value in {
            "import tariff": import_tariff_inr_kwh,
            "export price": export_price_inr_kwh,
            "fuel price": fuel_price_inr_m3,
            "battery degradation": battery_degradation_inr_kwh,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        self.import_tariff = import_tariff_inr_kwh
        self.export_price = export_price_inr_kwh
        self.fuel_price = fuel_price_inr_m3
        self.battery_degradation = battery_degradation_inr_kwh

    def simulate(self, energy: Mapping[str, float]) -> dict[str, float]:
        grid_cost = energy["grid_import_kwh"] * self.import_tariff
        export_revenue = energy["grid_export_kwh"] * self.export_price
        fuel_cost = energy["boiler_fuel_m3"] * self.fuel_price
        battery_cost = (
            energy["battery_charge_kwh"] + energy["battery_discharge_kwh"]
        ) * self.battery_degradation
        gross_cost = grid_cost + fuel_cost + battery_cost
        return {
            "grid_import_cost_inr": round(grid_cost, 2),
            "fuel_cost_inr": round(fuel_cost, 2),
            "battery_degradation_cost_inr": round(battery_cost, 2),
            "export_revenue_inr": round(export_revenue, 2),
            "gross_operating_cost_inr": round(gross_cost, 2),
            "net_operating_cost_inr": round(gross_cost - export_revenue, 2),
        }
