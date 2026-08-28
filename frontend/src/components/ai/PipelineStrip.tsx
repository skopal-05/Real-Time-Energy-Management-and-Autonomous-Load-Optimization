"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { PIPELINE_STEPS } from "@/lib/constants";
import type { PipelineStage } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATE_STYLE: Record<PipelineStage["state"], { dot: string; text: string; label: string }> = {
  ok: { dot: "bg-ok", text: "text-ok", label: "Nominal" },
  degraded: { dot: "bg-warn", text: "text-warn", label: "Attention" },
  down: { dot: "bg-crit", text: "text-crit", label: "Down" },
  idle: { dot: "bg-idle", text: "text-content-faint", label: "Idle" },
};

interface PipelineStripProps {
  stages: PipelineStage[];
  className?: string;
}

/**
 * The project's story in one row: sensors → twin → forecast → decisions →
 * optimisation → anomaly detection → explainability. Each step links to the
 * page that shows that module's output.
 */
export function PipelineStrip({ stages, className }: PipelineStripProps) {
  const stageById = Object.fromEntries(stages.map((s) => [s.id, s]));

  return (
    <ol
      className={cn(
        "grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-4 xl:grid-cols-7",
        className,
      )}
    >
      {PIPELINE_STEPS.map((step, i) => {
        const stage = stageById[step.id];
        const state = stage ? STATE_STYLE[stage.state] : STATE_STYLE.idle;
        return (
          <li key={step.id}>
            <Link
              href={step.href}
              className="group flex h-full flex-col rounded-lg border border-line bg-surface-inset px-3 py-2.5 transition-colors hover:border-line-strong hover:bg-surface-raised"
            >
              <div className="flex items-center gap-1.5">
                <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", state.dot)} aria-hidden />
                <span className="text-2xs uppercase tracking-wider text-content-faint">
                  Step {i + 1}
                </span>
                {i < PIPELINE_STEPS.length - 1 ? (
                  <ChevronRight
                    className="ml-auto h-3.5 w-3.5 shrink-0 text-content-faint/60"
                    aria-hidden
                  />
                ) : null}
              </div>
              <p className="mt-1.5 text-xs font-semibold leading-tight text-content transition-colors group-hover:text-info">
                {step.label}
              </p>
              <p className="mt-0.5 truncate text-2xs text-content-faint">{step.module}</p>
              <p className={cn("mt-auto pt-1.5 text-2xs font-medium leading-snug", state.text)}>
                {stage?.detail ?? state.label}
              </p>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
