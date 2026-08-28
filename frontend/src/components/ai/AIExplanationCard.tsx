"use client";

import { Lightbulb } from "lucide-react";
import type { Explanation } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/StatusBadge";

interface AIExplanationCardProps {
  explanation: Explanation;
  className?: string;
  /** Hides the model metadata row when the page already shows it. */
  compact?: boolean;
}

/**
 * Plain-language summary of a SHAP explanation: base value, model output, and
 * the sentence a viva examiner actually wants to hear.
 */
export function AIExplanationCard({ explanation: x, className, compact = false }: AIExplanationCardProps) {
  const total = x.prediction - x.baseValue;
  const digits = x.unit === "" ? 3 : 1;

  return (
    <div className={cn("panel p-4", className)}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-forecast/10 ring-1 ring-accent-forecast/25">
          <Lightbulb className="h-3.5 w-3.5 text-accent-forecast" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          {!compact ? (
            <div className="mb-2 flex flex-wrap items-center gap-1.5">
              <Chip tone="info">{x.algorithm}</Chip>
              <Chip>{x.modelName}</Chip>
              <Chip>{x.assetName}</Chip>
            </div>
          ) : null}

          <p className="text-[13px] leading-relaxed text-content-muted">{x.narrative}</p>

          <dl className="mt-3 grid grid-cols-3 gap-3 border-t border-line-soft pt-3">
            <div>
              <dt className="label-eyebrow">Base value E[f(x)]</dt>
              <dd className="mt-0.5 text-sm font-semibold tabular text-content-muted">
                {formatNumber(x.baseValue, digits)} {x.unit}
              </dd>
            </div>
            <div>
              <dt className="label-eyebrow">Sum of contributions</dt>
              <dd
                className={cn(
                  "mt-0.5 text-sm font-semibold tabular",
                  total >= 0 ? "text-ok" : "text-crit",
                )}
              >
                {total >= 0 ? "+" : ""}
                {formatNumber(total, digits)} {x.unit}
              </dd>
            </div>
            <div>
              <dt className="label-eyebrow">Model output f(x)</dt>
              <dd className="mt-0.5 text-sm font-semibold tabular text-content">
                {formatNumber(x.prediction, digits)} {x.unit}
              </dd>
            </div>
          </dl>

          <p className="mt-2.5 text-2xs text-content-faint">
            {x.target} · explained {formatDateTime(x.generatedAt)}
          </p>
        </div>
      </div>
    </div>
  );
}
