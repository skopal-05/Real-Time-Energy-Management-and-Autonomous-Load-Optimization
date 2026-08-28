"use client";

import { BrainCircuit, Boxes, Sliders, Target } from "lucide-react";
import type { SystemStatus } from "@/lib/types";
import { formatPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/InfoTip";

const OPT_LABEL: Record<SystemStatus["optimizationStatus"], { text: string; tone: string }> = {
  idle: { text: "Idle", tone: "text-content-faint" },
  running: { text: "Running", tone: "text-info" },
  converged: { text: "Converged", tone: "text-ok" },
  failed: { text: "Failed", tone: "text-crit" },
};

/** Four compact facts about the system that do not deserve a full KPI tile. */
export function SystemSummary({ status }: { status: SystemStatus }) {
  const opt = OPT_LABEL[status.optimizationStatus];

  const items = [
    {
      icon: Boxes,
      label: "Digital twins online",
      value: `${status.twinsOnline} / ${status.twinsTotal}`,
      tone: status.twinsOnline === status.twinsTotal ? "text-ok" : "text-warn",
      hint: "Number of asset twins currently reporting state to the platform.",
    },
    {
      icon: Target,
      label: "Operating objective",
      value: status.operatingModeLabel,
      tone: "text-content",
      hint: "The objective the decision agents are currently optimising for. It changes with the tariff band and plant conditions.",
    },
    {
      icon: Sliders,
      label: "Optimisation",
      value: opt.text,
      tone: opt.tone,
      hint: "State of the most recent Genetic Algorithm scheduling run.",
    },
    {
      icon: BrainCircuit,
      label: "Model confidence",
      value: status.aiConfidencePct === null ? "Not reported" : formatPct(status.aiConfidencePct, 0),
      tone: "text-content",
      hint: "Aggregate confidence reported by the active models. Shown as 'Not reported' when no model has published a confidence value.",
    },
  ];

  return (
    <ul className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <li key={item.label} className="bg-surface p-3.5">
            <div className="flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5 text-content-faint" aria-hidden />
              <span className="label-eyebrow">{item.label}</span>
              <InfoTip text={item.hint} />
            </div>
            <p className={cn("mt-1.5 text-base font-semibold tracking-tight", item.tone)}>{item.value}</p>
          </li>
        );
      })}
    </ul>
  );
}
