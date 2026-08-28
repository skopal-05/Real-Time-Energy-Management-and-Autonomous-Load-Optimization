# Module 5 - Generative Scenario Simulation

## Overview

Module 5 is the scenario simulation and decision evaluation layer of the
Generative Digital Twin project.

It integrates:

- Forecasted system states from Module 3
- Agent recommendations from Module 4
- What-if scenario generation
- Energy simulation
- Cost simulation
- Carbon impact simulation
- Multi-objective scenario evaluation
- Scenario ranking and best-scenario selection
- End-to-end integration validation

The module answers the question:

> "What happens if the system operates under different future strategies?"

Instead of directly applying a single recommendation, Module 5 generates
multiple possible operating scenarios, simulates their outcomes, compares
them, and selects the best-performing scenario.

---

## Module Workflow

    Module 3 - Forecasting
            |
            | forecast_output.json
            v
    Module 5 - Scenario Simulation
            |
            +------------------------------+
            |                              |
            v                              v
    Module 4 Recommendations        Scenario Generator
            |                              |
            | recommendations.json         |
            +--------------+---------------+
                           |
                           v
                    Generated Scenarios
                           |
                           v
                    Energy Simulator
                           |
                  +--------+--------+
                  |        |        |
                  v        v        v
                Cost     Carbon   Energy
               Simulator Simulator Simulator
                  |        |        |
                  +--------+--------+
                           |
                           v
                   Scenario Evaluator
                           |
                           v
                    Scenario Ranker
                           |
                           v
                     Best Scenario
                           |
                           v
                    Output JSON Files

---

## Main Components

### 1. Scenario Generator

Location:

    scenario_generator/scenario_generator.py

The Scenario Generator converts Module 3 forecasts and Module 4
recommendations into multiple operating scenarios.

Responsibilities:

- Read future system state from Module 3
- Read agent recommendations from Module 4
- Extract feasible equipment setpoints
- Generate predefined what-if scenarios
- Apply scenario-specific operating conditions
- Handle battery charging/discharging logic
- Validate every generated scenario

Production output is represented separately as `units_per_hour`.

It is not converted into electrical kW because the current Module 3
forecasting pipeline does not provide a production electrical-power forecast.

---

## 2. Scenario Templates

Location:

    scenario_generator/scenario_templates.py

Five predefined scenarios are generated:

| Scenario | Purpose |
|---|---|
| Forecast Baseline | Uses the forecasted operating point without optimization |
| Agent Optimized | Applies Module 4 equipment and dispatch recommendations |
| Renewable Priority | Prioritizes renewable utilization, battery charging and export |
| Cost Saver | Applies agent targets with reduced modeled electrical demand |
| Renewable Shortfall Resilience | Tests reduced renewable availability with battery support |

The templates define:

- Scenario ID
- Scenario name
- Description
- Electrical load factor
- Renewable generation factor
- Whether Module 4 agent targets are applied
- Grid export limit
- Battery operating mode

---

## 3. Scenario Validator

Location:

    scenario_generator/scenario_validator.py

The Scenario Validator validates generated Scenario objects before they
enter the simulation stage.

It checks:

- Scenario ID is present
- Simulation horizon is positive and finite
- Required operating values are present
- Operating values are numeric
- Operating values are finite
- Operating values are non-negative
- Battery cannot charge and discharge simultaneously

Invalid scenarios are rejected before simulation.

---

## 4. Energy Simulator

Location:

    simulation/energy_simulator.py

The Energy Simulator performs the electrical energy balance for each
scenario.

It calculates:

- Useful electrical load
- Site consumption
- Renewable generation
- Renewable energy used
- Renewable share
- Battery charging
- Battery discharging
- Grid import
- Grid export
- Curtailed energy
- Boiler fuel consumption

The energy dispatch logic follows:

    Renewable Generation
            |
            v
    Serve Electrical Load
            |
            +---- Surplus ----> Battery
            |                    |
            |                    +---- Remaining Surplus
            |                              |
            |                              v
            |                         Grid Export
            |
            +---- Deficit ----> Battery Discharge
                                      |
                                      +---- Remaining Deficit
                                                |
                                                v
                                           Grid Import

This provides an auditable energy balance for every scenario.

---

## 5. Cost Simulator

Location:

    simulation/cost_simulator.py

The Cost Simulator calculates the financial impact of each scenario.

