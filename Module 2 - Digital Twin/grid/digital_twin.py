from runtime import DigitalTwinBase


class GridDigitalTwin(DigitalTwinBase):
    def __init__(self):
        super().__init__(
            "grid",
            ("timestamp", "grid_import_kw", "grid_export_kw", "frequency_hz", "voltage_v", "power_factor", "tariff_inr_kwh"),
            {"grid_import_kw": (0, 10000), "grid_export_kw": (0, 10000), "frequency_hz": (45, 55), "voltage_v": (300, 500), "power_factor": (0, 1), "tariff_inr_kwh": (0, 100)},
            ("grid_export_kw", "frequency_hz", "voltage_v", "power_factor", "tariff_inr_kwh"),
            "grid_import_kw",
        )

    def _simulate(self, state):
        imported = max(0.0, self.predict_target(state))
        exported = float(state["grid_export_kw"])
        tariff = float(state["tariff_inr_kwh"])
        net_power = imported - exported
        return self._result(
            state,
            predicted_grid_import_kw=round(imported, 2),
            net_grid_power_kw=round(net_power, 2),
            estimated_cost_inr_15_min=round(max(0.0, net_power) * tariff * 0.25, 2),
            grid_stable=49.5 <= float(state["frequency_hz"]) <= 50.5,
        )
