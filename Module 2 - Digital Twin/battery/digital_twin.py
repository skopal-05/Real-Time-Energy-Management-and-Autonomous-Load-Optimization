from runtime import DigitalTwinBase


class BatteryDigitalTwin(DigitalTwinBase):
    CAPACITY_KWH = 500.0

    def __init__(self):
        super().__init__(
            "battery",
            ("timestamp", "state_of_charge_percent", "battery_power_kw", "voltage_v", "current_a", "temperature_c"),
            {"state_of_charge_percent": (0, 100), "battery_power_kw": (-1000, 1000), "voltage_v": (0, 1500), "current_a": (-2000, 2000), "temperature_c": (-20, 100)},
            ("battery_power_kw", "voltage_v", "current_a", "temperature_c"),
            "state_of_charge_percent",
        )

    def _simulate(self, state):
        state_of_charge = float(state["state_of_charge_percent"])
        power = float(state["battery_power_kw"])
        duration = float(state.get("duration_hours", 0.25))
        # Week 1 uses positive power for charging and negative for discharging.
        next_soc = state_of_charge + power * duration / self.CAPACITY_KWH * 100
        next_soc = min(100.0, max(0.0, next_soc))
        mode = "charging" if power > 0 else "discharging" if power < 0 else "idle"
        return self._result(
            state,
            predicted_state_of_charge_percent=round(next_soc, 2),
            stored_energy_kwh=round(next_soc / 100 * self.CAPACITY_KWH, 2),
            power_mode=mode,
        )