It considers:

- Grid electricity import cost
- Boiler fuel cost
- Battery degradation cost
- Grid export revenue
- Gross operating cost
- Net operating cost

Default parameters:

    Grid import tariff       = ₹8.00/kWh
    Grid export price        = ₹4.00/kWh
    Natural gas/fuel price   = ₹48.00/m³
    Battery degradation      = ₹1.50/kWh

The final net operating cost is calculated as:

    Net Operating Cost
        = Grid Import Cost
        + Fuel Cost
        + Battery Degradation Cost
        - Export Revenue

---

## 6. Carbon Simulator

Location:

    simulation/carbon_simulator.py

The Carbon Simulator calculates scenario-level greenhouse gas emissions.

It considers:

- Grid electricity emissions
- Boiler fuel emissions
- Total CO2e emissions

Default emission factors:

    Grid electricity = 0.716 kg CO2e/kWh
    Natural gas      = 2.0 kg CO2e/m³

The total emissions are calculated as:

    Total Emissions
        = Grid Emissions
        + Fuel Emissions

---

## 7. Scenario Evaluator

Location:

    ranking/scenario_evaluator.py

The Scenario Evaluator runs every generated scenario through the common
simulation models:

    Scenario
       |
       +--> Energy Simulator
       |
       +--> Cost Simulator
       |
       +--> Carbon Simulator
       |
       v
    ScenarioResult

It then compares every scenario against the baseline.

The evaluator calculates:

- Energy saving
- Cost saving
- Emissions avoided

This ensures that all scenarios are evaluated using the same energy,
financial, and carbon models.

---

## 8. Scenario Ranker

Location:

    ranking/scenario_ranker.py

The Scenario Ranker performs multi-objective scenario ranking.

Current objective weights are:

    Energy = 35%
    Cost   = 35%
    Carbon = 30%

The ranking process is:

    Scenario Results
            |
            v
    Normalize Energy
            |
            v
    Normalize Cost
            |
            v
    Normalize Carbon
            |
            v
    Apply Objective Weights
            |
            v
    Final Score (0-100)
            |
            v
    Scenario Ranking

Lower energy consumption, lower operating cost, and lower carbon emissions
are treated as better outcomes.

The scenario with the highest weighted score receives Rank 1.

---

## 9. Integration Layer

Location:

    integration/

The integration layer connects Module 3, Module 4, and Module 5.

### Scenario Controller

Location:

    integration/scenario_controller.py

The Scenario Controller is responsible for the complete Module 5 workflow.

It:

1. Loads Module 3 forecast output
2. Loads Module 4 recommendation output
3. Validates incoming data
4. Generates operating scenarios
5. Simulates energy flows
6. Calculates costs
7. Calculates carbon emissions
8. Evaluates scenarios
9. Ranks scenarios
10. Selects the best scenario
11. Generates the final report
12. Saves output JSON files

Default Module 3 input:

    Module 3 - Forecasting/
    └── outputs/
        └── forecast_output.json

Default Module 4 input:

    Module 4 - Multi-Agent Intelligence/
    └── outputs/
        └── recommendations/
            └── recommendations.json

### Integration Validator

Location:

    integration/scenario_validator.py

The Integration Validator checks the contracts between Modules 3, 4,
and 5.

It validates:

- Module 3 forecast structure
- Required forecast values
- Module 4 recommendation structure
- Recommendation fields
- Scenario count
- Scenario identifiers
- Ranking sequence
- Score range
- Energy-flow constraints
- Battery charge/discharge constraints

### Integration Test

Location:

    integration/integration_test.py

The integration test provides executable end-to-end validation.

It verifies:

- Five scenarios are generated
- Expected scenario identifiers exist
- Scenario ranks are valid
- Best scenario has Rank 1
- Baseline electrical load is correct
- Ranking scores are between 0 and 100
- Grid import/export values are valid
- Battery does not charge and discharge simultaneously
- Required output files are generated

---

## Data Contracts

### Module 3 Input

Module 5 consumes:

    Module 3 - Forecasting/
    └── outputs/
        └── forecast_output.json

Expected top-level structure:

    {
        "future_state": {},
        "energy_forecast": {}
    }

Important values include:

    future_state
        compressor_power_kw
        hvac_power_kw
        inverter_power_kw
        fuel_flow_m3_hr
        units_per_hour

    energy_forecast
        total_load_kw
        renewable_generation_kw
        boiler_fuel_flow_m3_hr

