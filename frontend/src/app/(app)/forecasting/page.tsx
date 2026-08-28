"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { Crosshair, Sigma, TrendingUp } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { ASSET_REGISTRY, CHART_COLORS } from "@/lib/constants";
import type { AssetForecastSummary, Forecast, ForecastHorizon } from "@/lib/types";
import { formatDateTime, formatKw, formatNumber, formatPct, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { Chip } from "@/components/ui/StatusBadge";
import { Segmented } from "@/components/ui/Segmented";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

const HORIZON_OPTIONS: { value: ForecastHorizon; label: string; title: string }[] = [
  { value: "1h", label: "1 H", title: "Next hour at 5-minute resolution" },
  { value: "6h", label: "6 H", title: "Next 6 hours at 15-minute resolution" },
  { value: "24h", label: "24 H", title: "Next 24 hours at 30-minute resolution" },
  { value: "7d", label: "7 D", title: "Next 7 days at 3-hour resolution" },
];

const MODEL_FEATURES = [
  "Lagged site load (15 / 30 / 60 min)",
  "Production line setpoints and shift state",
  "Ambient temperature and humidity",
  "Compressor and HVAC power",
  "Hour of day, day of week, holiday flag",
  "Rolling mean and standard deviation of load",
];

export default function ForecastingPage() {
  const ds = getDataSource();
  const now = useNow();
  const [horizon, setHorizon] = useState<ForecastHorizon>("24h");

  const forecast = useResource<Forecast>(
    useCallback(() => ds.getForecast(horizon), [ds, horizon]),
    { deps: [horizon] },
  );
  const perAsset = useResource<AssetForecastSummary[]>(
    useCallback(() => ds.getAssetForecastSummaries(horizon), [ds, horizon]),
    { deps: [horizon] },
  );

  const columns: Column<AssetForecastSummary>[] = [
    {
      key: "assetName",
      header: "Asset",
      sortable: true,
      render: (r) => (
        <Link href={`/twins/${r.assetId}`} className="text-[13px] font-medium text-content hover:text-info">
          {r.assetName}
        </Link>
      ),
    },
    {
      key: "currentKw",
      header: "Current",
      align: "right",
      sortable: true,
      render: (r) => formatKw(r.currentKw, 0),
    },
    {
      key: "predictedPeakKw",
      header: "Predicted peak",
      align: "right",
      sortable: true,
      render: (r) => (
        <span className="font-medium text-content">{formatKw(r.predictedPeakKw, 0)}</span>
      ),
    },
    {
      key: "changePct",
      header: "Change",
      align: "right",
      sortable: true,
      render: (r) => (
        <span
          className={cn(
            "font-medium",
            r.trend === "up" ? "text-warn" : r.trend === "down" ? "text-ok" : "text-content-faint",
          )}
        >
          {r.changePct > 0 ? "+" : ""}
          {formatNumber(r.changePct, 1)} %
        </span>
      ),
    },
    {
      key: "mapePct",
      header: "MAPE",
      align: "right",
      sortable: true,
      render: (r) => (r.mapePct === null ? "—" : `${formatNumber(r.mapePct, 2)} %`),
    },
    {
      key: "assetId",
      header: "vs rated",
      align: "right",
      render: (r) => (
        <Meter
          className="ml-auto w-20"
          value={Math.min((r.predictedPeakKw / ASSET_REGISTRY[r.assetId].ratedPowerKw) * 100, 100)}
          tone="info"
        />
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Forecasting & Analytics"
        description="Site and asset load prediction using a Random Forest regressor trained on lagged load, production state, ambient conditions and calendar features. Accuracy below is computed on the in-sample overlap shown in the chart."
        module="Random Forest"
        origin={forecast.origin}
        actions={
          <Segmented
            label="Forecast horizon"
            options={HORIZON_OPTIONS}
            value={horizon}
            onChange={setHorizon}
            size="md"
          />
        }
      />

      <ResourceBoundary resource={forecast} loading={<LoadingState variant="cards" rows={4} />}>
        {(data) => (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="MAE"
              value={data.accuracy.mae === null ? "—" : formatNumber(data.accuracy.mae, 2)}
              unit="kW"
              tone="neutral"
              icon={<Sigma className="h-4 w-4" />}
              caption={`Mean absolute error over ${data.accuracy.sampleCount} scored samples`}
              hint="Mean Absolute Error — the average size of the prediction error in kilowatts, regardless of sign."
            />
            <MetricCard
              label="RMSE"
              value={data.accuracy.rmse === null ? "—" : formatNumber(data.accuracy.rmse, 2)}
              unit="kW"
              tone="neutral"
              caption="Penalises large misses more heavily than MAE"
              hint="Root Mean Squared Error — the square root of the average squared error. Larger than MAE whenever the model makes occasional big mistakes."
            />
            <MetricCard
              label="R²"
              value={data.accuracy.r2 === null ? "—" : formatNumber(data.accuracy.r2, 3)}
              tone={data.accuracy.r2 !== null && data.accuracy.r2 > 0.9 ? "ok" : "neutral"}
              caption="Share of load variance explained"
              hint="Coefficient of determination. 1.0 is a perfect fit; 0 means the model does no better than always predicting the mean load."
            />
            <MetricCard
              label="MAPE"
              value={data.accuracy.mapePct === null ? "—" : formatNumber(data.accuracy.mapePct, 2)}
              unit="%"
              tone={data.accuracy.mapePct !== null && data.accuracy.mapePct < 5 ? "ok" : "warn"}
              caption="Mean absolute percentage error"
              hint="Mean Absolute Percentage Error — the average error as a share of the measured value. Useful for comparing models across assets of different sizes."
            />
          </div>
        )}
      </ResourceBoundary>

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-4">
        <Panel className="xl:col-span-3">
          <PanelHeader
            title="Actual vs predicted site load"
            subtitle="History is measured; the shaded region to the right of 'now' is model output with its 95 % prediction interval."
            eyebrow={`Horizon · ${HORIZON_OPTIONS.find((h) => h.value === horizon)?.title}`}
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={forecast} loading={<LoadingState className="h-[340px]" />}>
              {(data) => (
                <ForecastChart
                  points={data.series}
                  nowMs={now || new Date(data.generatedAt).getTime()}
                  peakAt={data.peak?.expectedAt ?? null}
                  height={340}
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <div className="space-y-3">
          <Panel>
            <PanelHeader title="Peak-load prediction" eyebrow="What to prepare for" />
            <PanelBody className="pt-3">
              <ResourceBoundary resource={forecast} loading={<LoadingState className="h-32" />}>
                {(data) =>
                  data.peak === null ? (
                    <p className="text-xs text-content-muted">
                      The model did not return a peak for this horizon.
                    </p>
                  ) : (
                    <>
                      <div className="flex items-start gap-2.5">
                        <Crosshair className="mt-0.5 h-4 w-4 text-accent-forecast" aria-hidden />
                        <div>
                          <p className="text-2xl font-semibold tabular leading-none text-content">
                            {formatKw(data.peak.predictedKw, 0)}
                          </p>
                          <p className="mt-1.5 text-xs text-content-muted">
                            expected around{" "}
                            <span className="font-medium text-content">
                              {formatTime(data.peak.expectedAt)}
                            </span>{" "}
                            on {formatDateTime(data.peak.expectedAt).split(" · ")[0]}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 border-t border-line-soft pt-3">
                        <Meter
                          value={data.peak.confidence === null ? null : data.peak.confidence * 100}
                          label="Model confidence in the peak window"
                          valueLabel={
                            data.peak.confidence === null
                              ? "Not reported"
                              : formatPct(data.peak.confidence * 100, 0)
                          }
                          tone="info"
                        />
                      </div>
                      <p className="mt-3 text-2xs leading-relaxed text-content-faint">
                        The optimisation and decision modules consume this peak directly — it sets the
                        window in which battery discharge and deferrable load are scheduled.
                      </p>
                    </>
                  )
                }
              </ResourceBoundary>
            </PanelBody>
          </Panel>

          <Panel>
            <PanelHeader title="Model card" eyebrow="Provenance" />
            <PanelBody className="space-y-3 pt-3">
              <ResourceBoundary resource={forecast} loading={<LoadingState className="h-40" />}>
                {(data) => (
                  <>
                    <dl className="space-y-2 text-xs">
                      {[
                        ["Model", data.modelName],
                        ["Algorithm", data.algorithm],
                        ["Target", data.target],
                        ["Resolution", `${data.resolutionMinutes} min`],
                        ["Generated", formatDateTime(data.generatedAt)],
                        [
                          "Evaluated on",
                          data.accuracy.evaluatedAt ? formatDateTime(data.accuracy.evaluatedAt) : "—",
                        ],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-3">
                          <dt className="text-content-faint">{k}</dt>
                          <dd className="text-right font-medium text-content">{v}</dd>
                        </div>
                      ))}
                    </dl>
                    <div className="border-t border-line-soft pt-3">
                      <p className="label-eyebrow mb-1.5">Input features</p>
                      <ul className="flex flex-wrap gap-1">
                        {MODEL_FEATURES.map((f) => (
                          <li key={f}>
                            <Chip>{f}</Chip>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <Link
                      href="/explainability"
                      className="inline-block text-2xs font-medium text-info hover:underline"
                    >
                      See how these features contributed →
                    </Link>
                  </>
                )}
              </ResourceBoundary>
            </PanelBody>
          </Panel>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-2">
        <Panel>
          <PanelHeader
            title="Demand trend"
            subtitle="Prediction only, plotted against its interval bounds."
            eyebrow="Trajectory"
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={forecast} loading={<LoadingState className="h-[260px]" />}>
              {(data) => (
                <TimeSeriesChart
                  data={data.series.map((p) => ({
                    timestamp: p.timestamp,
                    predicted: p.predictedKw,
                    lower: p.lowerKw,
                    upper: p.upperKw,
                  }))}
                  series={[
                    { key: "upper", label: "Upper bound", color: CHART_COLORS.baseline, type: "line", dashed: true, strokeWidth: 1 },
                    { key: "predicted", label: "Predicted load", color: CHART_COLORS.forecast },
                    { key: "lower", label: "Lower bound", color: CHART_COLORS.baseline, type: "line", dashed: true, strokeWidth: 1 },
                  ]}
                  yLabel="kW"
                  height={260}
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader
            title="Asset-wise forecast"
            subtitle="Predicted peak per consuming asset over the selected horizon."
            eyebrow="Breakdown"
            actions={
              <span className="inline-flex items-center gap-1 text-2xs text-content-faint">
                <TrendingUp className="h-3 w-3" aria-hidden />
                {HORIZON_OPTIONS.find((h) => h.value === horizon)?.label}
              </span>
            }
          />
          <ResourceBoundary resource={perAsset} loading={<LoadingState variant="rows" rows={5} />}>
            {(data) => (
              <DataTable
                columns={columns}
                rows={data}
                rowKey={(r) => r.assetId}
                initialSort={{ key: "predictedPeakKw", direction: "desc" }}
              />
            )}
          </ResourceBoundary>
        </Panel>
      </div>
    </>
  );
}
