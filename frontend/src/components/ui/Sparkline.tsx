import { cn } from "@/lib/utils";

interface SparklineProps {
  values: number[];
  color?: string;
  className?: string;
  width?: number;
  height?: number;
  /** Draws a soft area under the line. */
  filled?: boolean;
}

/**
 * Dependency-free trend line for asset cards. Renders nothing but a flat
 * baseline when there are fewer than two points, so it never throws on
 * missing data.
 */
export function Sparkline({
  values,
  color = "#38BDF8",
  className,
  width = 120,
  height = 32,
  filled = true,
}: SparklineProps) {
  const clean = values.filter((v) => Number.isFinite(v));
  if (clean.length < 2) {
    return (
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className={cn("h-full w-full", className)}
        preserveAspectRatio="none"
        aria-hidden
      >
        <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#2A3644" strokeWidth="1" strokeDasharray="3 3" />
      </svg>
    );
  }

  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const span = max - min || 1;
  const stepX = width / (clean.length - 1);
  const pad = 3;
  const usable = height - pad * 2;

  const points = clean.map((v, i) => {
    const x = i * stepX;
    const y = pad + usable - ((v - min) / span) * usable;
    return [x, y] as const;
  });

  const line = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  const gradientId = `spark-${color.replace("#", "")}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={cn("h-full w-full", className)}
      preserveAspectRatio="none"
      aria-hidden
    >
      {filled ? (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.28" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${gradientId})`} />
        </>
      ) : null}
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
