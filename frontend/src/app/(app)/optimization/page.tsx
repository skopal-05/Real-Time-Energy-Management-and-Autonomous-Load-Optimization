"use client";

import { useCallback } from "react";
import { CheckCircle2, CircleDot, Dna, IndianRupee, TrendingDown, XCircle } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { DEMAND_CAP_KW } from "@/lib/constants";
import type { OptimizationResult } from "@/lib/types";
import { formatCurrency, formatDateTime, formatKw, formatKwh, formatNumber, pctChange } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { MetricCard } from "@/components/ui/MetricCard";
import { Meter } from "@/components/ui/Meter";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { LoadingState } from "@/components/ui/States";
import { Chip } from "@/components/ui/StatusBadge";
import { DataOriginBadge } from "@/components/ui/DataOriginBadge";
import { OptimizationComparison } from "@/components/charts/OptimizationComparison";
import { ConvergenceChart } from "@/components/charts/ConvergenceChart";

const STATUS_META: Record<OptimizationResult["status"], { label: string; tone: string; icon: typeof CircleDot }> = {
  idle: { label: "Idle", tone: "text-content-faint", icon: CircleDot },
  running: { label: "Running", tone: "text-info", icon: CircleDot },
  converged: { label: "Converged", tone: "text-ok", icon: CheckCircle2 },
  failed: { label: "Failed", tone: "text-crit", icon: XCircle },
};

