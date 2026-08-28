"use client";

import type { Anomaly, AnomalyStatus, Severity } from "@/lib/types";
import { formatDateTime, formatNumber, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { SeverityBadge } from "@/components/ui/StatusBadge";

const STATUS_STYLE: Record<AnomalyStatus, string> = {
  active: "text-crit",
  acknowledged: "text-warn",
  resolved: "text-content-faint",
};

const STATUS_LABEL: Record<AnomalyStatus, string> = {
  active: "Active",
  acknowledged: "Acknowledged",
  resolved: "Resolved",
};

const SEVERITY_RANK: Record<Severity, number> = { low: 1, medium: 2, high: 3, critical: 4 };

type AnomalyRow = Anomaly & { severityRank: number };

interface AlertTableProps {
  anomalies: Anomaly[];
  now: number;
  onSelect?: (anomaly: Anomaly) => void;
  emptyTitle?: string;
  emptyDescription?: string;
}

/** Sortable anomaly log with severity, score and provenance columns. */
export function AlertTable({
  anomalies,
  now,
  onSelect,
  emptyTitle = "No anomalies match these filters",
  emptyDescription = "Try widening the severity, asset or status filters.",
}: AlertTableProps) {
  // Severity is ordinal, so sorting needs a rank rather than the label text.
  const rows: AnomalyRow[] = anomalies.map((a) => ({
    ...a,
    severityRank: SEVERITY_RANK[a.severity],
  }));

  const columns: Column<AnomalyRow>[] = [
    {
      key: "severityRank",
      header: "Severity",
      sortable: true,
      render: (a) => <SeverityBadge severity={a.severity} />,
    },
    {
      key: "assetName",
      header: "Asset",
      sortable: true,
      render: (a) => (
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-content">{a.assetName}</p>
          <p className="truncate text-2xs text-content-faint">{a.metricLabel}</p>
        </div>
      ),
    },
    {
      key: "summary",
      header: "Detection",
      render: (a) => (
        <p className="max-w-md text-xs leading-relaxed text-content-muted">{a.summary}</p>
      ),
    },
    {
      key: "observedValue",
      header: "Observed",
      align: "right",
      sortable: true,
      render: (a) => (
        <div>
          <p className="text-[13px] font-medium tabular text-content">
            {formatNumber(a.observedValue, 2)} {a.unit}
          </p>
          <p className="text-2xs tabular text-content-faint">
            expected {formatNumber(a.expectedRange[0], 1)}–{formatNumber(a.expectedRange[1], 1)}
          </p>
        </div>
      ),
    },
    {
      key: "score",
      header: "Score",
      align: "right",
      sortable: true,
      render: (a) => (
        <div>
          <p
            className={cn(
              "text-[13px] font-medium tabular",
              a.score < a.threshold ? "text-crit" : "text-content",
            )}
          >
            {formatNumber(a.score, 3)}
          </p>
          <p className="text-2xs tabular text-content-faint">thr {formatNumber(a.threshold, 2)}</p>
        </div>
      ),
    },
    {
      key: "detectedAt",
      header: "Detected",
      align: "right",
      sortable: true,
      render: (a) => (
        <div>
          <p className="whitespace-nowrap text-[13px] tabular text-content">
            {formatRelative(a.detectedAt, now)}
          </p>
          <p className="whitespace-nowrap text-2xs tabular text-content-faint">
            {formatDateTime(a.detectedAt)}
          </p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      align: "right",
      sortable: true,
      render: (a) => (
        <span className={cn("text-xs font-medium", STATUS_STYLE[a.status])}>
          {STATUS_LABEL[a.status]}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(a) => a.id}
      initialSort={{ key: "detectedAt", direction: "desc" }}
      onRowClick={onSelect}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
    />
  );
}
