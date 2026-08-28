from runtime import DigitalTwinBase


class HVACDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "hvac",
            (
                "timestamp",
                "power_kw",
                "temperature_c",
                "airflow_m3_min",
                "humidity_percent",
                "setpoint_temperature_c",
                "efficiency_percent",
            ),
            {
                "power_kw": (0, 500),
                "temperature_c": (0, 50),
                "airflow_m3_min": (0, 5000),
                "humidity_percent": (0, 100),
                "setpoint_temperature_c": (10, 35),
                "efficiency_percent": (0, 100),
            },
            (
                "power_kw",
                "temperature_c",
                "airflow_m3_min",
            ),
            "efficiency_percent",
        )

    def _simulate(self, state):
        efficiency = min(100.0, max(0.0, self.predict_target(state)))
        power = float(state["power_kw"])
        airflow = float(state["airflow_m3_min"])

        return self._result(
            state,
            predicted_efficiency_percent=round(efficiency, 2),
            airflow_to_power_ratio=round(airflow / max(power, 0.01), 3),
            energy_loss_percent=round(100 - efficiency, 2),
        )