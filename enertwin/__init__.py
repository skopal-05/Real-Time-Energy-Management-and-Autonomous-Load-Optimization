"""EnerTwin integration layer.

This package is the *only* new code in the repository. It sits around the seven
existing modules and never modifies them:

    Module 1 - Data Acquisition
    Module 2 - Digital Twin
    Module 3 - Forecasting
    Module 4 - Multi-Agent Intelligence
    Module 5 - Scenario Simulation
    Module 6 - Optimization Engine
    Module 7 - Explainable AI & Performance Evaluation

Each module is treated as a black box that is executed exactly the way it was
designed to be executed: as a Python program whose working directory is its own
module folder. Adapters translate between a module's native interface and the
platform's integration interface; the API layer maps the resulting artifacts to
the shapes the existing frontend already expects.
"""

__version__ = "1.0.0"
