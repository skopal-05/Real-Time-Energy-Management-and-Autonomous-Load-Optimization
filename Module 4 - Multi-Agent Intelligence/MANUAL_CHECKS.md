# Week 4 Manual Checks

This guide verifies every implemented Week 4 deliverable assigned to Person 1
and Person 2. Run commands from:

```text
Module 4 - Multi-Agent Intelligence/
```

Person 3's `infrastructure_agents/`, `intelligence/`, and `integration/` work is
not implemented in this delivery. The final section provides the handoff checks
that Person 3 should satisfy later.

## 1. One-command verification

Run:

```bash
python3 manual_checks.py
```

Expected ending:

```text
Passed: 18/18
RESULT: ALL MANUAL CHECKS PASSED
```

Then run the automated suite:

```bash
python3 -m unittest discover -s tests -v
```

Expected ending:

```text
Ran 28 tests
OK
```

Compile every Python file:

```bash
python3 -m compileall -q .
```

Expected result: no output and exit status `0`.

## 2. Folder and deliverable check

Confirm these files exist:

```text
contracts.py
manual_checks.py
production_agents/
  cost_optimization_agent.py
  load_balancing_agent.py
  production_scheduler.py
  energy_allocator.py
renewable_agents/
  renewable_agent.py
  solar_dispatch_agent.py
  battery_management_agent.py
  grid_interaction_agent.py
tests/
  test_person_1.py
  test_person_2.py
README.md
RESEARCH.md
MANUAL_CHECKS.md
```

Expected result: all listed files are present. No external Python package is
required by these agents.

## 3. Shared recommendation contract

Open Python:

```bash
python3
```

Run:

```python
import json
from contracts import AgentRecommendation

result = AgentRecommendation(
    agent="demo",
    action="verify",
    priority="low",
    reason="Manual verification",
    setpoints={"target_kw": 10},
    expected_impact={"saving_inr": 5},
    constraints=("demo constraint",),
)

print(json.dumps(result.as_dict(), indent=2))
```

Expected checks:

- Output contains `agent`, `action`, `priority`, `reason`, `setpoints`,
  `expected_impact`, and `constraints`.
- `constraints` is serialized as a JSON list.
- Replacing `priority="low"` with an unsupported value raises `ValueError`.

Exit Python with `exit()`.

## 4. Person 1 - Cost Optimization Agent

Run:

```bash
python3 - <<'PY'
from production_agents import CostOptimizationAgent

agent = CostOptimizationAgent()

peak = agent.optimize({
    "production_load_kw": 100,
    "renewable_generation_kw": 20,
    "tariff_inr_kwh": 10,
    "off_peak_tariff_inr_kwh": 5,
    "flexible_load_fraction": 0.15,
})
print(peak.as_dict())

low = agent.optimize({
    "production_load_kw": 100,
    "tariff_inr_kwh": 6,
    "off_peak_tariff_inr_kwh": 4,
})
print(low.as_dict())
PY
```

Expected checks:

- Peak action is `shift_flexible_load`.
- `load_to_shift_kw` is `15.0`.
- `production_load_target_kw` is `85.0`.
- Estimated saving is `75.0 INR`.
- Low-tariff action is `maintain_schedule`.
- Low-tariff shifted load is `0.0`.

Invalid-input check:

```bash
python3 - <<'PY'
from production_agents import CostOptimizationAgent
CostOptimizationAgent().optimize({
    "production_load_kw": -1,
    "tariff_inr_kwh": 5,
})
PY
```

Expected result: `ValueError` because production load cannot be negative.

## 5. Person 1 - Load Balancing Agent

Run:

```bash
python3 - <<'PY'
from production_agents import LoadBalancingAgent

lines = {
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

for available in (150, 90, 25):
    result = LoadBalancingAgent().balance(lines, available)
    print(available, result.as_dict())
PY
```

Expected checks:

- At `150 kW`, line targets are `70 kW` and `50 kW`; action is
  `serve_requested_load`.
- At `90 kW`, allocated targets total exactly `90 kW`; both minimums are
  protected and Line A receives the larger priority-weighted share.
- At `25 kW`, targets do not exceed `25 kW`; the result reports curtailed power
  with high priority.
