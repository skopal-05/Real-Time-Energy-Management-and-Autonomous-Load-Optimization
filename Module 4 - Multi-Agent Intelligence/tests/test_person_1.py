"""Tests for Person 1 production agents."""

from __future__ import annotations

import json
import unittest

from production_agents import (
    CostOptimizationAgent,
    EnergyAllocator,
    LoadBalancingAgent,
    ProductionScheduler,
)


class CostOptimizationAgentTests(unittest.TestCase):
    def test_shifts_flexible_load_during_expensive_period(self) -> None:
        result = CostOptimizationAgent().optimize(
            {
                "production_load_kw": 100,
                "renewable_generation_kw": 20,
                "tariff_inr_kwh": 10,
                "off_peak_tariff_inr_kwh": 5,
                "flexible_load_fraction": 0.15,
            }
        )
        self.assertEqual(result.action, "shift_flexible_load")
        self.assertEqual(result.setpoints["load_to_shift_kw"], 15)
        self.assertEqual(result.expected_impact["estimated_savings_inr"], 75)

    def test_maintains_schedule_when_tariff_is_low(self) -> None:
        result = CostOptimizationAgent().decide(
            {
                "production_load_kw": 100,
                "tariff_inr_kwh": 6,
                "off_peak_tariff_inr_kwh": 4,
            }
        )
        self.assertEqual(result.action, "maintain_schedule")
        self.assertEqual(result.setpoints["load_to_shift_kw"], 0)

    def test_recommendation_is_json_serializable(self) -> None:
        result = CostOptimizationAgent().optimize(
            {"production_load_kw": 10, "tariff_inr_kwh": 5}
        )
        json.dumps(result.as_dict())

    def test_rejects_negative_load(self) -> None:
        with self.assertRaises(ValueError):
            CostOptimizationAgent().optimize(
                {"production_load_kw": -1, "tariff_inr_kwh": 5}
            )


class LoadBalancingAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = {
            "line_a": {
                "requested_power_kw": 70,
                "minimum_power_kw": 30,
                "maximum_power_kw": 80,
                "priority_weight": 2,
            },
            "line_b": {
                "requested_power_kw": 50,
                "minimum_power_kw": 20,
                "maximum_power_kw": 60,
                "priority_weight": 1,
            },
        }

    def test_serves_all_requests_when_power_is_available(self) -> None:
        result = LoadBalancingAgent().balance(self.lines, 150)
        targets = result.setpoints["line_power_targets_kw"]
        self.assertEqual(targets, {"line_a": 70, "line_b": 50})
        self.assertEqual(result.action, "serve_requested_load")

    def test_balances_shortage_without_exceeding_available_power(self) -> None:
        result = LoadBalancingAgent().balance(self.lines, 90)
        targets = result.setpoints["line_power_targets_kw"]
        self.assertAlmostEqual(sum(targets.values()), 90, places=2)
        self.assertGreaterEqual(targets["line_a"], 30)
        self.assertGreaterEqual(targets["line_b"], 20)
        self.assertGreater(targets["line_a"], targets["line_b"])

    def test_handles_power_below_combined_minimum(self) -> None:
        result = LoadBalancingAgent().balance(self.lines, 25)
        targets = result.setpoints["line_power_targets_kw"]
        self.assertLessEqual(sum(targets.values()), 25.01)
        self.assertEqual(result.priority, "high")

    def test_requires_lines(self) -> None:
        with self.assertRaises(ValueError):
            LoadBalancingAgent().balance({}, 10)


class ProductionSchedulerTests(unittest.TestCase):
    def test_prefers_renewable_low_cost_slot(self) -> None:
        jobs = [
            {"job_id": "job-1", "energy_kwh": 20, "deadline_slot": 1},
            {"job_id": "job-2", "energy_kwh": 10, "deadline_slot": 1},
        ]
        slots = [
            {
                "slot_id": "peak",
                "capacity_kwh": 40,
                "renewable_kwh": 0,
                "tariff_inr_kwh": 10,
            },
            {
                "slot_id": "solar",
                "capacity_kwh": 40,
                "renewable_kwh": 30,
                "tariff_inr_kwh": 7,
            },
        ]
        result = ProductionScheduler().schedule(jobs, slots)
        self.assertEqual(result.action, "schedule_production")
        self.assertEqual(
            {assignment["slot_id"] for assignment in result.setpoints["assignments"]},
            {"solar"},
        )
        self.assertEqual(result.expected_impact["renewable_energy_used_kwh"], 30)

    def test_flags_job_that_cannot_meet_deadline(self) -> None:
        result = ProductionScheduler().schedule(
            [{"job_id": "large", "energy_kwh": 50, "deadline_slot": 0}],
            [{"slot_id": "now", "capacity_kwh": 20, "tariff_inr_kwh": 5}],
        )
        self.assertEqual(result.action, "schedule_with_capacity_alert")
        self.assertEqual(result.setpoints["unscheduled_jobs"], ["large"])
        self.assertEqual(result.priority, "high")

    def test_rejects_job_without_identifier(self) -> None:
        with self.assertRaises(ValueError):
            ProductionScheduler().schedule(
                [{"energy_kwh": 10, "deadline_slot": 0}],
                [{"capacity_kwh": 10, "tariff_inr_kwh": 5}],
            )


class EnergyAllocatorTests(unittest.TestCase):
    def test_uses_renewable_then_economic_battery_then_grid(self) -> None:
        result = EnergyAllocator().allocate(
            {
                "production_demand_kw": 100,
                "renewable_available_kw": 30,
                "battery_discharge_available_kw": 25,
                "grid_import_limit_kw": 100,
                "battery_cost_inr_kwh": 2,
                "grid_tariff_inr_kwh": 8,
            }
        )
        self.assertEqual(
            {
                "renewable": result.setpoints["renewable_to_production_kw"],
                "battery": result.setpoints["battery_to_production_kw"],
                "grid": result.setpoints["grid_to_production_kw"],
            },
            {"renewable": 30, "battery": 25, "grid": 45},
        )
        self.assertEqual(result.setpoints["unserved_production_kw"], 0)

    def test_uses_grid_before_expensive_battery(self) -> None:
        result = EnergyAllocator().allocate(
            {
                "production_demand_kw": 80,
                "battery_discharge_available_kw": 40,
                "grid_import_limit_kw": 80,
                "battery_cost_inr_kwh": 10,
                "grid_tariff_inr_kwh": 5,
            }
        )
        self.assertEqual(result.setpoints["battery_to_production_kw"], 0)
        self.assertEqual(result.setpoints["grid_to_production_kw"], 80)

    def test_reports_supply_shortfall(self) -> None:
        result = EnergyAllocator().allocate(
            {
                "production_demand_kw": 100,
                "renewable_available_kw": 10,
                "battery_discharge_available_kw": 10,
                "grid_import_limit_kw": 20,
            }
        )
        self.assertEqual(result.action, "allocate_with_shortfall")
        self.assertEqual(result.priority, "critical")
        self.assertEqual(result.setpoints["unserved_production_kw"], 60)


if __name__ == "__main__":
    unittest.main()
