from runtime import DigitalTwinBase


class SolarDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "solar",
            ("timestamp", "irradiance_w_m2", "dc_power_kw", "inverter_power_kw", "panel_temperature_c"),
            {"irradiance_w_m2": (0, 1500), "dc_power_kw": (0, 2000), "inverter_power_kw": (0, 2000), "panel_temperature_c": (-20, 100)},
            ("irradiance_w_m2", "panel_temperature_c", "dc_power_kw"),
            "inverter_power_kw",
        )

    def _simulate(self, state):
        inverter_power = max(0.0, self.predict_target(state))
        dc_power = float(state["dc_power_kw"])
        efficiency = min(100.0, inverter_power / max(dc_power, 0.01) * 100)
        return self._result(
            state,
            predicted_inverter_power_kw=round(inverter_power, 2),
            conversion_efficiency_percent=round(efficiency, 2),
            energy_15_min_kwh=round(inverter_power * 0.25, 2),
        )
