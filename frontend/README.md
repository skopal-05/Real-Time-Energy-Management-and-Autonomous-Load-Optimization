# EnerTwin — Digital Twin Energy Control Centre

Frontend for **“Generative Digital Twin for Real-Time Energy Management and Autonomous Load
Optimization in Industrial Manufacturing Systems.”**

It is a single control-centre experience that makes the whole pipeline legible in one sitting:

```
Sensors / acquisition → Digital twins → Forecasting (Random Forest)
   → Decision agents (rule-based multi-agent) → Optimisation (Genetic Algorithm)
   → Anomaly detection (Isolation Forest) → Explainability (SHAP)
```

Every page is one stage of that chain, and the Introduction page at `/` explains the whole thing
before you open any of them.

---

## Quick start

```bash
npm install
npm run dev          # http://localhost:3000
```

```bash
npm run build        # production build
npm start            # serve the build
npm run typecheck    # tsc --noEmit
npm run lint         # eslint
```

Node 18.17+ (built and verified on Node 22).

---

## Honesty about data

**Nothing in this app pretends to be a measurement.** With no backend configured, every screen is
served by a deterministic simulation in `src/data`, and every payload is tagged
`origin: "simulated"`. That tag surfaces as:

- a **Demo data** badge in the top bar and on every page header,
- a dismissible **Demo mode** banner under the top bar,
- an extra warning on the Optimisation page, because cost and peak figures are the easiest numbers
  to mistake for real savings.

Where a value genuinely does not exist, the UI shows an empty state rather than inventing one —
for example, the Explainable AI page shows “No SHAP explainer for this selection” for model/asset
pairs that have no explainer fitted, and asset efficiency reads “N/A” for the grid connection,
where efficiency is undefined.

---

## Connecting the Python backend

Copy `.env.example` to `.env.local` and set:

```bash
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
# optional, enables streaming instead of polling
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/stream
```

That is the entire switch. No component imports `fetch` or the mock generators — everything goes
through `getDataSource()` in `src/services/index.ts`, which returns either the mock adapter or the
REST adapter.

### Endpoints the REST adapter expects

Each returns the matching interface from `src/lib/types.ts` as plain JSON. The envelope
(`origin`, `fetchedAt`) is added on the frontend, so the backend does not need to know about it.

| Method | Endpoint | Returns |
| --- | --- | --- |
| GET | `/system/status` | `SystemStatus` |
| GET | `/system/events` | `SystemEvent[]` |
| GET | `/assets` | `Asset[]` |
| GET | `/assets/{assetId}` | `Asset \| null` |
| GET | `/assets/{assetId}/sensors/{metricKey}?hours=` | `SensorReading[]` |
| GET | `/energy/window?hours=&step_minutes=` | `EnergyReading[]` |
| GET | `/energy/sources?hours=` | `EnergySourceShare[]` |
| GET | `/energy/flow` | `EnergyFlowSnapshot` |
| GET | `/forecast/site?horizon=` | `Forecast` |
| GET | `/forecast/asset/{assetId}?horizon=` | `Forecast` |
| GET | `/forecast/assets/summary?horizon=` | `AssetForecastSummary[]` |
| GET | `/agents` | `Agent[]` |
| GET | `/agents/objective` | `OperatingObjective` |
| GET | `/agents/recommendations` | `AIRecommendation[]` |
| GET | `/optimization/latest` | `OptimizationResult` |
| GET | `/anomalies` | `Anomaly[]` |
| GET | `/anomalies/scores?hours=` | `{ points: AnomalyScorePoint[]; threshold: number }` |
| GET | `/explain/models` | `ExplainableModel[]` |
| GET | `/explain?model_id=&asset_id=` | `Explanation \| null` |
| GET | `/reports?period=` | `PerformanceReport` |
| POST | `/auth/login` | `AuthSession` |
| POST | `/auth/register` | `AuthSession` |
| POST | `/auth/logout` | `204` |

Return `null` from `/explain` when no explainer exists for that pair — the UI renders an empty
state rather than fabricating attributions.

### Realtime

`subscribe()` in `src/services/realtime.ts` is transport-agnostic. Today it polls every
`NEXT_PUBLIC_POLL_INTERVAL_MS`; set `NEXT_PUBLIC_WS_URL` and it uses a WebSocket with automatic
reconnect instead. Call sites do not change. The top-bar play/pause button suspends it.

---

## Routes

| Route | What it is |
| --- | --- |
| `/` | **Introduction** — what the system is, the seven-module pipeline, project details. Landing page after sign-in, and where the EnerTwin logo returns to. |
| `/overview` | Command Centre — the live operational dashboard |
| `/twins`, `/twins/[assetId]` | Asset grid and per-twin detail |
| `/monitoring`, `/energy-flow` | Acquisition view and system map |
| `/forecasting`, `/decisions`, `/optimization`, `/anomalies`, `/explainability` | One page per AI module |
| `/reports` | Performance reporting |
| `/login`, `/signup` | Sign-in screens, outside the app shell |

