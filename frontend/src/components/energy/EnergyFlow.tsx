"use client";

import { useMemo } from "react";
import Link from "next/link";
import { HEALTH_STYLES } from "@/lib/constants";
import type { EnergyFlowSnapshot } from "@/lib/types";
import { formatKw } from "@/lib/format";
import { cn } from "@/lib/utils";

interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

const VB = { w: 1040, h: 470 };

/** Fixed layout: sources left, storage and bus centre, consumers right. */
const LAYOUT: Record<string, Box> = {
  solar: { x: 24, y: 40, w: 168, h: 72 },
  battery: { x: 24, y: 196, w: 168, h: 78 },
  grid: { x: 24, y: 356, w: 168, h: 72 },
  bus: { x: 396, y: 178, w: 208, h: 114 },
  "line-a": { x: 812, y: 22, w: 204, h: 66 },
  "line-b": { x: 812, y: 106, w: 204, h: 66 },
  boiler: { x: 812, y: 190, w: 204, h: 66 },
  compressor: { x: 812, y: 274, w: 204, h: 66 },
  hvac: { x: 812, y: 358, w: 204, h: 66 },
};

function anchor(box: Box, side: "left" | "right"): [number, number] {
  return side === "right" ? [box.x + box.w, box.y + box.h / 2] : [box.x, box.y + box.h / 2];
}

/** Smooth S-curve between two boxes, always leaving right and entering left. */
function path(from: Box, to: Box): string {
  const [x1, y1] = anchor(from, "right");
  const [x2, y2] = anchor(to, "left");
  const dx = Math.max(60, (x2 - x1) / 2);
  return `M ${x1},${y1} C ${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`;
}

interface EnergyFlowProps {
  snapshot: EnergyFlowSnapshot;
  className?: string;
  /** Renders node labels smaller for embedding in a half-width panel. */
  compact?: boolean;
}

/**
 * System-level energy flow map.
 *
 * Line thickness encodes power, animated dashes encode direction, and dormant
 * paths stay visible but static so the topology is always legible.
 */
