"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { Download, Gauge, Leaf, Sigma, Zap } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import {
  ASSET_REGISTRY,
  CHART_COLORS,
  DEMAND_CAP_KW,
  SEVERITY_ORDER,
  SEVERITY_STYLES,
} from "@/lib/constants";
import type { PerformanceReport, ReportPeriod } from "@/lib/types";
import {
  formatCurrency,
  formatDate,
  formatKw,
  formatKwh,
  formatNumber,
  formatPct,
} from "@/lib/format";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { Segmented } from "@/components/ui/Segmented";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { CategoryBarChart } from "@/components/charts/CategoryBarChart";

type AssetRow = PerformanceReport["assetBreakdown"][number];

const PERIOD_OPTIONS: { value: ReportPeriod; label: string }[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
];

/** Builds a CSV from the asset breakdown and hands it to the browser. */
function exportCsv(report: PerformanceReport) {
  const header = ["Asset", "Energy (kWh)", "Share (%)", "Efficiency (%)", "Availability (%)"];
  const lines = report.assetBreakdown.map((r) =>
    [r.assetName, r.energyKwh, r.sharePct, r.efficiencyPct ?? "", r.availabilityPct].join(","),
  );
  const csv = [header.join(","), ...lines].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `energy-report-${report.period}-${report.rangeEnd.slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const ds = getDataSource();
  const [period, setPeriod] = useState<ReportPeriod>("week");

  const report = useResource<PerformanceReport>(
    useCallback(() => ds.getReport(period), [ds, period]),
    { deps: [period] },
  );

  const columns: Column<AssetRow>[] = [
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
      key: "energyKwh",
      header: "Energy",
      align: "right",
      sortable: true,
      render: (r) => formatKwh(r.energyKwh),
    },
    {
      key: "sharePct",
      header: "Share of load",
      align: "right",
      sortable: true,
      render: (r) => (
        <div className="flex items-center justify-end gap-2">
          <Meter value={r.sharePct} tone="info" className="w-20" />
          <span className="w-12 text-right tabular">{formatPct(r.sharePct, 1)}</span>
        </div>
      ),
    },
    {
      key: "efficiencyPct",
      header: "Efficiency",
      align: "right",
      sortable: true,
      render: (r) => (r.efficiencyPct === null ? "—" : formatPct(r.efficiencyPct)),
    },
    {
      key: "availabilityPct",
      header: "Availability",
      align: "right",
      sortable: true,
      render: (r) => (
        <span className={r.availabilityPct < 98 ? "text-warn" : "text-content"}>
          {formatPct(r.availabilityPct)}
        </span>
      ),
    },
    {
      key: "assetId",
      header: "Rated",
      align: "right",
      render: (r) => formatKw(ASSET_REGISTRY[r.assetId].ratedPowerKw, 0),
    },
  ];

  return (
    <>
      <PageHeader
        title="Reports & Performance"
        description="Aggregated performance over the selected period: energy use and generation, demand profile, asset efficiency, forecast accuracy, anomaly statistics and the modelled impact of the optimiser."
        origin={report.origin}
        actions={
          <>
            <Segmented
              label="Reporting period"
              options={PERIOD_OPTIONS}
              value={period}
              onChange={setPeriod}
              size="md"
            />
            <button
              type="button"
              disabled={!report.data}
              onClick={() => report.data && exportCsv(report.data)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface-inset px-3 py-1.5 text-xs font-medium text-content-muted transition-colors hover:border-line-strong hover:text-content disabled:opacity-40"
            >
              <Download className="h-3 w-3" aria-hidden />
              Export CSV
            </button>
          </>
        }
      />

      <ResourceBoundary resource={report} loading={<LoadingState variant="cards" rows={4} />}>
        {(data) => (
          <>
            <p className="mb-3 text-2xs text-content-faint">
              {formatDate(data.rangeStart)} — {formatDate(data.rangeEnd)}
            </p>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Energy consumed"
                value={formatKwh(data.totals.consumptionKwh)}
                tone="info"
                icon={<Zap className="h-4 w-4" />}
                caption={`Average load ${formatKw(data.totals.averageLoadKw, 0)}`}
              />
              <MetricCard
                label="Energy generated"
                value={formatKwh(data.totals.generationKwh)}
                tone="ok"
                icon={<Leaf className="h-4 w-4" />}
                caption={`Renewable utilisation ${formatPct(data.totals.renewableSharePct, 1)}`}
                footer={<Meter value={data.totals.renewableSharePct} tone="ok" />}
              />
              <MetricCard
                label="Peak demand"
                value={formatKw(data.totals.peakDemandKw, 0)}
                tone={data.totals.peakDemandKw > DEMAND_CAP_KW ? "crit" : "warn"}
                icon={<Gauge className="h-4 w-4" />}
                caption={`Contracted maximum demand ${DEMAND_CAP_KW} kW`}
                footer={<Meter value={(data.totals.peakDemandKw / DEMAND_CAP_KW) * 100} tone="warn" marker={100} />}
              />
              <MetricCard
                label="Load factor"
                value={formatPct(data.totals.loadFactorPct, 1)}
                tone="neutral"
                icon={<Sigma className="h-4 w-4" />}
                caption="Average load as a share of peak demand"
                hint="A higher load factor means demand is flatter, which lowers demand charges. Peak shaving raises it."
              />
            </div>

            <Panel className="mt-3">
              <PanelHeader
                title="Energy profile"
                subtitle="Consumption against on-site generation for each interval in the period."
                eyebrow="Trend"
              />
              <PanelBody className="pt-2">
                <CategoryBarChart
                  data={data.series}
                  categoryKey="label"
                  series={[
                    { key: "consumptionKwh", label: "Consumption", color: CHART_COLORS.load },
                    { key: "generationKwh", label: "Generation", color: CHART_COLORS.generation },
                  ]}
                  height={280}
                />
              </PanelBody>
            </Panel>

            <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
              <Panel className="xl:col-span-2">
                <PanelHeader
                  title="Asset efficiency & utilisation"
                  subtitle="Where the energy went, and how well each asset converted it."
                  eyebrow="Breakdown"
                />
                <DataTable
                  columns={columns}
                  rows={data.assetBreakdown}
                  rowKey={(r) => r.assetId}
                  initialSort={{ key: "energyKwh", direction: "desc" }}
                />
              </Panel>

              <div className="space-y-3">
                <Panel>
                  <PanelHeader
                    title="Forecast performance"
                    subtitle="Random Forest accuracy over the evaluated window."
                    eyebrow="Model quality"
                  />
                  <PanelBody className="pt-3">
                    <dl className="grid grid-cols-2 gap-3">
                      {[
                        { label: "MAE", value: data.forecastPerformance.mae, unit: "kW", digits: 2 },
                        { label: "RMSE", value: data.forecastPerformance.rmse, unit: "kW", digits: 2 },
                        { label: "R²", value: data.forecastPerformance.r2, unit: "", digits: 3 },
                        { label: "MAPE", value: data.forecastPerformance.mapePct, unit: "%", digits: 2 },
                      ].map((m) => (
                        <div key={m.label}>
                          <dt className="label-eyebrow">{m.label}</dt>
                          <dd className="mt-0.5 text-base font-semibold tabular text-content">
                            {m.value === null ? "—" : `${formatNumber(m.value, m.digits)} ${m.unit}`}
                          </dd>
                        </div>
                      ))}
                    </dl>
                    <p className="mt-3 border-t border-line-soft pt-2.5 text-2xs text-content-faint">
                      Computed over {data.forecastPerformance.sampleCount} scored samples.
                    </p>
                  </PanelBody>
                </Panel>

                <Panel>
                  <PanelHeader title="Anomaly statistics" eyebrow="Isolation Forest" />
                  <PanelBody className="space-y-2.5 pt-3">
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        ["Total", data.anomalyStats.total],
                        ["Active", data.anomalyStats.active],
                        ["Resolved", data.anomalyStats.resolved],
                      ].map(([k, v]) => (
                        <div key={String(k)} className="rounded-lg border border-line bg-surface-inset p-2.5">
                          <p className="label-eyebrow">{k}</p>
                          <p className="mt-0.5 text-base font-semibold tabular text-content">{v}</p>
                        </div>
                      ))}
                    </div>
                    <ul className="space-y-1.5 pt-1">
                      {SEVERITY_ORDER.map((s) => (
                        <li key={s} className="flex items-center gap-2">
                          <span
                            className="h-1.5 w-1.5 rounded-full"
                            style={{ backgroundColor: SEVERITY_STYLES[s].hex }}
                            aria-hidden
                          />
                          <span className="text-2xs text-content-muted">{SEVERITY_STYLES[s].label}</span>
                          <span className="ml-auto text-2xs font-medium tabular text-content">
                            {data.anomalyStats.bySeverity[s]}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </PanelBody>
                </Panel>
              </div>
            </div>

            <Panel className="mt-3">
              <PanelHeader
                title="Optimisation impact"
                subtitle="Modelled effect of the Genetic Algorithm schedules over the period, against the unmodified baseline."
                eyebrow="Module 5 · Optimisation"
                hint="These are modelled differences from the optimiser's own comparison, not metered savings."
              />
              <PanelBody className="pt-3">
                <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div>
                    <dt className="label-eyebrow">Runs completed</dt>
                    <dd className="mt-0.5 text-lg font-semibold tabular text-content">
                      {data.optimizationImpact.runsCompleted}
                    </dd>
                  </div>
                  <div>
                    <dt className="label-eyebrow">Peak reduction</dt>
                    <dd className="mt-0.5 text-lg font-semibold tabular text-ok">
                      {data.optimizationImpact.peakReductionKw === null
                        ? "—"
                        : formatKw(data.optimizationImpact.peakReductionKw, 1)}
                    </dd>
                  </div>
                  <div>
                    <dt className="label-eyebrow">Energy shifted</dt>
                    <dd className="mt-0.5 text-lg font-semibold tabular text-content">
                      {data.optimizationImpact.energyShiftedKwh === null
                        ? "—"
                        : formatKwh(data.optimizationImpact.energyShiftedKwh)}
                    </dd>
                  </div>
                  <div>
                    <dt className="label-eyebrow">Modelled cost difference</dt>
                    <dd className="mt-0.5 text-lg font-semibold tabular text-ok">
                      {data.optimizationImpact.costDelta === null
                        ? "—"
                        : formatCurrency(Math.abs(data.optimizationImpact.costDelta))}
                    </dd>
                  </div>
                </dl>
              </PanelBody>
            </Panel>
          </>
        )}
      </ResourceBoundary>
    </>
  );
}
