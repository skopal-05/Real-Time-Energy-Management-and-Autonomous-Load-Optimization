from runtime import DigitalTwinBase


class ProductionLineBDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "production_line_b",
            ("timestamp", "units_per_hour", "machine_load_kw", "motor_temperature_c", "vibration_mm_s"),
            {"units_per_hour": (0, 120), "machine_load_kw": (0, 150), "motor_temperature_c": (0, 120), "vibration_mm_s": (0, 15)},
            ("machine_load_kw", "motor_temperature_c", "vibration_mm_s"),
            "units_per_hour",
        )

    def _simulate(self, state):
        output = max(0.0, self.predict_target(state))
        load = float(state["machine_load_kw"])
        return self._result(
            state,
            predicted_units_per_hour=round(output, 2),
            energy_per_hour_kwh=round(load, 2),
            specific_energy_kwh_per_unit=round(load / max(output, 0.01), 3),
        )