## Authentication

`src/services/authService.ts` defines one `AuthService` interface with two adapters, chosen by the
same `NEXT_PUBLIC_API_MODE` switch as the data layer.

**Demo mode (default).** The sign-in screens are real UI on a demo adapter that verifies nothing,
creates no account and stores no password. It records a display name in `sessionStorage` so the
shell has something to show, flags the session `demo: true`, and both screens say so in an amber
notice. Do not present it as working authentication.

**Live mode.** With `NEXT_PUBLIC_API_MODE=live`, the HTTP adapter posts to `/auth/login`,
`/auth/register` and `/auth/logout` and expects an `AuthSession` back with `demo: false`.

The app is **not** gated by default — `/` opens straight into the dashboard so a demonstration never
stalls on a login screen. Set `NEXT_PUBLIC_REQUIRE_AUTH=true` to redirect unauthenticated visitors
to `/login`.

## Project structure

```
src/
  app/
    layout.tsx             html shell + Auth and AppState providers
    (app)/                 everything inside the control-centre shell
      layout.tsx           AppShell + optional auth gate
      page.tsx             Introduction — the story of the project
      overview/            Command Centre
      twins/               asset grid + [assetId] detail view
      monitoring/          real-time acquisition view
      forecasting/         Random Forest analytics
      decisions/           agent centre
      optimization/        Genetic Algorithm centre
      anomalies/           Isolation Forest alert centre
      explainability/      SHAP explanations
      energy-flow/         system map
      reports/             performance reporting
      error.tsx            route-level error boundary
    (auth)/                sign-in screens, no sidebar
      layout.tsx  login/  signup/
    not-found.tsx  globals.css
  components/
    layout/                AppShell, Sidebar, TopNavbar, PageHeader, DemoBanner, navigation
    ui/                    MetricCard, StatusBadge, Panel, Meter, DataTable, FilterBar,
                           DateRangeSelector, Segmented, Sparkline, InfoTip, States,
                           ResourceBoundary, DataOriginBadge
    charts/                TimeSeriesChart, ForecastChart, OptimizationComparison,
                           ConvergenceChart, FeatureImportanceChart, AnomalyScoreChart,
                           EnergyMixChart, CategoryBarChart, chartTheme, ChartTooltip
    assets/                AssetCard, AssetStatusGrid, assetIcon
    ai/                    RecommendationCard, AIExplanationCard, PipelineStrip
    alerts/                AlertTable
    energy/                EnergyFlow (SVG system map)
    overview/              SystemSummary, EventFeed, PipelineExplainer
    auth/                  Field, DemoAuthNotice, SubmitButton
  data/                    demo scenario — the ONLY place mock data lives
    scenario.ts            physical model: load profiles, PV, battery dispatch, tariff
    mock*.ts               per-module builders
  services/                DataSource + AuthService interfaces, mock/REST adapters, realtime, config
  hooks/                   useResource (loading/error/refresh), useNow
  providers/               AppStateProvider (stream control), AuthProvider (session)
  lib/                     types.ts, constants.ts, format.ts, utils.ts
```

**Rules the codebase follows:**

- Components never import from `src/data` — only from `src/services`.
- All formatting lives in `src/lib/format.ts` and is null-safe: a missing value renders `—`,
  never `NaN` or `null`.
- Status colours come from `HEALTH_STYLES` / `SEVERITY_STYLES` in `src/lib/constants.ts`, so
  “warning amber” means the same thing on every screen.
- Chart styling comes from `chartTheme.ts`; charts render an empty state instead of throwing when
  a series is missing.
- `ResourceBoundary` handles loading / error / empty for every panel, so those states are
  implemented once.

---

## Design system

| Token group | Where |
| --- | --- |
| Surfaces, lines, text, status, chart accents | `tailwind.config.ts` |
| Panel / eyebrow / grid-backdrop classes | `src/app/globals.css` |
| Status colour mapping | `src/lib/constants.ts` |

Dark, neutral, low-chroma; accent colour is used only for state and data. Radii, spacing and type
scale are fixed by the token set. Numeric readouts use tabular figures so values don’t jitter as
they update. `prefers-reduced-motion` disables all animation.

---

## Demo mode

The demo scenario advances on the same tick that drives data refresh (5 s by default), so during a
viva the load profile, PV output, battery state, grid position and asset metrics all move
realistically. Pause it from the top bar when you want to talk over a static screen, and hit
refresh to step it manually.

The scenario is deterministic — it is generated from a seeded PRNG anchored to the wall clock, so
the same instant always produces the same numbers, and server and client renders agree.

Scenario shape: two production lines on shift patterns, a boiler and compressor that cycle, HVAC
driven by ambient temperature, a 350 kW rooftop PV array, a 600 kWh battery dispatched against a
three-band tariff, and a 1050 kW contracted maximum demand that the baseline schedule breaches and
the optimiser brings back inside.
