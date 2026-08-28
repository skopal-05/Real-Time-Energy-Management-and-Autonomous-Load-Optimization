from runtime import DigitalTwinBase


class CompressorDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "compressor",
            (
                "timestamp",
                "power_kw",
                "air_pressure_bar",
                "air_flow_m3_min",
                "motor_temperature_c",
                "vibration_mm_s",
                "efficiency_percent",
            ),
            {
                "power_kw": (0, 500),
                "air_pressure_bar": (0, 20),
                "air_flow_m3_min": (0, 5000),
                "motor_temperature_c": (0, 150),
                "vibration_mm_s": (0, 50),
                "efficiency_percent": (0, 100),
            },
            (
                "power_kw",
                "air_pressure_bar",
                "air_flow_m3_min",
            ),
            "efficiency_percent",
        )

    def _simulate(self, state):
        efficiency = min(100.0, max(0.0, self.predict_target(state)))
        airflow = float(state["air_flow_m3_min"])
        power = float(state["power_kw"])

        return self._result(
            state,
            predicted_efficiency_percent=round(efficiency, 2),
            airflow_to_power_ratio=round(airflow / max(power, 0.01), 3),
            energy_loss_percent=round(100 - efficiency, 2),
        )