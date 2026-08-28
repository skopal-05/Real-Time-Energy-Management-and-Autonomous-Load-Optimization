"use client";

import Link from "next/link";
import type { Asset } from "@/lib/types";
import { HEALTH_STYLES } from "@/lib/constants";
import { formatKw, formatPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { StatusDot } from "@/components/ui/StatusBadge";
import { assetIcon } from "./assetIcon";

interface AssetStatusGridProps {
  assets: Asset[];
  className?: string;
}

/**
 * Dense status matrix of every digital twin. Designed to be readable from the
 * back of a room: colour, icon and value only, no decoration.
 */
export function AssetStatusGrid({ assets, className }: AssetStatusGridProps) {
  return (
    <ul className={cn("grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8", className)}>
      {assets.map((asset) => {
        const Icon = assetIcon(asset.id);
        const style = HEALTH_STYLES[asset.status];
        return (
          <li key={asset.id}>
            <Link
              href={`/twins/${asset.id}`}
              className={cn(
                "flex h-full flex-col gap-1.5 rounded-lg border bg-surface-inset p-2.5 transition-colors hover:bg-surface-raised",
                style.border,
              )}
            >
              <div className="flex items-center justify-between gap-1">
                <Icon className={cn("h-3.5 w-3.5", style.fg)} aria-hidden />
                <StatusDot status={asset.status} />
              </div>
              <p className="truncate text-2xs font-medium leading-tight text-content">{asset.shortName}</p>
              <p className="text-xs font-semibold tabular leading-tight text-content">
                {formatKw(Math.abs(asset.powerKw), 0)}
              </p>
              <p className="text-2xs tabular text-content-faint">
                {asset.efficiencyPct === null ? "—" : `${formatPct(asset.efficiencyPct, 0)} eff.`}
              </p>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
