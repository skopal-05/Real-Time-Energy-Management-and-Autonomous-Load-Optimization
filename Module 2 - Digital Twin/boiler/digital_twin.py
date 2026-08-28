from runtime import DigitalTwinBase


class BoilerDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "boiler",
            ("timestamp", "steam_pressure_bar", "steam_flow_kg_hr", "fuel_flow_m3_hr", "feedwater_temperature_c", "flue_gas_temperature_c", "efficiency_percent"),
            {"steam_pressure_bar": (0, 30), "steam_flow_kg_hr": (0, 10000), "fuel_flow_m3_hr": (0, 1000), "feedwater_temperature_c": (0, 180), "flue_gas_temperature_c": (0, 500), "efficiency_percent": (0, 100)},
            ("steam_flow_kg_hr", "fuel_flow_m3_hr", "flue_gas_temperature_c"),
            "efficiency_percent",
        )

    def _simulate(self, state):
        efficiency = min(100.0, max(0.0, self.predict_target(state)))
        steam = float(state["steam_flow_kg_hr"])
        fuel = float(state["fuel_flow_m3_hr"])
        return self._result(
            state,
            predicted_efficiency_percent=round(efficiency, 2),
            steam_to_fuel_ratio=round(steam / max(fuel, 0.01), 3),
            thermal_loss_percent=round(100 - efficiency, 2),
        )