- No line exceeds its requested or maximum power.

## 6. Person 1 - Production Scheduler

Run:

```bash
python3 - <<'PY'
from production_agents import ProductionScheduler

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

print(ProductionScheduler().schedule(jobs, slots).as_dict())

print(ProductionScheduler().schedule(
    [{"job_id": "large", "energy_kwh": 50, "deadline_slot": 0}],
    [{"slot_id": "now", "capacity_kwh": 20, "tariff_inr_kwh": 5}],
).as_dict())
PY
```

Expected checks:

- Both feasible jobs are assigned to the `solar` slot.
- Renewable energy used is `30 kWh`.
- The infeasible `large` job appears in `unscheduled_jobs`.
- Infeasible scheduling returns `schedule_with_capacity_alert` and high priority.
- Slot capacity and deadline constraints are listed in the recommendation.

## 7. Person 1 - Energy Allocation Engine

Run:

```bash
python3 - <<'PY'
from production_agents import EnergyAllocator

normal = EnergyAllocator().allocate({
    "production_demand_kw": 100,
    "renewable_available_kw": 30,
    "battery_discharge_available_kw": 25,
    "grid_import_limit_kw": 100,
    "battery_cost_inr_kwh": 2,
    "grid_tariff_inr_kwh": 8,
})
print(normal.as_dict())

shortage = EnergyAllocator().allocate({
    "production_demand_kw": 100,
    "renewable_available_kw": 10,
    "battery_discharge_available_kw": 10,
    "grid_import_limit_kw": 20,
})
print(shortage.as_dict())
PY
```

Expected checks:

- Normal allocation is `30 kW` renewable, `25 kW` battery, and `45 kW` grid.
- Unserved production is `0 kW`.
- Renewable share is `30 percent`.
- Shortage allocation reports `60 kW` unserved production.
- Shortage action is `allocate_with_shortfall` with critical priority.

## 8. Person 2 - Renewable Agent

Run:

```bash
python3 - <<'PY'
from renewable_agents import RenewableAgent

result = RenewableAgent().optimize({
    "plant_demand_kw": 100,
    "solar_available_kw": 55,
    "battery_discharge_available_kw": 35,
    "battery_reserve_kw": 10,
})
print(result.as_dict())
PY
```

Expected checks:

- Solar supplies `55 kW`.
- Battery supplies only `25 kW`, preserving the `10 kW` reserve.
- Grid supplies the remaining `20 kW`.
- Renewable penetration is `80 percent`.

## 9. Person 2 - Solar Dispatch Agent

Run:

```bash
python3 - <<'PY'
from renewable_agents import SolarDispatchAgent

result = SolarDispatchAgent().dispatch({
    "solar_generation_kw": 100,
    "site_demand_kw": 40,
    "battery_charge_headroom_kw": 25,
    "battery_charge_limit_kw": 20,
    "grid_export_limit_kw": 30,
})
print(result.as_dict())
PY
```

Expected checks:

- `40 kW` goes to site load.
- `20 kW` goes to battery because the charge limit is lower than headroom.
- `30 kW` goes to grid export.
- The remaining `10 kW` is curtailed.
- Action is `dispatch_and_curtail`.

Zero-generation check:

```bash
python3 - <<'PY'
from renewable_agents import SolarDispatchAgent
print(SolarDispatchAgent().dispatch({
    "solar_generation_kw": 0,
    "site_demand_kw": 50,
}).as_dict())
PY
```

Expected result: all solar setpoints are zero and there is no division error.

## 10. Person 2 - Battery Management Agent

Run:

```bash
python3 - <<'PY'
from renewable_agents import BatteryManagementAgent

agent = BatteryManagementAgent()

charge = agent.manage({
    "state_of_charge_percent": 50,
    "capacity_kwh": 100,
    "renewable_surplus_kw": 30,
    "maximum_charge_kw": 20,
})
print("CHARGE", charge.as_dict())

discharge = agent.manage({
    "state_of_charge_percent": 60,
    "capacity_kwh": 100,
    "site_deficit_kw": 30,
    "tariff_inr_kwh": 10,
    "maximum_discharge_kw": 25,
})
print("DISCHARGE", discharge.as_dict())

reserve = agent.manage({
    "state_of_charge_percent": 20,
    "capacity_kwh": 100,
    "site_deficit_kw": 30,
    "tariff_inr_kwh": 10,
})
print("RESERVE", reserve.as_dict())
PY
```

