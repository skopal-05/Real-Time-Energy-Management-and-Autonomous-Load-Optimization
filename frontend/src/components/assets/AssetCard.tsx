"use client";

import Link from "next/link";
import { AlertTriangle, ArrowUpRight } from "lucide-react";
import type { Asset } from "@/lib/types";
import { formatKw, formatNumber, formatPct, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Meter } from "@/components/ui/Meter";
import { Sparkline } from "@/components/ui/Sparkline";
import { assetAccent, assetIcon } from "./assetIcon";

interface AssetCardProps {
  asset: Asset;
  /** Reference clock for relative timestamps; keeps SSR deterministic. */
  now: number;
  className?: string;
}

/**
 * Power means something different per asset role, so the caption is derived
 * from the role rather than the sign alone: a grid connection "imports", a
 * battery "discharges", a line "consumes".
 */
function powerCaption(asset: Asset): { label: string; supplying: boolean } {
  const p = asset.powerKw;
  switch (asset.role) {
    case "producer":
      return { label: Math.abs(p) > 0.5 ? "Generating" : "Not generating", supplying: Math.abs(p) > 0.5 };
    case "storage":
      return p > 1
        ? { label: "Discharging", supplying: true }
        : p < -1
          ? { label: "Charging", supplying: false }
          : { label: "Idle", supplying: false };
    case "bidirectional":
      return p >= 0
        ? { label: "Importing", supplying: true }
        : { label: "Exporting", supplying: false };
    default:
      return { label: "Consuming", supplying: false };
  }
}

/** Compact digital-twin summary card used on the asset overview grid. */
export function AssetCard({ asset, now, className }: AssetCardProps) {
  const Icon = assetIcon(asset.id);
  const accent = assetAccent(asset.id);
  const power = powerCaption(asset);

  return (
    <Link
      href={`/twins/${asset.id}`}
      className={cn(
        "panel panel-hover group flex flex-col gap-3 p-4 transition-transform focus-visible:ring-2",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2.5">
          <span
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ring-1"
            style={{ backgroundColor: `${accent}14`, boxShadow: `inset 0 0 0 1px ${accent}33` }}
          >
            <Icon className="h-4 w-4" style={{ color: accent }} aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold leading-tight text-content">{asset.name}</p>
            <p className="truncate text-2xs text-content-faint">{asset.location}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {asset.activeAlerts > 0 ? (
            <span
              className="inline-flex items-center gap-0.5 rounded border border-warn/30 bg-warn/10 px-1 py-0.5 text-2xs font-medium text-warn"
              title={`${asset.activeAlerts} active alert${asset.activeAlerts > 1 ? "s" : ""}`}
            >
              <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
              {asset.activeAlerts}
            </span>
          ) : null}
          <StatusBadge status={asset.status} />
        </div>
      </div>

      {/* Headline metric + power */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="label-eyebrow">{asset.headline.label}</p>
          <p className="mt-0.5 text-lg font-semibold tabular leading-tight text-content">
            {formatNumber(asset.headline.value, asset.headline.unit === "" ? 2 : 1)}
            <span className="ml-1 text-2xs font-medium text-content-muted">{asset.headline.unit}</span>
          </p>
        </div>
        <div>
          <p className="label-eyebrow">{power.label}</p>
          <p
            className="mt-0.5 text-lg font-semibold tabular leading-tight"
            style={{ color: asset.role === "producer" && power.supplying ? "#22C55E" : "#E7ECF3" }}
          >
            {formatKw(Math.abs(asset.powerKw), 0)}
          </p>
        </div>
      </div>

      <div className="h-9">
        <Sparkline values={asset.sparkline} color={accent} height={36} />
      </div>

      <div className="space-y-1.5">
        <Meter
          value={asset.efficiencyPct}
          label="Efficiency"
          valueLabel={asset.efficiencyPct === null ? "Not applicable" : formatPct(asset.efficiencyPct)}
          tone={
            asset.efficiencyPct === null
              ? "neutral"
              : asset.efficiencyPct > 85
                ? "ok"
                : asset.efficiencyPct > 70
                  ? "warn"
                  : "crit"
          }
        />
        <Meter
          value={asset.utilisationPct}
          label="Utilisation of rated capacity"
          valueLabel={formatPct(asset.utilisationPct)}
          tone="info"
          marker={90}
        />
      </div>

      <div className="mt-auto flex items-center justify-between border-t border-line-soft pt-2.5">
        <span className="text-2xs text-content-faint">
          Updated {formatRelative(asset.lastUpdated, now)}
        </span>
        <span className="inline-flex items-center gap-1 text-2xs font-medium text-content-muted transition-colors group-hover:text-info">
          View details
          <ArrowUpRight className="h-3 w-3" aria-hidden />
        </span>
      </div>
    </Link>
  );
}
