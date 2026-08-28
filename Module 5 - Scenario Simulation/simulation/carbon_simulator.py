"""Carbon impact model for grid electricity and boiler fuel."""

from __future__ import annotations

from typing import Mapping


class CarbonSimulator:
    """Calculate direct and purchased-energy emissions in kg CO2e."""

    def __init__(
        self,
        *,
        grid_factor_kg_kwh: float = 0.716,
        natural_gas_factor_kg_m3: float = 2.0,
    ) -> None:
        if grid_factor_kg_kwh < 0 or natural_gas_factor_kg_m3 < 0:
            raise ValueError("emission factors must be non-negative")
        self.grid_factor = grid_factor_kg_kwh
        self.gas_factor = natural_gas_factor_kg_m3

    def simulate(self, energy: Mapping[str, float]) -> dict[str, float]:
        grid = energy["grid_import_kwh"] * self.grid_factor
        fuel = energy["boiler_fuel_m3"] * self.gas_factor
        total = grid + fuel
        return {
            "grid_emissions_kg_co2e": round(grid, 3),
            "fuel_emissions_kg_co2e": round(fuel, 3),
            "total_emissions_kg_co2e": round(total, 3),
        }
