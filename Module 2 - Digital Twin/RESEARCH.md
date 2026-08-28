# Week 2 Research Notes - Persons 1 and 2

## Person 1

### Industrial digital twin concepts

An industrial digital twin is a continuously updated software representation of a physical asset. This implementation separates state validation, telemetry synchronization, behaviour learning, and scenario simulation. The separation makes sensor errors easier to isolate and simulated results easier to audit.

### Production-line behaviour modelling

The production twins relate machine load, motor temperature, and vibration to units produced per hour. Their scenario results include throughput, hourly energy, and specific energy consumption. Range validation prevents physically unrealistic temperature, vibration, load, or throughput readings from entering the learned model.

### Boiler state synchronization

The boiler twin synchronizes pressure, steam flow, fuel flow, feedwater temperature, flue-gas temperature, and efficiency as one timestamped state. Its simulations report predicted efficiency, steam-to-fuel ratio, and thermal loss. Atomic updates prevent measurements from different timestamps being combined into a misleading state.

## Person 2

### Renewable-energy digital twin

The solar twin relates irradiance, panel temperature, and DC power to inverter output. Its scenarios report inverter power, conversion efficiency, and energy for a 15-minute interval.

### Battery state modelling

The battery twin represents state of charge, signed power, voltage, current, temperature, and operating mode. The Week 1 convention uses positive power for charging and negative power for discharging. Scenario calculations use a documented 500 kWh nominal capacity and constrain state of charge to 0-100%.

### Grid synchronization

The grid twin synchronizes imports, exports, frequency, voltage, power factor, and tariff. It calculates net power and 15-minute import cost and flags whether frequency is inside the 49.5-50.5 Hz stability band.

## Learning approach

The prototype uses a dependency-free online linear learner. Every synchronized observation updates the behaviour model. Scenario predictions remain anchored to the latest measured target and use the learned model to estimate changes caused by overridden inputs.
