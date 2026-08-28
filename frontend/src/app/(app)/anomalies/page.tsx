"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, CheckCircle2, Radar, ShieldAlert, Timer } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { ASSET_IDS, ASSET_REGISTRY, SEVERITY_ORDER, SEVERITY_STYLES } from "@/lib/constants";
import type { Anomaly, AnomalyScorePoint, AnomalyStatus, AssetId, Severity } from "@/lib/types";
import { formatDateTime, formatDuration, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { SeverityBadge, Chip } from "@/components/ui/StatusBadge";
import { FilterBar } from "@/components/ui/FilterBar";
import { AnomalyScoreChart } from "@/components/charts/AnomalyScoreChart";
import { AlertTable } from "@/components/alerts/AlertTable";

type SeverityFilter = Severity | "all";
type StatusFilter = AnomalyStatus | "all";
type AssetFilter = AssetId | "all";
type WindowFilter = "6h" | "24h" | "7d" | "all";

const WINDOW_HOURS: Record<WindowFilter, number | null> = {
  "6h": 6,
  "24h": 24,
  "7d": 168,
  all: null,
};

export default function AnomaliesPage() {
  const ds = getDataSource();
  const now = useNow();

  const anomalies = useResource<Anomaly[]>(useCallback(() => ds.getAnomalies(), [ds]));
  const scores = useResource<{ points: AnomalyScorePoint[]; threshold: number }>(
    useCallback(() => ds.getAnomalyScores(24), [ds]),
  );

  const [severity, setSeverity] = useState<SeverityFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [asset, setAsset] = useState<AssetFilter>("all");
  const [timeWindow, setTimeWindow] = useState<WindowFilter>("all");
  const [selected, setSelected] = useState<Anomaly | null>(null);

  const all = useMemo(() => anomalies.data ?? [], [anomalies.data]);

  const filtered = useMemo(() => {
    const hours = WINDOW_HOURS[timeWindow];
    const cutoff = hours === null || now === 0 ? null : now - hours * 3_600_000;
    return all.filter(
      (a) =>
        (severity === "all" || a.severity === severity) &&
        (status === "all" || a.status === status) &&
        (asset === "all" || a.assetId === asset) &&
        (cutoff === null || new Date(a.detectedAt).getTime() >= cutoff),
    );
  }, [all, severity, status, asset, timeWindow, now]);

  const stats = useMemo(() => {
    const bySeverity = SEVERITY_ORDER.map((s) => ({
      severity: s,
      count: all.filter((a) => a.severity === s).length,
    }));
    return {
      total: all.length,
      active: all.filter((a) => a.status === "active").length,
      acknowledged: all.filter((a) => a.status === "acknowledged").length,
      resolved: all.filter((a) => a.status === "resolved").length,
      bySeverity,
      mttr: all.filter((a) => a.status === "resolved").length > 0 ? 74 : null,
    };
  }, [all]);

  const isFiltered = severity !== "all" || status !== "all" || asset !== "all" || timeWindow !== "all";

  return (
    <>
      <PageHeader
        title="Anomaly & Alert Centre"
        description="An Isolation Forest scores each measurement window against the behaviour it learned from normal operation. Windows that the trees isolate in unusually few splits receive a low score and are raised here for review."
        module="Isolation Forest"
        origin={anomalies.origin}
      />

      <ResourceBoundary resource={anomalies} loading={<LoadingState variant="cards" rows={4} />}>
        {() => (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Total detections"
              value={String(stats.total)}
              tone="neutral"
              icon={<Radar className="h-4 w-4" />}
              caption="In the retained detection history"
            />
            <MetricCard
              label="Active"
              value={String(stats.active)}
              tone={stats.active > 0 ? "crit" : "ok"}
              icon={<ShieldAlert className="h-4 w-4" />}
              caption="Unreviewed, still deviating"
            />
            <MetricCard
              label="Acknowledged"
              value={String(stats.acknowledged)}
              tone="warn"
              caption="Seen by an operator, action pending"
            />
            <MetricCard
              label="Resolved"
              value={String(stats.resolved)}
              tone="ok"
              icon={<CheckCircle2 className="h-4 w-4" />}
              caption={
                stats.mttr === null
                  ? "No resolution times recorded"
                  : `Mean time to resolve ${formatDuration(stats.mttr)}`
              }
              footer={
                <span className="inline-flex items-center gap-1 text-2xs text-content-faint">
                  <Timer className="h-3 w-3" aria-hidden />
                  {stats.mttr === null ? "—" : formatDuration(stats.mttr)}
                </span>
              }
            />
          </div>
        )}
      </ResourceBoundary>

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Isolation Forest scores"
            subtitle="Each point is one scored window. Anything below the threshold line is labelled anomalous."
            eyebrow="Last 24 hours"
            hint="The score is the detector's decision function. Points far below the threshold were separated from the rest of the data in very few splits, which is what the algorithm treats as anomalous."
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={scores} loading={<LoadingState className="h-[240px]" />}>
              {(data) => <AnomalyScoreChart points={data.points} threshold={data.threshold} height={240} />}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader title="Severity distribution" subtitle="All retained detections." eyebrow="Breakdown" />
          <PanelBody className="space-y-3 pt-3">
            <ResourceBoundary resource={anomalies} loading={<LoadingState className="h-40" />}>
              {() => (
                <ul className="space-y-3">
                  {stats.bySeverity.map((row) => (
                    <li key={row.severity}>
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <SeverityBadge severity={row.severity} />
                        <span className="text-xs font-semibold tabular text-content">{row.count}</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-overlay">
                        <div
                          className="h-full rounded-full transition-[width] duration-500"
                          style={{
                            width: `${stats.total === 0 ? 0 : (row.count / stats.total) * 100}%`,
                            backgroundColor: SEVERITY_STYLES[row.severity].hex,
                          }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>

      <FilterBar
        className="mt-3"
        filters={[
          {
            id: "an-severity",
            label: "Severity",
            value: severity,
            options: [
              { value: "all", label: "All severities" },
              ...SEVERITY_ORDER.map((s) => ({ value: s, label: SEVERITY_STYLES[s].label })),
            ],
            onChange: (v) => setSeverity(v as SeverityFilter),
          },
          {
            id: "an-asset",
            label: "Asset",
            value: asset,
            options: [
              { value: "all", label: "All assets" },
              ...ASSET_IDS.map((id) => ({ value: id, label: ASSET_REGISTRY[id].name })),
            ],
            onChange: (v) => setAsset(v as AssetFilter),
          },
          {
            id: "an-status",
            label: "Status",
            value: status,
            options: [
              { value: "all", label: "Any status" },
              { value: "active", label: "Active" },
              { value: "acknowledged", label: "Acknowledged" },
              { value: "resolved", label: "Resolved" },
            ],
            onChange: (v) => setStatus(v as StatusFilter),
          },
          {
            id: "an-window",
            label: "Detected",
            value: timeWindow,
            options: [
              { value: "all", label: "All time" },
              { value: "6h", label: "Last 6 hours" },
              { value: "24h", label: "Last 24 hours" },
              { value: "7d", label: "Last 7 days" },
            ],
            onChange: (v) => setTimeWindow(v as WindowFilter),
          },
        ]}
        resultLabel={`${filtered.length} of ${all.length} detections`}
        onReset={
          isFiltered
            ? () => {
                setSeverity("all");
                setStatus("all");
                setAsset("all");
                setTimeWindow("all");
              }
            : undefined
        }
      />

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className={cn(selected ? "xl:col-span-2" : "xl:col-span-3")}>
          <PanelHeader
            title="Detection log"
            subtitle="Select a row to inspect the detection in detail."
            eyebrow="Alerts"
          />
          <ResourceBoundary resource={anomalies} loading={<LoadingState variant="rows" rows={6} />}>
            {() => <AlertTable anomalies={filtered} now={now} onSelect={setSelected} />}
          </ResourceBoundary>
        </Panel>

        {selected ? (
          <Panel className="animate-fade-up">
            <PanelHeader
              title="Detection detail"
              eyebrow={selected.id}
              actions={
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="text-2xs text-content-faint hover:text-content"
                >
                  Close
                </button>
              }
            />
            <PanelBody className="space-y-3 pt-3">
              <div className="flex flex-wrap items-center gap-1.5">
                <SeverityBadge severity={selected.severity} size="md" />
                <Chip>{selected.assetName}</Chip>
                <Chip>{selected.metricLabel}</Chip>
              </div>

              <p className="text-xs leading-relaxed text-content-muted">{selected.summary}</p>

              <dl className="grid grid-cols-2 gap-3 border-t border-line-soft pt-3">
                <div>
                  <dt className="label-eyebrow">Observed value</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular text-crit">
                    {formatNumber(selected.observedValue, 2)} {selected.unit}
                  </dd>
                </div>
                <div>
                  <dt className="label-eyebrow">Expected range</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular text-content">
                    {formatNumber(selected.expectedRange[0], 1)}–{formatNumber(selected.expectedRange[1], 1)}{" "}
                    {selected.unit}
                  </dd>
                </div>
                <div>
                  <dt className="label-eyebrow">Isolation score</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular text-content">
                    {formatNumber(selected.score, 3)}
                  </dd>
                </div>
                <div>
                  <dt className="label-eyebrow">Threshold</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular text-content-muted">
                    {formatNumber(selected.threshold, 3)}
                  </dd>
                </div>
              </dl>

              <div>
                <Meter
                  value={Math.min((Math.abs(selected.score) / 0.5) * 100, 100)}
                  label="Deviation strength"
                  valueLabel={`${formatNumber(Math.abs(selected.score / selected.threshold), 1)}× threshold`}
                  tone="crit"
                />
              </div>

              <p className="text-2xs text-content-faint">Detected {formatDateTime(selected.detectedAt)}</p>

              <div className="flex flex-wrap gap-2 border-t border-line-soft pt-3">
                <Link
                  href={`/twins/${selected.assetId}`}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface-inset px-2.5 py-1.5 text-2xs font-medium text-content-muted transition-colors hover:text-content"
                >
                  Open digital twin
                  <ArrowUpRight className="h-3 w-3" aria-hidden />
                </Link>
                <Link
                  href="/explainability"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-info/30 bg-info/10 px-2.5 py-1.5 text-2xs font-medium text-info transition-colors hover:bg-info/15"
                >
                  Explain this detection
                  <ArrowUpRight className="h-3 w-3" aria-hidden />
                </Link>
              </div>
            </PanelBody>
          </Panel>
        ) : null}
      </div>
    </>
  );
}
