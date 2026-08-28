# Integration architecture

How seven independently developed modules became one running product without a
single line of any module changing.

---

## 1. The constraint that shaped everything

Modules 1–7 are frozen. They had already been built and tested, so the
integration work had to happen *around* them:

```
Existing module  →  Adapter  →  Integration interface  →  Backend  →  Frontend
```

Every design decision below follows from that. Where a module's interface did
not match what the platform needed, the answer was always an adapter outside the
module, never an edit inside it.

This is enforced, not just intended. `tests/test_modules_unmodified.py` fails if
any tracked file inside a module folder differs from `HEAD`, with one exception:
each module's own `outputs/` folder, which the module itself rewrites whenever it
runs.

---

## 2. Layout

```
enertwin/                     the integration layer - the only new Python
  config.py                   where every module and artifact lives
  runner.py                   executes a module in its own working directory
  adapters/
    base.py                   the run(context) -> StageResult interface
    boundary.py               data translations between modules
    pipeline_adapters.py      one adapter per module, in execution order
    drivers/                  scripts that run *inside* a module's folder
      m2_sync.py
      m3_forecast.py
      m4_agents.py
      m5_scenarios.py
  orchestration/
    pipeline.py               runs the seven stages in order
    snapshot.py               the artifacts of one run, in memory
    store.py                  the current snapshot; background runs
  api/
    app.py                    FastAPI; the frontend's REST contract
    catalog.py                plant asset metadata
    mappers/                  module artifacts -> frontend types

tests/                        contract tests and the immutability guard
deploy/                       Dockerfiles and compose
frontend/                     the existing Next.js control centre, unchanged
```

---

## 3. Why modules run as subprocesses

The modules cannot be imported side by side. Several of them ship top-level
packages with the *same name and different contents*:

| Name         | Appears in                              |
|--------------|------------------------------------------|
| `common`     | Module 2 and Module 3, unrelated code     |
| `integration`| Modules 2, 3, 4, 5, 6, 7                  |
| `contracts`  | Modules 4, 5 and 6, three different files |
| `tests`      | Modules 2, 4, 5, 6, 7                     |

Importing them into one interpreter would need packages renamed inside the
modules — exactly what is forbidden. Instead `enertwin/runner.py` runs each
module as a subprocess with:

- the module's folder as the working directory,
- the module's folder first on `PYTHONPATH`,
- the project root second, so drivers can `import enertwin`.

That reproduces the environment each module was developed in, exactly. It also
means a module crash cannot take the API down, and a module can be swapped or
upgraded without touching the platform.

The cost is process start-up per stage. It does not matter: the API never runs
the pipeline inside a request. Requests are served from the last completed run's
snapshot, held in memory.

---

## 4. How each module is invoked

| Module | Invoked via | Why |
|---|---|---|
| 1 · Data Acquisition | its own `main.py` | Skipped by default — its outputs are version-controlled inputs for everything downstream. Enable with `ENERTWIN_REGENERATE_DATA=1`. |
| 2 · Digital Twin | driver `m2_sync.py` | `run_realtime.py` loops forever; a request-driven backend cannot call it. The driver performs a bounded number of the same `sync_once()` rounds. |
| 3 · Forecasting | driver `m3_forecast.py` | `run_forecasting.py` forecasts from a hard-coded example state, not live twin state. |
| 4 · Multi-Agent | driver `m4_agents.py` | Module 4 ships no `__main__`; the driver follows the sequence its own `integration_test.py` documents. |
| 5 · Scenario Simulation | driver `m5_scenarios.py` | Needs the Module 3 boundary translation (§5) before the module's own `ScenarioController.run()`. |
| 6 · Optimization | its own `integration/optimization_controller.py` | Already resolves Modules 4 and 5 outputs from default paths. No driver needed. |
| 7 · Explainability | its own `run_person_1_2.py`, then `integration/final_controller.py` | Both resolve their inputs from default paths. No driver needed. |