The production model predicts:

    units_per_hour

This represents production output and is not directly treated as
electrical load.

The electrical load currently modeled in Module 5 comes from the explicitly
forecasted electrical equipment:

    Compressor Power
          +
    HVAC Power
          =
    Useful Electrical Load

---

### Module 4 Input

Module 5 consumes:

    Module 4 - Multi-Agent Intelligence/
    └── outputs/
        └── recommendations/
            └── recommendations.json

Each recommendation can contain:

    agent
    action
    priority
    reason
    setpoints
    expected_impact
    constraints

Relevant equipment setpoints include:

    compressor_power_target_kw
    hvac_power_target_kw
    boiler_fuel_target_m3_hr
    battery_charge_kw
    battery_discharge_kw

These recommendations are used by the Scenario Generator when generating
agent-based scenarios.

---

## Scenario Output

Module 5 generates the following output structure:

    outputs/
    ├── scenarios/
    │   └── generated_scenarios.json
    │
    ├── comparisons/
    │   └── scenario_comparison.json
    │
    ├── best_scenario/
    │   └── best_scenario.json
    │
    └── reports/
        └── simulation_report.json

### generated_scenarios.json

Contains:

- All generated scenarios
- Scenario operating points
- Applied recommendations
- Scenario assumptions
- Simulation horizon

### scenario_comparison.json

Contains:

- Ranked scenarios
- Energy metrics
- Cost metrics
- Carbon metrics
- Component scores
- Overall weighted scores

### best_scenario.json

Contains the highest-ranked scenario and its complete simulation results.

### simulation_report.json

Contains:

- Generation timestamp
- Input file summary
- Recommendation count
- Ranking weights
- Scenario count
- Best scenario ID
- Best scenario name
- Best scenario score
- Baseline comparison
- Simulation status

---

## Running Module 5

From the Module 5 directory:

    cd "E:\Final year Project\DigitalTwin-AI\Module 5 - Scenario Simulation"

Run the complete integration test:

    py -m integration.integration_test

Expected successful output:

    ================================================================
    Module 5 - Generative Scenario Simulation Integration Test
    ================================================================
    PASS scenario count: 5
    PASS scenario identifiers: [...]
    PASS ranking: best = Cost Saver
    PASS baseline electrical load: 68.700 kWh
    PASS ranking scores are within 0-100
    PASS energy-flow constraints
    PASS output scenarios: ...
    PASS output comparisons: ...
    PASS output best_scenario: ...
    PASS output report: ...
    ----------------------------------------------------------------
    Scenarios generated and ranked: 5
    Best scenario: Cost Saver
    Weighted score: 100.00/100
    ----------------------------------------------------------------
    INTEGRATION TEST PASSED

The complete scenario controller can also be executed using:

    py -m integration.scenario_controller

---

## Current Validation Result

The current Module 5 integration test successfully validates the complete
pipeline:

    Module 3 Forecast
            ↓
    Module 4 Recommendations
            ↓
    Scenario Generation
            ↓
    Energy Simulation
            ↓
    Cost Simulation
            ↓
    Carbon Simulation
            ↓
    Scenario Evaluation
            ↓
    Scenario Ranking
            ↓
    Best Scenario
            ↓
    JSON Outputs

Current validation confirms:

    Scenario count              = 5
    Baseline electrical load   = 68.700 kWh
    Best scenario              = Cost Saver
    Best weighted score        = 100.00/100
    Integration test           = PASSED

The baseline electrical load is calculated from the explicitly forecasted
compressor and HVAC loads without double counting.

---

## Project Role

Module 5 acts as the what-if simulation and decision evaluation layer of
the Generative Digital Twin.

The overall project flow is:

    Module 1 / Module 2
            ↓
    Data Acquisition & Digital Twin State
            ↓
    Module 3
    Forecasting
            ↓
    Module 4
    Multi-Agent Intelligence
            ↓
    Module 5
    Scenario Simulation
            ↓
    Energy + Cost + Carbon Evaluation
            ↓
    Multi-Objective Ranking
            ↓
    Best Operating Scenario

Module 3 predicts future operating conditions.

Module 4 produces intelligent recommendations.

Module 5 evaluates the consequences of different operating strategies and
identifies the scenario with the best combined energy, cost, and carbon
performance.