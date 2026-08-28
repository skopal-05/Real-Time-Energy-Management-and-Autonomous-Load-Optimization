"use client";

import { useCallback } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Activity,
  BatteryCharging,
  Gauge,
  HeartPulse,
  Leaf,
  ShieldAlert,
  Sun,
  TrendingUp,
} from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { CHART_COLORS } from "@/lib/constants";
import { formatKw, formatKwh, formatPct, pctChange } from "@/lib/format";
import type {
  AIRecommendation,
  Asset,
  EnergyReading,
  EnergySourceShare,
  Forecast,
  SystemEvent,
  SystemStatus,
} from "@/lib/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { EnergyMixChart } from "@/components/charts/EnergyMixChart";
import { AssetStatusGrid } from "@/components/assets/AssetStatusGrid";
import { PipelineStrip } from "@/components/ai/PipelineStrip";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { SystemSummary } from "@/components/overview/SystemSummary";
import { EventFeed } from "@/components/overview/EventFeed";

export default function OverviewPage() {
  const ds = getDataSource();
  const now = useNow();

  const status = useResource<SystemStatus>(useCallback(() => ds.getSystemStatus(), [ds]));
  const assets = useResource<Asset[]>(useCallback(() => ds.getAssets(), [ds]));
  const energy = useResource<EnergyReading[]>(useCallback(() => ds.getEnergyWindow(12, 15), [ds]));
  const shares = useResource<EnergySourceShare[]>(useCallback(() => ds.getSourceShares(24), [ds]));
  const forecast = useResource<Forecast>(useCallback(() => ds.getForecast("6h"), [ds]));
  const recs = useResource<AIRecommendation[]>(useCallback(() => ds.getRecommendations(), [ds]));
  const events = useResource<SystemEvent[]>(useCallback(() => ds.getEvents(), [ds]));

  const s = status.data;
  const forecastDelta = s ? pctChange(s.consumptionKw, s.forecastNextHourKw) : null;
  const totalKwh = (shares.data ?? []).reduce((a, x) => a + x.energyKwh, 0);

  return (
    <>
      <PageHeader
        title="Command Centre"
        description="Live state of the plant and of every stage of the digital-twin pipeline — acquisition, twin state, forecasting, agent decisions, optimisation, anomaly detection and explainability."
        origin={status.origin}
        actions={
          <>
            <Link
              href="/energy-flow"
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface-inset px-3 py-1.5 text-xs font-medium text-content-muted transition-colors hover:border-line-strong hover:text-content"
            >
              Energy flow map
              <ArrowRight className="h-3 w-3" aria-hidden />
            </Link>
            <Link
              href="/twins"
              className="inline-flex items-center gap-1.5 rounded-lg border border-info/30 bg-info/10 px-3 py-1.5 text-xs font-medium text-info transition-colors hover:bg-info/15"
            >
              Open digital twins
              <ArrowRight className="h-3 w-3" aria-hidden />
            </Link>
          </>
        }
      />

      {/* KPI row */}
      <ResourceBoundary resource={status} loading={<LoadingState variant="cards" rows={6} />}>
        {(data) => (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <MetricCard
              label="System health"
              value={formatPct(data.healthScorePct, 0)}
              tone={data.overall === "healthy" ? "ok" : data.overall === "critical" ? "crit" : "warn"}
              icon={<HeartPulse className="h-4 w-4" />}
              caption={`${data.twinsOnline} of ${data.twinsTotal} twins reporting`}
              footer={<StatusBadge status={data.overall} />}
              hint="Composite score derived from twin status and open anomalies. 100 % means every twin is nominal with no active detections."
            />
            <MetricCard
              label="Current load"
              value={formatKw(data.consumptionKw, 0)}
              tone="info"
              icon={<Gauge className="h-4 w-4" />}
              caption="Total site demand across all consumers"
              sparkline={(energy.data ?? []).map((e) => e.consumptionKw)}
              sparklineColor={CHART_COLORS.load}
            />
            <MetricCard
              label="On-site generation"
              value={formatKw(data.generationKw, 0)}
              tone="ok"
              icon={<Sun className="h-4 w-4" />}
              caption="Rooftop PV output"
              sparkline={(energy.data ?? []).map((e) => e.generationKw)}
              sparklineColor={CHART_COLORS.generation}
            />
            <MetricCard
              label="Renewable share"
              value={formatPct(data.renewableSharePct, 0)}
              tone={data.renewableSharePct > 40 ? "ok" : "neutral"}
              icon={<Leaf className="h-4 w-4" />}
              caption={`${formatKwh(totalKwh)} delivered in the last 24 h`}
              hint="Share of the current demand being met by on-site renewable generation."
            />
            <MetricCard
              label="Forecast · next hour"
              value={formatKw(data.forecastNextHourKw, 0)}
              tone="neutral"
              icon={<TrendingUp className="h-4 w-4" />}
              caption="Random Forest site-load prediction"
              delta={
                forecastDelta === null
                  ? undefined
                  : {
                      value: `${Math.abs(forecastDelta).toFixed(1)} %`,
                      trend: forecastDelta > 1 ? "up" : forecastDelta < -1 ? "down" : "flat",
                      positiveIsGood: false,
                    }
              }
            />
            <MetricCard
              label="Active anomalies"
              value={String(data.activeAnomalies)}
              tone={data.activeAnomalies > 0 ? "warn" : "ok"}
              icon={<ShieldAlert className="h-4 w-4" />}
              caption="Flagged by Isolation Forest, awaiting review"
              footer={
                <Link href="/anomalies" className="text-2xs font-medium text-info hover:underline">
                  Open anomaly centre →
                </Link>
              }
            />
          </div>
        )}
      </ResourceBoundary>

      {/* Pipeline story */}
      <Panel className="mt-3">
        <PanelHeader
          title="AI & Digital Twin pipeline"
          subtitle="Sensor data flows left to right; every stage links to the page that shows its output."
          eyebrow="System architecture"
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={status} loading={<LoadingState className="h-24" />}>
            {(data) => <PipelineStrip stages={data.pipelineStages} />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      {/* Twin status */}
      <Panel className="mt-3">
        <PanelHeader
          title="Digital Twin system status"
          subtitle="Every modelled asset, its live power and its health state."
          eyebrow="Module 2 · Digital twin"
          actions={
            <Link href="/twins" className="text-2xs font-medium text-info hover:underline">
              All twins →
            </Link>
          }
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={assets} loading={<LoadingState className="h-24" />}>
            {(data) => <AssetStatusGrid assets={data} />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      {/* Summary strip */}
      <ResourceBoundary resource={status} loading={<LoadingState className="mt-3 h-20" />}>
        {(data) => (
          <div className="mt-3">
            <SystemSummary status={data} />
          </div>
        )}
      </ResourceBoundary>

      {/* Charts */}
      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Consumption vs generation"
            subtitle="Last 12 hours at 15-minute resolution."
            eyebrow="Energy balance"
            actions={
              <Link href="/monitoring" className="text-2xs font-medium text-info hover:underline">
                Live monitoring →
              </Link>
            }
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={energy} loading={<LoadingState className="h-[260px]" />}>
              {(data) => (
                <TimeSeriesChart
                  data={data}
                  series={[
                    { key: "consumptionKw", label: "Site demand", color: CHART_COLORS.load },
                    { key: "generationKw", label: "PV generation", color: CHART_COLORS.generation },
                    { key: "gridKw", label: "Grid import", color: CHART_COLORS.grid, type: "line", dashed: true },
                  ]}
                  yLabel="kW"
                  height={264}
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader
            title="Energy source distribution"
            subtitle="Where the last 24 hours of demand was served from."
            eyebrow="Supply mix"
          />
          <PanelBody className="pt-4">
            <ResourceBoundary resource={shares} loading={<LoadingState className="h-[220px]" />}>
              {(data) => (
                <EnergyMixChart
                  shares={data}
                  centerValue={formatKwh(totalKwh)}
                  centerLabel="24 h served"
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>

      {/* Forecast + recommendations */}
      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Load forecast"
            subtitle="Measured load against the Random Forest prediction, with its 95 % interval."
            eyebrow="Module 3 · Forecasting"
            hint="A Random Forest regressor is trained on lagged load, production setpoints, ambient conditions and calendar features. Shaded region shows the prediction interval."
            actions={
              <Link href="/forecasting" className="text-2xs font-medium text-info hover:underline">
                Forecast analytics →
              </Link>
            }
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={forecast} loading={<LoadingState className="h-[280px]" />}>
              {(data) => (
                <ForecastChart
                  points={data.series}
                  nowMs={now || new Date(data.generatedAt).getTime()}
                  peakAt={data.peak?.expectedAt ?? null}
                  height={280}
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel className="flex flex-col">
          <PanelHeader
            title="AI recommendations"
            subtitle="Latest proposals from the rule-based agent layer."
            eyebrow="Module 4 · Decisions"
            actions={
              <Link href="/decisions" className="text-2xs font-medium text-info hover:underline">
                Agent centre →
              </Link>
            }
          />
          <PanelBody className="flex-1 space-y-2 pt-3">
            <ResourceBoundary resource={recs} loading={<LoadingState variant="rows" rows={3} />}>
              {(data) =>
                data
                  .slice(0, 3)
                  .map((r) => <RecommendationCard key={r.id} recommendation={r} now={now} compact />)
              }
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>

      {/* Events + battery/quick facts */}
      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Recent events & alerts"
            subtitle="Everything the platform detected or acted on, newest first."
            eyebrow="Activity log"
          />
          <ResourceBoundary resource={events} loading={<LoadingState variant="rows" rows={5} />}>
            {(data) => <EventFeed events={data} now={now} />}
          </ResourceBoundary>
        </Panel>

        <Panel>
          <PanelHeader title="Storage & supply" subtitle="Current battery and grid position." eyebrow="Now" />
          <PanelBody className="space-y-3 pt-3">
            <ResourceBoundary resource={energy} loading={<LoadingState className="h-40" />}>
              {(data) => {
                const last = data[data.length - 1];
                if (!last) return null;
                const charging = last.batteryKw < 0;
                return (
                  <>
                    <div className="flex items-center justify-between rounded-lg border border-line bg-surface-inset p-3">
                      <div className="flex items-center gap-2.5">
                        <BatteryCharging className="h-4 w-4 text-accent-battery" aria-hidden />
                        <div>
                          <p className="text-2xs uppercase tracking-wider text-content-faint">Battery</p>
                          <p className="text-sm font-semibold text-content">
                            {charging ? "Charging" : last.batteryKw > 1 ? "Discharging" : "Idle"}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold tabular text-content">
                          {formatPct(last.batterySocPct, 0)}
                        </p>
                        <p className="text-2xs tabular text-content-faint">
                          {formatKw(Math.abs(last.batteryKw), 0)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-line bg-surface-inset p-3">
                      <div className="flex items-center gap-2.5">
                        <Activity className="h-4 w-4 text-accent-grid" aria-hidden />
                        <div>
                          <p className="text-2xs uppercase tracking-wider text-content-faint">Grid</p>
                          <p className="text-sm font-semibold text-content">
                            {last.gridKw >= 0 ? "Importing" : "Exporting"}
                          </p>
                        </div>
                      </div>
                      <p className="text-lg font-semibold tabular text-content">
                        {formatKw(Math.abs(last.gridKw), 0)}
                      </p>
                    </div>

                    <p className="text-2xs leading-relaxed text-content-faint">
                      Battery dispatch and grid position are set by the storage and cost agents against the
                      current tariff band. Open the energy-flow map to see the full topology.
                    </p>
                    <Link
                      href="/energy-flow"
                      className="inline-flex items-center gap-1.5 text-2xs font-medium text-info hover:underline"
                    >
                      Open energy flow map
                      <ArrowRight className="h-3 w-3" aria-hidden />
                    </Link>
                  </>
                );
              }}
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>
    </>
  );
}