Expected checks:

- Charge case selects `charge_from_renewable`, charges at `20 kW`, and projects
  `70 percent` SOC.
- Discharge case selects `discharge_to_load`, discharges at `25 kW`, and projects
  `35 percent` SOC.
- Reserve case selects `protect_reserve` and discharge remains `0 kW`.
- Projected SOC always remains between configured minimum and maximum SOC.

## 11. Person 2 - Grid Interaction Agent

Run:

```bash
python3 - <<'PY'
from renewable_agents import GridInteractionAgent

agent = GridInteractionAgent()

print("IMPORT", agent.interact({
    "net_demand_kw": 70,
    "grid_import_limit_kw": 100,
    "tariff_inr_kwh": 6,
}).as_dict())

print("EXPORT", agent.interact({
    "net_demand_kw": -50,
    "grid_export_limit_kw": 30,
    "export_price_inr_kwh": 4,
}).as_dict())

print("OVERLOAD", agent.interact({
    "net_demand_kw": 120,
    "grid_import_limit_kw": 80,
    "tariff_inr_kwh": 6,
}).as_dict())
PY
```

Expected checks:

- Import case imports `70 kW` with no unserved load.
- Export case exports `30 kW`, curtails `20 kW`, and reports `120 INR/hour`
  export revenue.
- Overload case limits import to `80 kW`, reports `40 kW` unserved load, and
  returns critical priority.

## 12. Combined JSON communication smoke check

Run:

```bash
python3 - <<'PY'
import json
from production_agents import EnergyAllocator
from renewable_agents import RenewableAgent

messages = [
    RenewableAgent().optimize({
        "plant_demand_kw": 100,
        "solar_available_kw": 30,
    }).as_dict(),
    EnergyAllocator().allocate({
        "production_demand_kw": 100,
        "renewable_available_kw": 30,
        "grid_import_limit_kw": 70,
    }).as_dict(),
]

payload = json.dumps(messages, indent=2)
print(payload)
json.loads(payload)
print("JSON COMMUNICATION CHECK: PASSED")
PY
```

Expected result: two complete recommendation objects followed by
`JSON COMMUNICATION CHECK: PASSED`.

## 13. Documentation and research check

Review:

- `README.md` contains scope, agent descriptions, output contract, test commands,
  example usage, units, and Person 3 integration handoff.
- `RESEARCH.md` covers multi-agent design, cost optimization, load balancing,
  scheduling, energy allocation, renewable optimization, solar allocation,
  battery strategies, grid management, assumptions, and limitations.
- `tests/test_person_1.py` covers all four Person 1 agents.
- `tests/test_person_2.py` covers all four Person 2 agents.

Expected result: no assigned Person 1 or Person 2 deliverable is undocumented or
untested.

## 14. Person 3 integration handoff checklist

These checks become applicable after Person 3 implements the remaining Week 4
scope:

- `infrastructure_agents/` contains HVAC, compressor, boiler, and equipment-health
  agents.
- `intelligence/` contains the base class, decision engine, rule engine,
  communication manager, and priority manager.
- `integration/agent_controller.py` consumes Module 3 forecast output and creates
  inputs for these Person 1 and Person 2 agents.
- The controller calls `as_dict()` before validating or serializing a
  recommendation.
- The priority manager recognizes `low`, `medium`, `high`, and `critical`.
- Conflicting battery recommendations are resolved before control actions are
  approved.
- Critical unserved-load recommendations override cost-saving recommendations.
- Approved recommendations are written under `outputs/recommendations/`.
- Optimized setpoints are written under `outputs/optimized_states/`.
- The complete integration test verifies Module 3 forecast input, all agent
  outputs, rule validation, conflict resolution, and JSON persistence.

Until these Person 3 files exist, do not claim that the complete Week 4
multi-agent engine or Module 3-to-Module 4 integration is finished.