export function EnergyFlow({ snapshot, className, compact = false }: EnergyFlowProps) {
  const maxPower = useMemo(
    () => Math.max(1, ...snapshot.links.map((l) => Math.abs(l.powerKw))),
    [snapshot.links],
  );

  const nodeById = useMemo(
    () => Object.fromEntries(snapshot.nodes.map((n) => [n.id, n])),
    [snapshot.nodes],
  );

  return (
    <div className={cn("w-full", className)}>
      <svg
        viewBox={`0 0 ${VB.w} ${VB.h}`}
        className="h-auto w-full"
        role="img"
        aria-label="Energy flow from generation and storage through the main bus to plant loads"
      >
        <defs>
          <filter id="flow-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Links */}
        <g>
          {snapshot.links.map((link) => {
            const from = LAYOUT[link.from];
            const to = LAYOUT[link.to];
            if (!from || !to) return null;
            const d = link.from === "bus" && link.to === "grid" ? path(LAYOUT.grid, LAYOUT.bus) : path(from, to);
            const width = link.active ? 1.4 + (Math.abs(link.powerKw) / maxPower) * 4.6 : 1;

            return (
              <g key={`${link.from}-${link.to}`}>
                <path
                  d={d}
                  fill="none"
                  stroke={link.active ? link.colorToken : "#1E2733"}
                  strokeOpacity={link.active ? 0.24 : 0.9}
                  strokeWidth={width}
                  strokeLinecap="round"
                />
                {link.active ? (
                  <path
                    d={d}
                    fill="none"
                    stroke={link.colorToken}
                    strokeWidth={width}
                    strokeLinecap="round"
                    strokeDasharray="7 9"
                    className="animate-flow-dash"
                    filter="url(#flow-glow)"
                    style={
                      link.from === "bus" && link.to === "grid"
                        ? { animationDirection: "reverse" }
                        : undefined
                    }
                  />
                ) : null}
              </g>
            );
          })}
        </g>

        {/* Link labels */}
        <g>
          {snapshot.links
            .filter((l) => l.active && Math.abs(l.powerKw) >= 8)
            .map((link) => {
              const from = LAYOUT[link.from];
              const to = LAYOUT[link.to];
              if (!from || !to) return null;
              const [x1, y1] = anchor(from, "right");
              const [x2, y2] = anchor(to, "left");
              const mx = (x1 + x2) / 2;
              const my = (y1 + y2) / 2 - 8;
              return (
                <text
                  key={`label-${link.from}-${link.to}`}
                  x={mx}
                  y={my}
                  textAnchor="middle"
                  className="fill-current"
                  style={{ fill: link.colorToken, fontSize: 11, fontWeight: 600 }}
                >
                  {Math.round(Math.abs(link.powerKw))} kW
                </text>
              );
            })}
        </g>

        {/* Nodes */}
        <g>
          {Object.entries(LAYOUT).map(([id, box]) => {
            const node = nodeById[id];
            if (!node) return null;
            const style = HEALTH_STYLES[node.status];
            const isHub = node.kind === "hub";

            return (
              <g key={id}>
                <rect
                  x={box.x}
                  y={box.y}
                  width={box.w}
                  height={box.h}
                  rx={12}
                  fill={isHub ? "#121822" : "#0D1117"}
                  stroke={isHub ? "#2A3644" : style.hex}
                  strokeOpacity={isHub ? 1 : 0.45}
                  strokeWidth={1.2}
                />
                <circle cx={box.x + 13} cy={box.y + 15} r={3} fill={style.hex} />
                <text
                  x={box.x + 24}
                  y={box.y + 19}
                  style={{ fill: "#93A1B5", fontSize: compact ? 10 : 11, fontWeight: 500 }}
                >
                  {node.label}
                </text>
                <text
                  x={box.x + 13}
                  y={box.y + (isHub ? 62 : 44)}
                  style={{
                    fill: "#E7ECF3",
                    fontSize: isHub ? 22 : compact ? 15 : 17,
                    fontWeight: 600,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {formatKw(Math.abs(node.powerKw), 0)}
                </text>
                {node.detail ? (
                  <text
                    x={box.x + 13}
                    y={box.y + (isHub ? 84 : 60)}
                    style={{ fill: "#64748B", fontSize: 10 }}
                  >
                    {node.detail}
                  </text>
                ) : null}
              </g>
            );
          })}
        </g>

        {/* Column captions */}
        <text x={24} y={22} style={{ fill: "#64748B", fontSize: 10, letterSpacing: 1 }}>
          SOURCES &amp; STORAGE
        </text>
        <text x={396} y={160} style={{ fill: "#64748B", fontSize: 10, letterSpacing: 1 }}>
          DISTRIBUTION
        </text>
        <text x={812} y={12} style={{ fill: "#64748B", fontSize: 10, letterSpacing: 1 }}>
          PLANT LOADS
        </text>
      </svg>

      {/* Accessible / clickable node list mirroring the diagram */}
      <ul className="mt-3 grid grid-cols-2 gap-1.5 sm:grid-cols-3 lg:grid-cols-5">
        {snapshot.nodes
          .filter((n) => n.assetId)
          .map((n) => (
            <li key={n.id}>
              <Link
                href={`/twins/${n.assetId}`}
                className="flex items-center justify-between gap-2 rounded-md border border-line bg-surface-inset px-2 py-1.5 text-2xs transition-colors hover:border-line-strong hover:bg-surface-raised"
              >
                <span className="truncate text-content-muted">{n.label}</span>
                <span className="shrink-0 tabular text-content">{formatKw(Math.abs(n.powerKw), 0)}</span>
              </Link>
            </li>
          ))}
      </ul>
    </div>
  );
}