Drivers use only each module's public classes. They write the module's own
artifacts to the module's own paths, in the module's own format, so the
file-based hand-off between Modules 3→4→5→6→7 keeps working through each
module's existing default paths.

---

## 5. What integration revealed

Running the seven modules against each other for the first time surfaced three
real incompatibilities. All three are handled outside the modules, and all three
are reported through `GET /api/pipeline/translations` rather than being fixed
silently.

### 5.1 Module 1's raw dataset violates Module 2's operating ranges

Module 2's `SystemSync` reads Module 1's **raw** `outputs/` folder. Measured
against the twins' own declared ranges, that dataset does not satisfy them:

- **9,059 of 10,000** rows in raw `grid.csv` carry a `grid_export_kw` above the
  grid twin's declared 10,000 kW limit, peaking at **400,003 kW**.
- One production row exceeds the line twin's `units_per_hour` limit.

The grid twin correctly raises on the sixth row, so `run_realtime.py` halts
almost immediately against this data.

Module 1's **cleaned** output — the validated product of its own
validate → clean → feature-engineer pipeline — satisfies every twin's range for
every row of every asset (verified: 96/96 rows × 8 assets, zero rejections).

**Resolution.** The Module 2 driver composes the module's own twin classes and
`CSVLoader` in exactly the order `SystemSync.sync_once()` does, pointed at the
cleaned dataset. `SystemSync` is untouched and still reachable with
`--source raw`, which reports rejections as data-quality events instead of
crashing.

### 5.2 Modules 3, 4 and 5 disagree on what "renewable generation" means

Module 3's `LoadForecast.renewable_generation()` returns *solar + battery power*.
Module 1 signs battery power positive while charging, so whenever the battery
charges, Module 3 emits a **negative** `energy_forecast.renewable_generation_kw`.

Both downstream consumers reject that:

- Module 4's `CostOptimizationAgent` and `EnergyAllocator` require the value to
  be ≥ 0 and return an `agent_execution_error` recommendation instead of a
  decision — **2 of 12 agents go dark**.
- Module 5's `IntegrationValidator` requires the same and rejects the whole
  forecast, **halting the chain**.

Module 5 states the definition it means. Its `ScenarioGenerator` reads renewable
generation from `future_state.inverter_power_kw` and comments: *"Battery power is
simulated separately and therefore must not be counted as renewable
generation."* The disputed field is never read by any Module 5 calculation — only
by the validator.

**Resolution.** `enertwin/adapters/boundary.py` gives Modules 4 and 5 a
translated *view* carrying the solar-only figure — Module 3's own
`inverter_power_kw`. Nothing is invented, and Module 3's artifact on disk stays
byte-for-byte as Module 3 wrote it. With the translation in place all twelve
agents return real decisions.

### 5.3 Module 3's flat state dictionary cross-wires shared sensor names

`FutureStateGenerator.generate()` hands one flat dictionary to all seven models.
That works for the hand-written example in `run_forecasting.py`, but real
per-asset telemetry cannot be flattened: `motor_temperature_c` belongs to both a
production line and the compressor, `efficiency_percent` to the boiler,
compressor and HVAC, `voltage_v` to both the battery and the grid. Flattening
would feed one asset's reading to another asset's model.

**Resolution.** The Module 3 driver calls the same public per-asset methods
`generate()` calls — `production_forecast()`, `boiler_forecast()`, and so on —
once per asset, each with that asset's own twin state. The merged result is
identical in shape to `generate()`'s, because every model's `postprocess` emits a
single uniquely-named key.

---

## 6. The one approved module change

Module 6's genetic algorithm records best-fitness per generation in
`GeneticAlgorithmResult.history` and returns it. `Optimizer.optimize()` read
`generations` and `evaluations` off that same object but not `history`, so the
series was computed, returned and discarded before reaching
`optimization_report.json` — leaving the convergence chart with no data.

**Approved by the project owner on 2026-08-28.** One line added to the
`algorithm` dictionary in `optimization/optimizer.py`:

