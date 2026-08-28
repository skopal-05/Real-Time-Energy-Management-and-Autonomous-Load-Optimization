"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, BatteryCharging, Cable, Gauge, Radio, Sun } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { useAppState } from "@/providers/AppStateProvider";
import { CHART_COLORS, CONSUMER_ASSET_IDS, DEMAND_CAP_KW } from "@/lib/constants";
import type { Asset, EnergyFlowSnapshot, EnergyReading } from "@/lib/types";
import { formatKw, formatPct, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { StatusDot } from "@/components/ui/StatusBadge";
import {
  DateRangeSelector,
  RANGE_HOURS,
  RANGE_STEP_MINUTES,
  type RangeKey,
} from "@/components/ui/DateRangeSelector";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { AssetStatusGrid } from "@/components/assets/AssetStatusGrid";
import { EnergyFlow } from "@/components/energy/EnergyFlow";
import { assetIcon } from "@/components/assets/assetIcon";

export default function MonitoringPage() {
  const ds = getDataSource();
  const now = useNow();
  const { streaming, pollIntervalMs } = useAppState();
  const [range, setRange] = useState<RangeKey>("6h");

  const energy = useResource<EnergyReading[]>(
    useCallback(
      () => ds.getEnergyWindow(RANGE_HOURS[range], RANGE_STEP_MINUTES[range]),
      [ds, range],
    ),
    { deps: [range] },
  );
  const assets = useResource<Asset[]>(useCallback(() => ds.getAssets(), [ds]));
  const flow = useResource<EnergyFlowSnapshot>(useCallback(() => ds.getEnergyFlow(), [ds]));

  const latest = useMemo(() => {
    const list = energy.data ?? [];
    return list.length > 0 ? list[list.length - 1] : null;
  }, [energy.data]);

  const availableSupplyKw = useMemo(() => {
    if (!latest) return null;
    // PV output plus what storage and the grid connection could deliver now.
    const batteryHeadroom = latest.batterySocPct > 20 ? 200 : 0;
    return latest.solarKw + batteryHeadroom + DEMAND_CAP_KW;
  }, [latest]);

  const operatingAssets = useMemo(
    () => (assets.data ?? []).filter((a) => CONSUMER_ASSET_IDS.includes(a.id)),
    [assets.data],
  );

  return (
    <>
      <PageHeader
        title="Real-Time Monitoring"
        description="Continuous view of the acquisition layer: every measured signal feeding the digital twins, the instantaneous energy balance, and the operating state of each plant load."
        module="Module 1 · Data acquisition"
        origin={energy.origin}
        actions={
          <>
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-2xs font-medium",
                streaming
                  ? "border-ok/30 bg-ok/10 text-ok"
                  : "border-line bg-surface-inset text-content-faint",
              )}
            >
              <Radio className={cn("h-3 w-3", streaming && "animate-pulse-dot")} aria-hidden />
              {streaming ? `Streaming · ${Math.round(pollIntervalMs / 1000)} s` : "Stream paused"}
            </span>
            <DateRangeSelector value={range} onChange={setRange} options={["1h", "6h", "12h", "24h"]} />
          </>
        }
      />

      {/* Live tiles */}
      <ResourceBoundary resource={energy} loading={<LoadingState variant="cards" rows={5} />}>
        {(data) => {
          const last = data[data.length - 1];
          if (!last) return null;
          return (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <MetricCard
                label="Site demand"
                value={formatKw(last.consumptionKw, 0)}
                tone="info"
                icon={<Gauge className="h-4 w-4" />}
                caption={`Sampled ${formatTime(last.timestamp)}`}
                sparkline={data.map((d) => d.consumptionKw)}
                sparklineColor={CHART_COLORS.load}
              />
              <MetricCard
                label="Solar generation"
                value={formatKw(last.solarKw, 0)}
                tone="ok"
                icon={<Sun className="h-4 w-4" />}
                caption="Inverter AC output"
                sparkline={data.map((d) => d.solarKw)}
                sparklineColor={CHART_COLORS.solar}
              />
              <MetricCard
                label={last.batteryKw < 0 ? "Battery charging" : last.batteryKw > 1 ? "Battery discharging" : "Battery idle"}
                value={formatKw(Math.abs(last.batteryKw), 0)}
                tone="neutral"
                icon={<BatteryCharging className="h-4 w-4" />}
                caption={`State of charge ${formatPct(last.batterySocPct, 0)}`}
                footer={
                  <Meter
                    value={last.batterySocPct}
                    tone={last.batterySocPct < 25 ? "warn" : "ok"}
                    marker={18}
                  />
                }
              />
              <MetricCard
                label={last.gridKw >= 0 ? "Grid import" : "Grid export"}
                value={formatKw(Math.abs(last.gridKw), 0)}
                tone={last.gridKw > DEMAND_CAP_KW * 0.9 ? "warn" : "neutral"}
                icon={<Cable className="h-4 w-4" />}
                caption={`Contracted maximum demand ${DEMAND_CAP_KW} kW`}
                footer={<Meter value={(Math.max(last.gridKw, 0) / DEMAND_CAP_KW) * 100} tone="info" marker={95} />}
              />
              <MetricCard
                label="Demand vs available supply"
                value={
                  availableSupplyKw === null
                    ? "—"
                    : formatPct((last.consumptionKw / availableSupplyKw) * 100, 0)
                }
                tone="neutral"
                icon={<Activity className="h-4 w-4" />}
                caption={
                  availableSupplyKw === null
                    ? "Awaiting data"
                    : `${formatKw(last.consumptionKw, 0)} of ${formatKw(availableSupplyKw, 0)} available`
                }
                hint="Available supply is PV output plus dischargeable storage plus the contracted grid capacity."
              />
            </div>
          );
        }}
      </ResourceBoundary>

      {/* Balance chart */}
      <Panel className="mt-3">
        <PanelHeader
          title="Energy balance"
          subtitle={`Demand against each supply path over the last ${range.replace("h", " hours").replace("d", " days")}.`}
          eyebrow="Time series"
        />
        <PanelBody className="pt-2">
          <ResourceBoundary resource={energy} loading={<LoadingState className="h-[300px]" />}>
            {(data) => (
              <TimeSeriesChart
                data={data}
                series={[
                  { key: "consumptionKw", label: "Site demand", color: CHART_COLORS.load },
                  { key: "solarKw", label: "Solar", color: CHART_COLORS.solar },
                  { key: "gridKw", label: "Grid (import +/export −)", color: CHART_COLORS.grid, type: "line" },
                  {
                    key: "batteryKw",
                    label: "Battery (discharge +/charge −)",
                    color: CHART_COLORS.battery,
                    type: "line",
                    dashed: true,
                  },
                ]}
                yLabel="kW"
                height={300}
                includeZero
                referenceLines={[{ y: DEMAND_CAP_KW, label: "Demand cap", color: CHART_COLORS.negative }]}
              />
            )}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      <div className="mt-3 grid grid-cols-1 items-start gap-3 xl:grid-cols-3">
        {/* Battery state */}
        <Panel>
          <PanelHeader
            title="Battery state of charge"
            subtitle="Charge cycles follow PV surplus and the evening peak window."
            eyebrow="Storage"
          />
          <PanelBody className="pt-2">
            <ResourceBoundary resource={energy} loading={<LoadingState className="h-[220px]" />}>
              {(data) => (
                <TimeSeriesChart
                  data={data}
                  series={[{ key: "batterySocPct", label: "State of charge", color: CHART_COLORS.battery }]}
                  unit="%"
                  yLabel="%"
                  height={220}
                  showLegend={false}
                  referenceLines={[{ y: 18, label: "Reserve floor", color: CHART_COLORS.negative }]}
                />
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>

        {/* Operating indicators */}
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Plant load operating state"
            subtitle="Production, thermal and utility assets with their live draw and utilisation."
            eyebrow="Operating indicators"
          />
          <PanelBody className="pt-3">
            <ResourceBoundary resource={assets} loading={<LoadingState variant="rows" rows={5} />}>
              {() => (
                <ul className="space-y-2">
                  {operatingAssets.map((a) => {
                    const Icon = assetIcon(a.id);
                    const running = a.powerKw > a.ratedPowerKw * 0.15;
                    return (
                      <li key={a.id}>
                        <Link
                          href={`/twins/${a.id}`}
                          className="flex items-center gap-3 rounded-lg border border-line bg-surface-inset px-3 py-2.5 transition-colors hover:border-line-strong hover:bg-surface-raised"
                        >
                          <Icon className="h-4 w-4 shrink-0 text-content-faint" aria-hidden />
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-3">
                              <span className="truncate text-[13px] font-medium text-content">{a.name}</span>
                              <span className="shrink-0 text-[13px] font-semibold tabular text-content">
                                {formatKw(a.powerKw, 0)}
                              </span>
                            </div>
                            <div className="mt-1.5 flex items-center gap-3">
                              <Meter value={a.utilisationPct} tone="info" className="flex-1" marker={90} />
                              <span className="shrink-0 text-2xs tabular text-content-faint">
                                {formatPct(a.utilisationPct, 0)}
                              </span>
                            </div>
                          </div>
                          <span className="flex w-20 shrink-0 items-center justify-end gap-1.5">
                            <StatusDot status={a.status} />
                            <span className="text-2xs text-content-muted">
                              {running ? "Running" : "Idle"}
                            </span>
                          </span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </ResourceBoundary>
          </PanelBody>
        </Panel>
      </div>

      {/* Status matrix + flow */}
      <Panel className="mt-3">
        <PanelHeader
          title="Asset status matrix"
          subtitle="All eight twins, colour-coded by health."
          eyebrow="Fleet"
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={assets} loading={<LoadingState className="h-24" />}>
            {(data) => <AssetStatusGrid assets={data} />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      <Panel className="mt-3">
        <PanelHeader
          title="Live energy flow"
          subtitle="Instantaneous power path from sources through the distribution bus to each load."
          eyebrow="System map"
          actions={
            <Link href="/energy-flow" className="text-2xs font-medium text-info hover:underline">
              Full map →
            </Link>
          }
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={flow} loading={<LoadingState className="h-[320px]" />}>
            {(data) => <EnergyFlow snapshot={data} compact />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      <p className="mt-3 text-2xs text-content-faint">
        Sampling clock: {now ? formatTime(new Date(now).toISOString()) : "—"}
      </p>
    </>
  );
}