export default function OptimizationPage() {
  const ds = getDataSource();
  const now = useNow();
  const opt = useResource<OptimizationResult>(useCallback(() => ds.getOptimization(), [ds]));

  const d = opt.data;
  const costDelta = d ? pctChange(d.cost.baseline, d.cost.optimised) : null;
  const peakDelta = d ? pctChange(d.peakDemand.baselineKw, d.peakDemand.optimisedKw) : null;
  const savings =
    d && d.cost.baseline !== null && d.cost.optimised !== null ? d.cost.baseline - d.cost.optimised : null;

  return (
    <>
      <PageHeader
        title="Optimisation Centre"
        description="A Genetic Algorithm searches load schedules over a 24-hour horizon, minimising energy cost while penalising grid peaks and respecting the hard process constraints listed below. Figures compare the optimiser's proposal against the unmodified baseline schedule."
        module="Genetic Algorithm"
        origin={opt.origin}
      />

      {opt.origin === "simulated" ? (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-warn/25 bg-warn/[0.06] px-3 py-2.5">
          <DataOriginBadge origin="simulated" withHint={false} className="mt-0.5 shrink-0" />
          <p className="text-2xs leading-relaxed text-warn/90">
            The cost and peak figures on this page are produced by the demo scenario and its tariff model.
            They demonstrate the comparison the optimiser makes — they are not a measured saving from a real
            deployment. Connect the backend to replace them with values from an actual GA run.
          </p>
        </div>
      ) : null}

      <ResourceBoundary resource={opt} loading={<LoadingState variant="cards" rows={4} />}>
        {(data) => {
          const meta = STATUS_META[data.status];
          const StatusIcon = meta.icon;
          return (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  label="Baseline cost"
                  value={formatCurrency(data.cost.baseline)}
                  tone="neutral"
                  icon={<IndianRupee className="h-4 w-4" />}
                  caption="24-hour horizon at the current tariff schedule"
                  hint="Cost of running the unmodified load schedule through the tariff bands."
                />
                <MetricCard
                  label="Optimised cost"
                  value={formatCurrency(data.cost.optimised)}
                  tone="ok"
                  icon={<TrendingDown className="h-4 w-4" />}
                  caption="Best schedule found by the GA"
                  delta={
                    costDelta === null
                      ? undefined
                      : {
                          value: `${Math.abs(costDelta).toFixed(1)} %`,
                          trend: costDelta < 0 ? "down" : "up",
                          positiveIsGood: false,
                        }
                  }
                />
                <MetricCard
                  label="Modelled cost difference"
                  value={savings === null ? "—" : formatCurrency(Math.abs(savings))}
                  tone={savings !== null && savings > 0 ? "ok" : "neutral"}
                  caption={
                    savings === null
                      ? "Not available"
                      : `${savings > 0 ? "Lower" : "Higher"} than baseline over the horizon`
                  }
                  hint="The difference between the two schedules under the same tariff model. It is a modelled figure, not a metered saving."
                />
                <MetricCard
                  label="Peak demand"
                  value={formatKw(data.peakDemand.optimisedKw, 0)}
                  tone={
                    data.peakDemand.optimisedKw !== null && data.peakDemand.optimisedKw > DEMAND_CAP_KW
                      ? "crit"
                      : "ok"
                  }
                  caption={`Baseline ${formatKw(data.peakDemand.baselineKw, 0)} · cap ${DEMAND_CAP_KW} kW`}
                  delta={
                    peakDelta === null
                      ? undefined
                      : {
                          value: `${Math.abs(peakDelta).toFixed(1)} %`,
                          trend: peakDelta < 0 ? "down" : "up",
                          positiveIsGood: false,
                        }
                  }
                  footer={
                    <Meter
                      value={
                        data.peakDemand.optimisedKw === null
                          ? null
                          : (data.peakDemand.optimisedKw / DEMAND_CAP_KW) * 100
                      }
                      tone="info"
                      marker={100}
                    />
                  }
                />
              </div>

              {/* Run status */}
              <Panel className="mt-3">
                <PanelHeader
                  title="Optimisation run"
                  subtitle={data.algorithm}
                  eyebrow="Module 5 · Optimisation"
                  actions={
                    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", meta.tone)}>
                      <StatusIcon className="h-3.5 w-3.5" aria-hidden />
                      {meta.label}
                    </span>
                  }
                />
                <PanelBody className="pt-3">
                  <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6">
                    {[
                      ["Run id", data.runId],
                      ["Generations", String(data.generations)],
                      ["Population", String(data.populationSize)],
                      ["Started", formatDateTime(data.startedAt)],
                      ["Finished", data.finishedAt ? formatDateTime(data.finishedAt) : "—"],
                      [
                        "Energy over horizon",
                        `${formatKwh(data.energyKwh.optimised)} vs ${formatKwh(data.energyKwh.baseline)}`,
                      ],
                    ].map(([k, v]) => (
                      <div key={k} className="min-w-0">
                        <dt className="label-eyebrow">{k}</dt>
                        <dd className="mt-0.5 truncate text-xs font-medium text-content" title={v}>
                          {v}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </PanelBody>
              </Panel>

              {/* Comparison */}
              <Panel className="mt-3">
                <PanelHeader
                  title="Load schedule · baseline vs optimised"
                  subtitle="The optimiser sheds deferrable load from demand peaks and the peak tariff band, then recovers exactly the same energy in off-peak hours."
                  eyebrow="Before / after"
                />
                <PanelBody className="pt-2">
                  <OptimizationComparison
                    schedule={data.schedule}
                    demandCapKw={DEMAND_CAP_KW}
                    nowMs={now || undefined}
                    height={320}
                  />
                </PanelBody>
              </Panel>

              <div className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-2">
                {/* Objective */}
                <Panel>
                  <PanelHeader
                    title="Objective function"
                    subtitle={data.objective.summary}
                    eyebrow="What is being minimised"
                    hint="The GA evaluates each candidate schedule against this weighted sum. Lower is better."
                  />
                  <PanelBody className="space-y-3 pt-3">
                    <ul className="space-y-2.5">
                      {data.objective.terms.map((t) => (
                        <li key={t.label}>
                          <div className="flex items-baseline justify-between gap-3">
                            <span className="text-[13px] font-medium text-content">{t.label}</span>
                            <span className="text-xs tabular text-content-muted">
                              weight {formatNumber(t.weight, 2)}
                            </span>
                          </div>
                          <p className="mt-0.5 text-2xs text-content-faint">{t.description}</p>
                          <Meter value={t.weight * 100} tone="info" className="mt-1.5" />
                        </li>
                      ))}
                    </ul>
                    <div className="flex items-center gap-2 border-t border-line-soft pt-3">
                      <Dna className="h-3.5 w-3.5 text-content-faint" aria-hidden />
                      <p className="text-2xs text-content-faint">
                        Tournament selection · two-point crossover · adaptive mutation · elitism of 2
                      </p>
                    </div>
                  </PanelBody>
                </Panel>

                {/* Convergence */}
                <Panel>
                  <PanelHeader
                    title="Search convergence"
                    subtitle="Best and mean population cost per generation."
                    eyebrow="How the GA got there"
                  />
                  <PanelBody className="pt-2">
                    <ConvergenceChart convergence={data.convergence} height={240} />
                    <p className="mt-2 text-2xs leading-relaxed text-content-faint">
                      The best individual improves quickly and then flattens, which is the signal used to stop
                      the run. The mean tracking above the best line shows the population still holding
                      diversity rather than collapsing early.
                    </p>
                  </PanelBody>
                </Panel>
              </div>

              {/* Constraints */}
              <Panel className="mt-3">
                <PanelHeader
                  title="Constraint satisfaction"
                  subtitle="Every candidate schedule must satisfy all of these. A violated constraint invalidates the individual."
                  eyebrow="Feasibility"
                />
                <PanelBody className="pt-3">
                  <ul className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {data.constraints.map((c) => (
                      <li
                        key={c.id}
                        className={cn(
                          "flex items-start gap-2.5 rounded-lg border bg-surface-inset p-3",
                          c.satisfied ? "border-line" : "border-crit/40",
                        )}
                      >
                        {c.satisfied ? (
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-ok" aria-hidden />
                        ) : (
                          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-crit" aria-hidden />
                        )}
                        <div className="min-w-0">
                          <p className="text-[13px] font-medium text-content">{c.label}</p>
                          <code className="mt-1 block overflow-x-auto font-mono text-2xs text-info">
                            {c.expression}
                          </code>
                          <p className="mt-1 text-2xs text-content-faint">
                            Margin: <span className="tabular">{c.slack}</span>
                          </p>
                        </div>
                        <Chip tone={c.satisfied ? "ok" : "crit"} className="ml-auto shrink-0">
                          {c.satisfied ? "Satisfied" : "Violated"}
                        </Chip>
                      </li>
                    ))}
                  </ul>
                </PanelBody>
              </Panel>
            </>
          );
        }}
      </ResourceBoundary>
    </>
  );
}