```python
"history": list(ga_result.history),
```

Purely additive: no algorithm, calculation or existing output value changes.
Before making it, every consumer was checked — Module 6's
`OptimizationValidator` does not inspect this dictionary,
`recommendation_engine.py` passes it through verbatim, Module 6's own
`integration_test.py` reads only the `best_fitness` and `evaluations` keys, and
Module 7 never reads it.

This is the **only** approved change to any module. It is recorded in
`APPROVED_MODULE_CHANGES` in `tests/test_modules_unmodified.py` with its
reasoning, and a test asserts the list has exactly one entry — so a second
change cannot be added without that tripwire firing. Every other module file is
protected exactly as before.

The chart now plots Module 6's real search trajectory: 80 generations,
1.0 → 0.9665, monotonically improving.

**Still absent, deliberately.** The GA records only the *best* fitness per
generation, never the population mean. `meanFitness` is `null` on every point,
so the chart draws the best line and leaves the mean line absent rather than the
platform inventing a second series. Recording the mean would mean changing the
GA itself, which has not been requested or approved.
`tests/test_api_contract.py` pins both properties.

---

## 7. Connecting the frontend

The frontend was written against a backend that did not exist yet:
`src/services/httpDataSource.ts` already declared every endpoint path, and
`src/lib/types.ts` every payload shape. The backend was built to that contract,
so connecting the real system required **no frontend code change** — only
`frontend/.env.local`:

```
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_BASE_URL=http://localhost:8010/api
```

`tests/test_api_contract.py` verifies all 20 endpoints against those shapes. If
one breaks, a screen breaks, and the test says which.

### Endpoints

| Path | Serves | Source |
|---|---|---|
| `/api/system/status`, `/system/events` | health, pipeline strip, event feed | all stages |
| `/api/assets`, `/assets/{id}`, `/assets/{id}/sensors/{metric}` | twin state and history | Module 2 |
| `/api/energy/window`, `/energy/sources`, `/energy/flow` | energy series and topology | Module 2 |
| `/api/forecast/site`, `/forecast/asset/{id}`, `/forecast/assets/summary` | forecasts and accuracy | Modules 3 + 7 |
| `/api/agents`, `/agents/objective`, `/agents/recommendations` | decisions | Modules 4 + 5 + 6 |
| `/api/optimization/latest` | GA result | Module 6 |
| `/api/anomalies`, `/anomalies/scores` | Isolation Forest | Module 7 |
| `/api/explain/models`, `/explain`, `/explain/importance` | SHAP | Module 7 |
| `/api/models/lifecycle`, `/models/evaluation` | drift, retraining, chain evaluation | Module 7 |
| `/api/reports` | aggregated performance | Modules 2 + 6 + 7 |
| `/api/pipeline/status`, `/pipeline/run`, `/pipeline/translations` | platform control | — |
| `/api/auth/login`, `/register`, `/logout` | demo sessions | — |

---

## 8. Rules the mappers follow

**Never invent a number.** Where a module produced no value, the API returns
`null` and the UI renders the "unavailable" state it already has for every
nullable field. Concretely:

- Forecast `lowerKw`/`upperKw` and peak `confidence` are `null` — Module 3's
  models expose no predictive distribution.
- `convergence` is empty — see §6.
- `meanTimeToResolveMinutes` is `null` — nothing in the chain resolves anomalies.
- Efficiency is `null` for assets with no measured efficiency signal.
- Agent `ruleCount` is 0 for the twelve agents, which encode their logic
  directly; only the rule engine has an explicit rule set, and it reports its
  real count of 4.

**Prefer the module that owns the measurement.** Forecast accuracy comes from
Module 7's held-out evaluation where it produced one, not from the platform's own
replay of the models over data they were trained on.

**Say when attribution was inferred.** Module 7 scores anomalies over the two
production lines' data concatenated, and its records carry a row index rather
than an asset or a timestamp. The mapper matches each record's feature values
back against the synchronized twin history to recover which line and when. A
record that matches nothing is marked `origin: "simulated"` rather than being
asserted.

