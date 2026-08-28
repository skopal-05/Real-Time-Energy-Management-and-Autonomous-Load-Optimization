"""Tests for Person 2 renewable and grid agents."""

from __future__ import annotations

import json
import unittest

from renewable_agents import (
    BatteryManagementAgent,
    GridInteractionAgent,
    RenewableAgent,
    SolarDispatchAgent,
)


class RenewableAgentTests(unittest.TestCase):
    def test_dispatches_renewables_before_grid(self) -> None:
        result = RenewableAgent().optimize(
            {
                "plant_demand_kw": 100,
                "solar_available_kw": 55,
                "battery_discharge_available_kw": 35,
                "battery_reserve_kw": 10,
            }
        )
        self.assertEqual(result.setpoints["solar_to_load_kw"], 55)
        self.assertEqual(result.setpoints["battery_to_load_kw"], 25)
        self.assertEqual(result.setpoints["grid_to_load_kw"], 20)
        self.assertEqual(result.expected_impact["renewable_penetration_percent"], 80)

    def test_preserves_battery_reserve(self) -> None:
        result = RenewableAgent().optimize(
            {
                "plant_demand_kw": 30,
                "battery_discharge_available_kw": 10,
                "battery_reserve_kw": 10,
            }
        )
        self.assertEqual(result.setpoints["battery_to_load_kw"], 0)
        self.assertEqual(result.setpoints["grid_to_load_kw"], 30)

    def test_output_is_json_serializable(self) -> None:
        result = RenewableAgent().optimize({"plant_demand_kw": 0})
        json.dumps(result.as_dict())


class SolarDispatchAgentTests(unittest.TestCase):
    def test_dispatch_order_is_load_battery_grid(self) -> None:
        result = SolarDispatchAgent().dispatch(
            {
                "solar_generation_kw": 100,
                "site_demand_kw": 40,
                "battery_charge_headroom_kw": 25,
                "battery_charge_limit_kw": 20,
                "grid_export_limit_kw": 30,
            }
        )
        self.assertEqual(result.setpoints["solar_to_load_kw"], 40)
        self.assertEqual(result.setpoints["solar_to_battery_kw"], 20)
        self.assertEqual(result.setpoints["solar_to_grid_kw"], 30)
        self.assertEqual(result.setpoints["solar_curtailed_kw"], 10)

    def test_zero_generation_is_safe(self) -> None:
        result = SolarDispatchAgent().dispatch(
            {"solar_generation_kw": 0, "site_demand_kw": 50}
        )
        self.assertEqual(result.expected_impact["self_consumption_percent"], 100)
        self.assertEqual(result.setpoints["solar_curtailed_kw"], 0)

    def test_rejects_negative_generation(self) -> None:
        with self.assertRaises(ValueError):
            SolarDispatchAgent().dispatch(
                {"solar_generation_kw": -1, "site_demand_kw": 10}
            )


class BatteryManagementAgentTests(unittest.TestCase):
    def test_charges_from_renewable_surplus(self) -> None:
        result = BatteryManagementAgent().manage(
            {
                "state_of_charge_percent": 50,
                "capacity_kwh": 100,
                "renewable_surplus_kw": 30,
                "maximum_charge_kw": 20,
                "interval_hours": 1,
            }
        )
        self.assertEqual(result.action, "charge_from_renewable")
        self.assertEqual(result.setpoints["battery_charge_kw"], 20)
        self.assertEqual(result.setpoints["projected_soc_percent"], 70)

    def test_discharges_during_peak_price(self) -> None:
        result = BatteryManagementAgent().manage(
            {
                "state_of_charge_percent": 60,
                "capacity_kwh": 100,
                "site_deficit_kw": 30,
                "tariff_inr_kwh": 10,
                "maximum_discharge_kw": 25,
            }
        )
        self.assertEqual(result.action, "discharge_to_load")
        self.assertEqual(result.setpoints["battery_discharge_kw"], 25)
        self.assertEqual(result.setpoints["projected_soc_percent"], 35)

    def test_protects_minimum_soc(self) -> None:
        result = BatteryManagementAgent().manage(
            {
                "state_of_charge_percent": 20,
                "capacity_kwh": 100,
                "site_deficit_kw": 30,
                "tariff_inr_kwh": 10,
            }
        )
        self.assertEqual(result.action, "protect_reserve")
        self.assertEqual(result.setpoints["battery_discharge_kw"], 0)

    def test_does_not_discharge_for_low_tariff(self) -> None:
        result = BatteryManagementAgent().manage(
            {
                "state_of_charge_percent": 60,
                "capacity_kwh": 100,
                "site_deficit_kw": 30,
                "tariff_inr_kwh": 5,
            }
        )
        self.assertEqual(result.action, "standby")


class GridInteractionAgentTests(unittest.TestCase):
    def test_imports_within_limit(self) -> None:
        result = GridInteractionAgent().interact(
            {
                "net_demand_kw": 70,
                "grid_import_limit_kw": 100,
                "tariff_inr_kwh": 6,
            }
        )
        self.assertEqual(result.action, "import_power")
        self.assertEqual(result.setpoints["grid_import_kw"], 70)
        self.assertEqual(result.setpoints["unserved_load_kw"], 0)

    def test_reports_unserved_load_over_import_limit(self) -> None:
        result = GridInteractionAgent().interact(
            {
                "net_demand_kw": 120,
                "grid_import_limit_kw": 80,
                "tariff_inr_kwh": 6,
            }
        )
        self.assertEqual(result.action, "limit_import_and_shed_load")
        self.assertEqual(result.priority, "critical")
        self.assertEqual(result.setpoints["unserved_load_kw"], 40)

    def test_exports_surplus_and_reports_revenue(self) -> None:
        result = GridInteractionAgent().interact(
            {
                "net_demand_kw": -50,
                "grid_export_limit_kw": 30,
                "export_price_inr_kwh": 4,
            }
        )
        self.assertEqual(result.action, "export_surplus")
        self.assertEqual(result.setpoints["grid_export_kw"], 30)
        self.assertEqual(result.setpoints["curtailed_export_kw"], 20)
        self.assertEqual(result.expected_impact["export_revenue_inr_per_hour"], 120)

    def test_balanced_site_avoids_grid_exchange(self) -> None:
        result = GridInteractionAgent().interact(
            {"net_demand_kw": 0, "grid_import_limit_kw": 100}
        )
        self.assertEqual(result.action, "islanded_balance")


if __name__ == "__main__":
    unittest.main()
