"use client";

import Link from "next/link";
import {
  AlertTriangle,
  BrainCircuit,
  Radar,
  Settings2,
  Sliders,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { ASSET_REGISTRY, SEVERITY_STYLES } from "@/lib/constants";
import type { EventKind, SystemEvent } from "@/lib/types";
import { formatRelative } from "@/lib/format";
import { EmptyState } from "@/components/ui/States";

const KIND_ICON: Record<EventKind, LucideIcon> = {
  alert: AlertTriangle,
  anomaly: Radar,
  decision: BrainCircuit,
  optimization: Sliders,
  forecast: TrendingUp,
  system: Settings2,
};

const KIND_HREF: Record<EventKind, string> = {
  alert: "/anomalies",
  anomaly: "/anomalies",
  decision: "/decisions",
  optimization: "/optimization",
  forecast: "/forecasting",
  system: "/monitoring",
};

/** Chronological log of what the platform has done and detected. */
export function EventFeed({
  events,
  now,
  limit = 8,
}: {
  events: SystemEvent[];
  now: number;
  limit?: number;
}) {
  if (events.length === 0) {
    return <EmptyState title="No events recorded" description="Nothing has been logged in this session yet." />;
  }

  return (
    <ul className="divide-y divide-line-soft">
      {events.slice(0, limit).map((e) => {
        const Icon = KIND_ICON[e.kind];
        const color = e.severity === "info" ? "#64748B" : SEVERITY_STYLES[e.severity].hex;
        return (
          <li key={e.id}>
            <Link
              href={KIND_HREF[e.kind]}
              className="flex items-start gap-3 px-4 py-2.5 transition-colors hover:bg-surface-raised sm:px-5"
            >
              <span
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
                style={{ backgroundColor: `${color}1A` }}
              >
                <Icon className="h-3 w-3" style={{ color }} aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium leading-snug text-content">{e.title}</p>
                <p className="mt-0.5 line-clamp-2 text-xs leading-relaxed text-content-muted">{e.detail}</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="whitespace-nowrap text-2xs tabular text-content-faint">
                  {formatRelative(e.timestamp, now)}
                </p>
                {e.assetId ? (
                  <p className="mt-0.5 whitespace-nowrap text-2xs text-content-faint">
                    {ASSET_REGISTRY[e.assetId].shortName}
                  </p>
                ) : null}
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