---

## 8a. Module 7's model-lifecycle layer

Module 7 does more than explain and score. On every run it also monitors each
Random Forest for drift, trains a candidate replacement wherever a retraining
trigger fires, compares the candidate against the incumbent, and records whether
it was promoted. That work was running every cycle with nowhere to go — the
artifacts were written and nothing read them.

It is now surfaced three ways:

- `GET /api/models/lifecycle` — per-model trigger, status, promotion decision,
  RMSE delta, and both metric sets
- `GET /api/models/evaluation` — Module 7's end-to-end assessment of the
  Modules 3–7 chain, plus any joblib/scikit-learn compatibility warnings
- The operator **event feed** and the Module 7 **pipeline stage detail**, so it
  is visible in the existing UI without a new screen

A typical run: 6 of 7 models trigger retraining, every candidate is rejected,
nothing is promoted. Module 7's own safety policy is carried through verbatim —
*"candidate models are never promoted without an explicit promotion_path"* — and
because no promotion path is configured, no candidate could replace a model in
service even if it won. Tests assert the platform never reports a promotion
Module 7 did not make.

### A cross-platform caveat

Module 7's *candidate fit* is not bit-identical across operating systems. With
the same scikit-learn 1.9.0 and numpy 2.5.2, a boiler candidate scored RMSE
4.02872448 on macOS/arm64 and 4.0274937 on linux/arm64 — a ~0.03% difference from
floating-point behaviour in the platform builds. The incumbent's metrics are
identical on both, since those come from loading a fixed model.

The **decisions are stable**: both platforms trigger the same 6 models, reject
every candidate and promote nothing, because Module 7's acceptance threshold is
1% and the platform differences are two orders of magnitude smaller. Worth
knowing if you ever compare retraining numbers between a developer machine and a
deployed container — the *outcome* is reproducible, the fourth decimal place is
not.

---

## 9. Two properties of the data worth knowing

**The dataset is not energy-balanced.** Module 1 generates each asset's telemetry
independently, so metered grid import does not equal metered demand minus
generation — over 24 hours, import is roughly 9.1 MWh against 4.6 MWh of metered
demand. The platform reports measured values as measured and does not force a
balance.

**Site demand and Module 3's load forecast are different quantities.** Metered
site demand includes both production lines, the compressor and HVAC. Module 3's
`LoadForecast.calculate_total_load()` is compressor + HVAC only, because Module 3
forecasts production as throughput in units/hour and does not convert it to kW —
a limitation Module 5 also documents in its scenario assumptions. The forecast
screen labels its target accordingly, and the optimisation schedule chart plots
only Module 6's own quantities rather than mixing the two.

---

## 10. Running it

```bash
make setup      # virtual environment, Python and npm dependencies
make check      # verify modules, packages, models and data
make run        # run Modules 1-7 once, printing each stage
make serve      # API on :8010
make ui         # control centre on :3010
make test       # 67 tests, including the immutability guard
```

Or with Docker — UI on `:3000`, API on `:8000`:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

A full pipeline pass takes about 20 seconds, dominated by Module 3 loading seven
Random Forest models and Module 7 refitting its explainers. The API container
runs one pass at start-up and reports unhealthy until it completes, so the
frontend waits on `service_healthy` before starting.

Both images have been built and the stack verified end to end on
linux/arm64: all seven modules produce identical results inside the container to
the host, and the containerised UI renders live data from the containerised API.

Three things worth knowing if you change the Dockerfiles:

- The frontend has **no `public/` directory**; a `COPY` for one fails the build.
- `enertwin_data/` must exist in the image *before* the ownership change. A
  named volume mounted over a path absent from the image is initialised
  root-owned, and the unprivileged runtime user then cannot write run history.
- The runner stage's `COPY` needs `--chown`. `COPY` preserves the source mode,
  and `frontend/package.json` is mode 0600 in this repository, so without it the
  runtime user cannot read it and the container crash-loops.
