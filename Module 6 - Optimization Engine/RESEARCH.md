# Module 6 Research Notes

## Optimization Methods Considered

### Rule-based optimization

Rule-based control is easy to explain and fast enough for real-time use, but
it explores only actions anticipated by the rule author. It is retained in
Module 6 as deterministic constraint repair and renewable-dispatch polishing,
not as the main search method.

### Linear and mixed-integer optimization

Linear programming is a strong choice when equipment behavior, costs, and
constraints can all be represented linearly. Mixed-integer programming also
supports on/off decisions and scheduling. The current project does not yet
provide sufficiently detailed production curves, equipment efficiency curves,
or binary operating modes to justify a full mathematical-programming model.

### Genetic algorithms

Genetic algorithms support bounded continuous variables, non-linear objective
functions, and penalty-based constraint handling without requiring gradients.
They are also straightforward to demonstrate using candidate populations,
selection, crossover, mutation, and elitism. These properties fit the Week 6
requirement and the current Module 4/5 JSON data.

The implementation uses a real-valued Genetic Algorithm with:

- tournament selection;
- arithmetic crossover;
- Gaussian mutation;
- elitism;
- a deterministic random seed;
- bound and SOC repair; and
- penalties for infeasible operating states.

### Multi-objective evolutionary algorithms

NSGA-II is a well-established alternative that uses elitism and non-dominated
sorting to generate a Pareto set instead of one weighted solution. See Deb,
Pratap, Agarwal, and Meyarivan, "A Fast and Elitist Multiobjective Genetic
Algorithm: NSGA-II," *IEEE Transactions on Evolutionary Computation*, 6(2),
182-197, 2002: https://doi.org/10.1109/4235.996017

Module 6 currently uses a weighted objective because Module 5 already defines
energy, cost, and carbon weights and the downstream recommendation layer needs
one operating state. NSGA-II would be appropriate if a future interface lets
an operator choose among multiple Pareto-optimal states.

## Selected Objective

The objective uses the same relative priorities as Module 5:

| Component | Weight | Included values |
|---|---:|---|
| Energy | 0.35 | useful electrical demand, boiler-fuel energy, renewable curtailment |
| Cost | 0.35 | grid import, fuel, battery degradation, export revenue |
| Carbon | 0.30 | grid electricity and boiler-fuel emissions |

Each component is normalized against the corrected baseline so rupees, kWh,
and kg CO2e can be combined without one unit dominating solely because of its
numeric scale.

Renewable curtailment is explicitly represented because storage and flexible
dispatch can recover energy that export limits would otherwise waste. NREL
dispatch research similarly models battery charging, electricity prices,
forecast PV production, and battery wear together:
https://www.nrel.gov/docs/fy19osti/72513.pdf

## Constraint Strategy

Candidate states must satisfy:

- the required production load;
- compressor, HVAC, boiler, battery, and grid bounds;
- no simultaneous battery charging and discharging;
- minimum and maximum battery SOC;
- maximum grid import; and
- a physically auditable renewable/load/export/curtailment balance.

Constraints are handled twice: candidate repair keeps the GA search inside the
valid region, while validation and a large fitness penalty protect against any
remaining infeasible result.

## Recommendation Conversion

An optimization value is not useful to an operator by itself. The
Recommendation Engine compares each baseline and optimized setpoint and emits:

- equipment and action;
- current and recommended value;
- unit and percentage change;
- priority and reason;
- expected energy, cost, and carbon impact; and
- confirmation that constraints were respected.

Small changes below the configured tolerance are suppressed to prevent noisy
or non-actionable instructions. If no material setpoint changes, the engine
emits a validated maintain-state recommendation.

## Limitations and Future Work

- The current horizon is one hour; multi-period optimization should carry SOC
  and production requirements across time.
- Equipment efficiency curves should replace minimum/maximum approximations
  when real manufacturer or plant data becomes available.
- Tariff forecasts would allow economically meaningful battery discharge and
  grid-charging decisions.
- Uncertainty bands from forecasting could support robust or stochastic
  optimization.
- NSGA-II could expose a Pareto front instead of one weighted result.

