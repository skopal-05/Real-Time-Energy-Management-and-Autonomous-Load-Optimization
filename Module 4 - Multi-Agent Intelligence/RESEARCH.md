# Person 1 and Person 2 Research Notes

## Multi-agent design

The agents use a shared recommendation contract rather than directly mutating
plant state. This supports loose coupling: each specialist evaluates its own
constraints, while Person 3's future decision engine can compare priorities,
validate setpoints, resolve conflicts, and authorize actions. Deterministic rules
also make recommendations explainable and repeatable during testing.

## Person 1

### Cost optimization

Flexible production demand can be shifted from a high-tariff interval to a
lower-tariff interval. The agent limits the shifted amount to an explicitly
configured flexible fraction and never treats renewable-served demand as
avoidable grid cost.

### Production load balancing

The balancing strategy first protects each line's minimum operating allocation.
Remaining power is distributed according to priority weights without exceeding
requested or maximum power. When available power is below the combined minimum,
the same weights provide a deterministic shortage allocation.

### Energy scheduling

The scheduler applies an earliest-deadline-first ordering, then selects the
lowest-cost feasible slot. Renewable energy offsets grid energy in the slot cost.
Capacity and deadline checks are hard constraints, and infeasible jobs are
reported rather than silently dropped.

### Energy allocation

Renewable power is dispatched first because its marginal fuel cost and operational
emissions are normally lowest. Battery and grid energy are ordered by their
declared marginal costs. The battery can still be used after grid capacity is
exhausted to prevent an avoidable production shortfall.

## Person 2

### Renewable optimization

Plant demand is served using available solar first and dispatchable battery energy
second. A declared battery reserve is withheld from dispatch. The recommendation
reports renewable penetration and the residual grid requirement.

### Solar allocation

Solar dispatch follows the practical order: on-site consumption, battery
charging, permitted grid export, then curtailment. Battery headroom, charge power,
and export capacity are explicit constraints.

### Battery dispatch

The battery charges from renewable surplus when SOC headroom exists. It
discharges into a site deficit during high-price periods only above the reserve
SOC. Power limits and interval energy limits are both enforced, and the projected
SOC is included for validation.

### Grid management

Positive net demand is imported up to the connection limit. Negative net demand
is exported up to the export limit. Any remaining import deficit becomes an
unserved-load alert; any remaining surplus becomes curtailed export. Costs and
revenues are reported separately for auditability.

## Assumptions and handoff constraints

- Agents recommend actions; they do not directly control equipment.
- Input power is instantaneous average kW for the decision interval.
- The scheduler currently treats jobs as indivisible.
- Battery efficiency and degradation can be represented through the
  `battery_cost_inr_kwh` supplied to allocation; a future controller may add a
  richer degradation model.
- Person 3 remains responsible for cross-agent conflict resolution, communication,
  persistent outputs, and integration with Module 3 forecasting.
