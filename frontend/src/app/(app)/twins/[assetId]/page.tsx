"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Boxes, Gauge, Percent, Zap } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { ASSET_REGISTRY } from "@/lib/constants";
import type {
  AIRecommendation,
  Anomaly,
  Asset,
  AssetId,
  ExplainableModel,
  Explanation,
  Forecast,
  SensorReading,
} from "@/lib/types";
import { formatKw, formatNumber, formatPct, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { EmptyState, LoadingState } from "@/components/ui/States";
import { StatusBadge, Chip } from "@/components/ui/StatusBadge";
import { Segmented } from "@/components/ui/Segmented";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { AlertTable } from "@/components/alerts/AlertTable";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { assetAccent, assetIcon } from "@/components/assets/assetIcon";

const HISTORY_HOURS = 12;

function MetricTile({ metric }: { metric: Asset["metrics"][number] }) {
  const outOfRange =
    metric.value !== null &&
    ((metric.warnAbove !== undefined && metric.value > metric.warnAbove) ||
      (metric.warnBelow !== undefined && metric.value < metric.warnBelow));

  const pct =
    metric.value !== null && metric.min !== undefined && metric.max !== undefined
      ? ((metric.value - metric.min) / (metric.max - metric.min)) * 100
      : null;

  return (
    <div
      className={cn(
        "rounded-lg border bg-surface-inset p-3",
        outOfRange ? "border-warn/40" : "border-line",
      )}
    >
      <p className="label-eyebrow truncate">{metric.label}</p>
      <p className="mt-1 flex items-baseline gap-1">
        <span
          className={cn(
            "text-lg font-semibold tabular leading-none",
            outOfRange ? "text-warn" : "text-content",
          )}
        >
          {metric.value === null ? "—" : formatNumber(metric.value, metric.unit === "" ? 3 : 1)}
        </span>
        {metric.unit ? <span className="text-2xs text-content-muted">{metric.unit}</span> : null}
      </p>
      {pct !== null ? (
        <Meter value={pct} tone={outOfRange ? "warn" : "info"} className="mt-2" />
      ) : (
        <p className="mt-2 text-2xs text-content-faint">
          {metric.warnAbove !== undefined
            ? `Alarm above ${metric.warnAbove} ${metric.unit}`
            : metric.warnBelow !== undefined
              ? `Alarm below ${metric.warnBelow} ${metric.unit}`
              : "No configured limits"}
        </p>
      )}
    </div>
  );
}

export default function AssetDetailPage() {
  const params = useParams<{ assetId: string }>();
  const rawId = params?.assetId ?? "";
  const isKnown = rawId in ASSET_REGISTRY;
  const assetId = rawId as AssetId;

  const ds = getDataSource();
  const now = useNow();
  const [metricKey, setMetricKey] = useState("power");

  const asset = useResource<Asset | null>(
    useCallback(() => ds.getAsset(assetId), [ds, assetId]),
    { deps: [assetId] },
  );
  const history = useResource<SensorReading[]>(
    useCallback(() => ds.getSensorHistory(assetId, metricKey, HISTORY_HOURS), [ds, assetId, metricKey]),
    { deps: [assetId, metricKey] },
  );
  const forecast = useResource<Forecast>(
    useCallback(() => ds.getAssetForecast(assetId, "6h"), [ds, assetId]),
    { deps: [assetId] },
  );
  const anomalies = useResource<Anomaly[]>(useCallback(() => ds.getAnomalies(), [ds]));
  const recs = useResource<AIRecommendation[]>(useCallback(() => ds.getRecommendations(), [ds]));

  const models = useResource<ExplainableModel[]>(
    useCallback(() => ds.getExplainableModels(), [ds]),
  );
  const explainerModel = useMemo(
    () => (models.data ?? []).find((m) => m.scope.includes(assetId)),
    [models.data, assetId],
  );
  const explanation = useResource<Explanation | null>(
    useCallback(
      () =>
        explainerModel
          ? ds.getExplanation(explainerModel.id, assetId)
          : Promise.resolve({
              data: null,
              origin: "unavailable" as const,
              fetchedAt: new Date().toISOString(),
            }),
      [ds, assetId, explainerModel],
    ),
    { deps: [assetId, explainerModel?.id ?? ""] },
  );

  const assetAnomalies = useMemo(
    () => (anomalies.data ?? []).filter((a) => a.assetId === assetId),
    [anomalies.data, assetId],
  );
  const assetRecs = useMemo(
    () => (recs.data ?? []).filter((r) => r.targetAssets.includes(assetId)),
    [recs.data, assetId],
  );

  if (!isKnown) {
    return (
      <EmptyState
        title="Unknown asset"
        description={`No digital twin is registered under the id "${rawId}".`}
        icon={<Boxes className="h-5 w-5" />}
        action={
          <Link href="/twins" className="text-xs font-medium text-info hover:underline">
            Back to all twins
          </Link>
        }
      />
    );
  }

  const descriptor = ASSET_REGISTRY[assetId];
  const Icon = assetIcon(assetId);
  const accent = assetAccent(assetId);
  const historySeries = (history.data ?? []).map((r) => ({ timestamp: r.timestamp, value: r.value }));
  const historyUnit = history.data?.[0]?.unit ?? "";

  return (
    <>
      <Link
        href="/twins"
        className="mb-3 inline-flex items-center gap-1.5 text-xs font-medium text-content-muted transition-colors hover:text-content"
      >
        <ArrowLeft className="h-3 w-3" aria-hidden />
        All digital twins
      </Link>

      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
            style={{ backgroundColor: `${accent}14`, boxShadow: `inset 0 0 0 1px ${accent}33` }}
          >
            <Icon className="h-5 w-5" style={{ color: accent }} aria-hidden />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold tracking-tight text-content sm:text-xl">
                {descriptor.name}
              </h2>
              {asset.data ? <StatusBadge status={asset.data.status} size="md" /> : null}
              <Chip>{descriptor.location}</Chip>
              <Chip tone="info">{descriptor.category}</Chip>
            </div>
            <p className="mt-1 max-w-3xl text-xs leading-relaxed text-content-muted sm:text-[13px]">
              {descriptor.description}
            </p>
          </div>
        </div>
        <p className="text-2xs text-content-faint">
          Rated {formatKw(descriptor.ratedPowerKw, 0)}
          {asset.data ? ` · updated ${formatRelative(asset.data.lastUpdated, now)}` : ""}
        </p>
      </div>

      {/* Current state */}
      <ResourceBoundary
        resource={asset}
        loading={<LoadingState variant="cards" rows={4} />}
        isEmpty={(a) => a === null}
        empty={<EmptyState title="Twin not reporting" description="No state has been received for this asset." />}
      >
        {(data) =>
          data ? (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  label={data.powerKw < 0 ? "Power produced" : "Power drawn"}
                  value={formatKw(Math.abs(data.powerKw), 1)}
                  tone={data.powerKw < 0 ? "ok" : "info"}
                  icon={<Zap className="h-4 w-4" />}
                  caption={`Rated ${formatKw(descriptor.ratedPowerKw, 0)}`}
                  sparkline={data.sparkline}
                  sparklineColor={accent}
                />
                <MetricCard
                  label="Efficiency"
                  value={data.efficiencyPct === null ? "N/A" : formatPct(data.efficiencyPct)}
                  tone={
                    data.efficiencyPct === null
                      ? "neutral"
                      : data.efficiencyPct > 85
                        ? "ok"
                        : data.efficiencyPct > 70
                          ? "warn"
                          : "crit"
                  }
                  icon={<Percent className="h-4 w-4" />}
                  caption={
                    data.efficiencyPct === null
                      ? "Not defined for this asset type"
                      : "Derived by the twin from its state vector"
                  }
                  hint="Each asset type defines efficiency differently — thermal efficiency for the boiler, performance ratio for PV, loaded fraction for the compressor."
                />
                <MetricCard
                  label="Utilisation"
                  value={formatPct(data.utilisationPct, 0)}
                  tone="info"
                  icon={<Gauge className="h-4 w-4" />}
                  caption="Share of rated capacity in use"
                  footer={<Meter value={data.utilisationPct} tone="info" marker={90} />}
                />
                <MetricCard
                  label="Open alerts"
                  value={String(data.activeAlerts)}
                  tone={data.activeAlerts > 0 ? "warn" : "ok"}
                  caption={
                    assetAnomalies.filter((a) => a.status === "active").length > 0
                      ? `${assetAnomalies.filter((a) => a.status === "active").length} active anomaly detection(s)`
                      : "No active detections"
                  }
                />
              </div>

              {/* Sensor vector */}
              <Panel className="mt-3">
                <PanelHeader
                  title="Twin state vector"
                  subtitle="Every signal the twin currently holds, with its configured operating limits."
                  eyebrow="Sensor metrics"
                />
                <PanelBody className="grid grid-cols-2 gap-2.5 pt-3 sm:grid-cols-3 xl:grid-cols-6">
                  {data.metrics.map((m) => (
                    <MetricTile key={m.key} metric={m} />
                  ))}
                </PanelBody>
              </Panel>

              {/* History */}
              <Panel className="mt-3">
                <PanelHeader
                  title="Historical trend"
                  subtitle={`Last ${HISTORY_HOURS} hours of the selected signal.`}
                  eyebrow="Module 1 · Data acquisition"
                  actions={
                    <Segmented
                      label="Metric"
                      value={metricKey}
                      onChange={setMetricKey}
                      options={data.metrics
                        .filter((m) => m.value !== null)
                        .slice(0, 5)
                        .map((m) => ({ value: m.key, label: m.label }))}
                    />
                  }
                />
                <PanelBody className="pt-2">
                  <ResourceBoundary resource={history} loading={<LoadingState className="h-[240px]" />}>
                    {() => (
                      <TimeSeriesChart
                        data={historySeries}
                        series={[
                          {
                            key: "value",
                            label: data.metrics.find((m) => m.key === metricKey)?.label ?? "Value",
                            color: accent,
                          },
                        ]}
                        unit={historyUnit}
                        yLabel={historyUnit}
                        height={240}
                        showLegend={false}
                        emptyMessage="This signal has no samples in the selected window."
                      />
                    )}
                  </ResourceBoundary>
                </PanelBody>
              </Panel>
            </>
          ) : null
        }
      </ResourceBoundary>

      {/* Forecast + explanation */}
      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Asset load forecast"
            subtitle="Next 6 hours, predicted by the per-asset Random Forest model."
            eyebrow="Module 3 · Forecasting"
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={forecast} loading={<LoadingState className="h-[260px]" />}>
              {(data) => (
                <>
                  <ForecastChart
                    points={data.series}
                    nowMs={now || new Date(data.generatedAt).getTime()}
                    height={250}
                  />
                  <dl className="mt-3 grid grid-cols-2 gap-3 border-t border-line-soft pt-3 sm:grid-cols-4">
                    {[
                      { label: "MAE", value: data.accuracy.mae, unit: "kW" },
                      { label: "RMSE", value: data.accuracy.rmse, unit: "kW" },
                      { label: "R²", value: data.accuracy.r2, unit: "" },
                      { label: "MAPE", value: data.accuracy.mapePct, unit: "%" },
                    ].map((m) => (
                      <div key={m.label}>
                        <dt className="label-eyebrow">{m.label}</dt>
                        <dd className="mt-0.5 text-sm font-semibold tabular text-content">
                          {m.value === null ? "—" : `${formatNumber(m.value, m.label === "R²" ? 3 : 2)} ${m.unit}`}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </>
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader
            title="Why the model says this"
            subtitle="SHAP attribution for the model that covers this asset."
            eyebrow="Module 7 · Explainability"
          />
          <PanelBody className="pt-3">
            <ResourceBoundary resource={explanation} loading={<LoadingState className="h-56" />}>
              {(data) =>
                data === null ? (
                  <EmptyState
                    title="No explainer fitted"
                    description={`No SHAP explainer has been fitted for ${descriptor.name} yet. Rather than showing invented attributions, this panel stays empty until one is available.`}
                  />
                ) : (
                  <>
                    <FeatureImportanceChart
                      contributions={data.contributions}
                      unit={data.unit}
                      height={230}
                      maxFeatures={5}
                    />
                    <p className="mt-3 border-t border-line-soft pt-3 text-xs leading-relaxed text-content-muted">
                      {data.narrative}
                    </p>
                    <Link
                      href="/explainability"
                      className="mt-2 inline-block text-2xs font-medium text-info hover:underline"
                    >
                      Full explainability view →
                    </Link>
                  </>
                )
              }
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>

      {/* Anomalies + recommendations */}
      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Anomalies for this asset"
            subtitle="Detections raised by the Isolation Forest against this twin's signals."
            eyebrow="Module 6 · Anomaly detection"
          />
          <ResourceBoundary resource={anomalies} loading={<LoadingState variant="rows" rows={3} />}>
            {() => (
              <AlertTable
                anomalies={assetAnomalies}
                now={now}
                emptyTitle="No anomalies recorded"
                emptyDescription="The detector has not flagged this asset in the retained history."
              />
            )}
          </ResourceBoundary>
        </Panel>

        <Panel className="flex flex-col">
          <PanelHeader
            title="Agent recommendations"
            subtitle="Decisions that name this asset as a target."
            eyebrow="Module 4 · Decisions"
          />
          <PanelBody className="flex-1 space-y-2 pt-3">
            <ResourceBoundary resource={recs} loading={<LoadingState variant="rows" rows={2} />}>
              {() =>
                assetRecs.length === 0 ? (
                  <EmptyState
                    title="No open recommendations"
                    description="No agent has proposed an action for this asset in the current window."
                  />
                ) : (
                  assetRecs.map((r) => (
                    <RecommendationCard key={r.id} recommendation={r} now={now} compact />
                  ))
                )
              }
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>
    </>
  );
}
