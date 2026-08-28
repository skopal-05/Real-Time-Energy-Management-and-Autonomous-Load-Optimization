"use client";

import { useState } from "react";
import { ChevronDown, CircleCheck, CircleSlash, Clock, Sparkles } from "lucide-react";
import { ASSET_REGISTRY } from "@/lib/constants";
import type { AIRecommendation, DecisionStatus, Priority } from "@/lib/types";
import { formatNumber, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/StatusBadge";

const PRIORITY_TONE: Record<Priority, "info" | "warn" | "crit" | "neutral"> = {
  low: "neutral",
  medium: "info",
  high: "warn",
  critical: "crit",
};

const STATUS_META: Record<DecisionStatus, { label: string; className: string }> = {
  pending: { label: "Awaiting operator", className: "text-warn" },
  accepted: { label: "Accepted", className: "text-info" },
  applied: { label: "Applied", className: "text-ok" },
  rejected: { label: "Rejected by constraint", className: "text-crit" },
  expired: { label: "Expired", className: "text-content-faint" },
};

const MODULE_LABEL: Record<AIRecommendation["sourceModule"], string> = {
  rules: "Rule engine",
  forecast: "Random Forest forecast",
  optimizer: "Genetic Algorithm",
  anomaly: "Isolation Forest",
};

interface RecommendationCardProps {
  recommendation: AIRecommendation;
  now: number;
  /** Collapsed by default on dense pages; expanded on the decision centre. */
  defaultOpen?: boolean;
  compact?: boolean;
}

/**
 * One agent decision, written so a non-specialist reviewer can follow it:
 * what was proposed, which rule fired, why, and what it is expected to do.
 */
export function RecommendationCard({
  recommendation: r,
  now,
  defaultOpen = false,
  compact = false,
}: RecommendationCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const status = STATUS_META[r.status];
  const StatusIcon =
    r.status === "applied" ? CircleCheck : r.status === "rejected" ? CircleSlash : Clock;

  return (
    <article className="panel overflow-hidden">
      <div className="flex items-start gap-3 p-3.5">
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-info/10 ring-1 ring-info/20">
          <Sparkles className="h-3.5 w-3.5 text-info" aria-hidden />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip tone={PRIORITY_TONE[r.priority]}>{r.priority} priority</Chip>
            <Chip>{r.agentName}</Chip>
            {!compact ? <Chip>{MODULE_LABEL[r.sourceModule]}</Chip> : null}
          </div>

          <h3 className="mt-1.5 text-[13px] font-semibold leading-snug text-content">{r.title}</h3>

          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-2xs text-content-faint">
            <span className={cn("inline-flex items-center gap-1 font-medium", status.className)}>
              <StatusIcon className="h-3 w-3" aria-hidden />
              {status.label}
            </span>
            <span>{formatRelative(r.createdAt, now)}</span>
            <span className="truncate">
              {r.targetAssets.map((a) => ASSET_REGISTRY[a].shortName).join(" · ")}
            </span>
          </div>

          {/* Expected impact */}
          {r.expectedImpact.length > 0 ? (
            <ul className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1">
              {r.expectedImpact.map((im) => (
                <li key={im.label}>
                  <p className="text-2xs text-content-faint">{im.label}</p>
                  <p className="text-xs font-semibold tabular text-content">
                    {im.value === null ? (
                      <span className="text-content-faint">Not quantified</span>
                    ) : (
                      `${formatNumber(im.value, im.value % 1 === 0 ? 0 : 1)} ${im.unit}`
                    )}
                  </p>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="shrink-0 rounded-md p-1 text-content-faint transition-colors hover:text-content"
          aria-label={open ? "Hide explanation" : "Why this decision?"}
        >
          <ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} aria-hidden />
        </button>
      </div>

      {open ? (
        <div className="animate-fade-up border-t border-line bg-surface-inset px-3.5 py-3">
          <p className="label-eyebrow mb-1">Why this decision?</p>
          <p className="text-xs leading-relaxed text-content-muted">{r.rationale}</p>
          <p className="label-eyebrow mb-1 mt-3">Rule triggered</p>
          <code className="block overflow-x-auto rounded-md border border-line bg-surface p-2 font-mono text-2xs leading-relaxed text-info">
            {r.ruleTriggered}
          </code>
        </div>
      ) : null}
    </article>
  );
}
