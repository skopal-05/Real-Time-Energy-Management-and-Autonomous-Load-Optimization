# Week 5 Research Notes

## Generative scenario simulation

A scenario simulator is a what-if layer between forecasting and control. A forecast supplies the expected future operating point, while agent recommendations supply candidate setpoints. The simulator changes selected assumptions, evaluates the resulting operating states, and retains the original forecast as a comparison baseline. It does not execute equipment commands.

The implementation uses five deterministic scenarios: forecast baseline, agent optimized, renewable priority, cost saver, and renewable shortfall resilience. Deterministic templates were chosen so a weekly review can reproduce and explain every result. Additional templates can be added without changing the simulators.

## Energy model

For a horizon of `h` hours:

    useful demand = production + compressor + HVAC
    site consumption = useful demand + battery charging
    grid import = max(0, site consumption - renewable - battery discharge)
    surplus = max(0, renewable + battery discharge - site consumption)
    grid export = min(export limit, surplus)
    curtailment = surplus - grid export

Boiler fuel is tracked separately in cubic metres. The model assumes input kW values remain constant during the selected horizon.

## Cost and carbon comparison

Net operating cost includes purchased electricity, boiler fuel, and battery throughput cost, less export revenue. Carbon impact includes grid-import emissions and direct boiler-fuel emissions. Exported renewable energy is reported but does not receive a carbon credit, avoiding unsupported claims about the displaced grid source.

Default factors are transparent configuration values rather than hidden constants:

- Grid purchase: INR 8/kWh
- Grid export: INR 4/kWh
- Natural gas: INR 48/m3
- Battery degradation: INR 1.5/kWh throughput
- Grid emissions: 0.716 kg CO2e/kWh
- Natural gas emissions: 2.0 kg CO2e/m3

These are demonstration assumptions and should be replaced with the plant's contracted tariffs and approved emissions inventory factors before operational use.

## Multi-objective ranking

Useful plant electrical load, net cost, and emissions are each min-max normalized to a 0-100 benefit score, where 100 is the best observed scenario. Battery charging is reported in total site consumption but is not treated as an efficiency loss because that energy remains stored for later use. The overall score is:

    score = 0.35 energy + 0.35 cost + 0.30 carbon

The weights are configurable and normalized automatically. Ranking only compares the generated candidate set, so the score is relative rather than a universal measure of performance.

## Limitations

- The simulation is a one-interval steady-state model, not a transient physics model.
- Battery efficiency, state-of-charge evolution, equipment ramp limits, and production quality are outside the Week 5 scope.
- A scenario selected here must still pass safety and optimization constraints before Module 6 can act on it.
