"use client";

import { useCallback, useMemo } from "react";
import Link from "next/link";
import { ArrowLeftRight, BatteryCharging, Factory, Sun } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { CHART_COLORS, DEMAND_CAP_KW } from "@/lib/constants";
import type { EnergyFlowSnapshot, EnergyReading } from "@/lib/types";
import { formatKw, formatPct, formatTime } from "@/lib/format";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EnergyFlow } from "@/components/energy/EnergyFlow";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

const LEGEND = [
  { label: "Solar generation", color: CHART_COLORS.solar },
  { label: "Battery discharge", color: CHART_COLORS.battery },
  { label: "Grid import", color: CHART_COLORS.grid },
  { label: "Export to grid", color: CHART_COLORS.generation },
  { label: "Load draw", color: CHART_COLORS.load },
];

export default function EnergyFlowPage() {
  const ds = getDataSource();
  const flow = useResource<EnergyFlowSnapshot>(useCallback(() => ds.getEnergyFlow(), [ds]));
  const energy = useResource<EnergyReading[]>(useCallback(() => ds.getEnergyWindow(6, 10), [ds]));

  const totals = useMemo(() => {
    const nodes = flow.data?.nodes ?? [];
    const generation = nodes.find((n) => n.id === "solar")?.powerKw ?? 0;
    const battery = nodes.find((n) => n.id === "battery")?.powerKw ?? 0;
    const grid = nodes.find((n) => n.id === "grid")?.powerKw ?? 0;
    const load = nodes.filter((n) => n.kind === "sink").reduce((a, n) => a + n.powerKw, 0);
    return { generation, battery, grid, load };
  }, [flow.data]);

  return (
    <>
      <PageHeader
        title="Energy Flow & System Map"
        description="How power moves through the site right now: rooftop PV and the grid feed the main distribution bus, storage buffers between them, and each plant load draws from the bus. Line thickness is proportional to power and the moving dashes show direction."
        origin={flow.origin}
        actions={
          flow.data ? (
            <span className="text-2xs text-content-faint">
              Snapshot {formatTime(flow.data.timestamp)}
            </span>
          ) : null
        }
      />

      <ResourceBoundary resource={flow} loading={<LoadingState variant="cards" rows={4} />}>
        {() => (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="On-site generation"
              value={formatKw(Math.abs(totals.generation), 0)}
              tone="ok"
              icon={<Sun className="h-4 w-4" />}
              caption="Rooftop PV, AC side of the inverters"
            />
            <MetricCard
              label="Plant consumption"
              value={formatKw(totals.load, 0)}
              tone="info"
              icon={<Factory className="h-4 w-4" />}
              caption="Sum of all connected loads"
            />
            <MetricCard
              label={totals.battery < 0 ? "Storage charging" : totals.battery > 1 ? "Storage discharging" : "Storage idle"}
              value={formatKw(Math.abs(totals.battery), 0)}
              tone="neutral"
              icon={<BatteryCharging className="h-4 w-4" />}
              caption="Positive to the bus, negative from it"
            />
            <MetricCard
              label={totals.grid >= 0 ? "Grid import" : "Grid export"}
              value={formatKw(Math.abs(totals.grid), 0)}
              tone={totals.grid > DEMAND_CAP_KW * 0.9 ? "warn" : "neutral"}
              icon={<ArrowLeftRight className="h-4 w-4" />}
              caption={
                totals.load > 0
                  ? `${formatPct((Math.max(totals.grid, 0) / totals.load) * 100, 0)} of demand`
                  : "No load"
              }
            />
          </div>
        )}
      </ResourceBoundary>

      <Panel className="mt-3 overflow-hidden">
        <PanelHeader
          title="System energy flow"
          subtitle="Sources and storage on the left, distribution in the centre, plant loads on the right."
          eyebrow="Live topology"
          actions={
            <ul className="hidden flex-wrap items-center gap-3 lg:flex">
              {LEGEND.map((l) => (
                <li key={l.label} className="flex items-center gap-1.5 text-2xs text-content-muted">
                  <span className="h-0.5 w-4 rounded-full" style={{ backgroundColor: l.color }} aria-hidden />
                  {l.label}
                </li>
              ))}
            </ul>
          }
        />
        <PanelBody className="grid-backdrop pt-4">
          <ResourceBoundary resource={flow} loading={<LoadingState className="h-[420px]" />}>
            {(data) => <EnergyFlow snapshot={data} />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Flow history"
            subtitle="How the balance between the three supply paths has moved over the last 6 hours."
            eyebrow="Context"
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={energy} loading={<LoadingState className="h-[260px]" />}>
              {(data) => (
                <TimeSeriesChart
                  data={data}
                  series={[
                    { key: "solarKw", label: "Solar", color: CHART_COLORS.solar },
                    { key: "batteryKw", label: "Battery", color: CHART_COLORS.battery, type: "line" },
                    { key: "gridKw", label: "Grid", color: CHART_COLORS.grid, type: "line" },
                    { key: "consumptionKw", label: "Total demand", color: CHART_COLORS.load, type: "line", dashed: true },
                  ]}
                  yLabel="kW"
                  height={260}
                  includeZero
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader
            title="Node status"
            subtitle="Every node in the map with its health state."
            eyebrow="Topology"
          />
          <PanelBody className="pt-3">
            <ResourceBoundary resource={flow} loading={<LoadingState variant="rows" rows={6} />}>
              {(data) => (
                <ul className="space-y-1.5">
                  {data.nodes.map((n) => {
                    const inner = (
                      <>
                        <div className="min-w-0">
                          <p className="truncate text-[13px] font-medium text-content">{n.label}</p>
                          <p className="truncate text-2xs text-content-faint">{n.detail}</p>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <span className="text-[13px] font-semibold tabular text-content">
                            {formatKw(Math.abs(n.powerKw), 0)}
                          </span>
                          <StatusBadge status={n.status} />
                        </div>
                      </>
                    );
                    return (
                      <li key={n.id}>
                        {n.assetId ? (
                          <Link
                            href={`/twins/${n.assetId}`}
                            className="flex items-center justify-between gap-3 rounded-lg border border-line bg-surface-inset px-3 py-2 transition-colors hover:border-line-strong hover:bg-surface-raised"
                          >
                            {inner}
                          </Link>
                        ) : (
                          <div className="flex items-center justify-between gap-3 rounded-lg border border-line bg-surface-inset px-3 py-2">
                            {inner}
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>
    </>
  );
}
