import { CURRENCY_SYMBOL } from "./constants";

const NBSP = " ";

/** Renders a nullable number, never printing "NaN" or "null" in the UI. */
export function formatNumber(
  value: number | null | undefined,
  digits = 1,
  fallback = "—",
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback;
  return value.toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatUnit(
  value: number | null | undefined,
  unit: string,
  digits = 1,
  fallback = "—",
): string {
  const n = formatNumber(value, digits, fallback);
  return n === fallback ? fallback : `${n}${NBSP}${unit}`;
}

export function formatKw(value: number | null | undefined, digits = 1): string {
  return formatUnit(value, "kW", digits);
}

export function formatKwh(value: number | null | undefined, digits = 0): string {
  if (value !== null && value !== undefined && Math.abs(value) >= 1000) {
    return formatUnit(value / 1000, "MWh", 2);
  }
  return formatUnit(value, "kWh", digits);
}

export function formatPct(value: number | null | undefined, digits = 1): string {
  return formatUnit(value, "%", digits);
}

export function formatCurrency(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${CURRENCY_SYMBOL}${value.toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

export function formatSigned(value: number | null | undefined, unit: string, digits = 1): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}${NBSP}${unit}`;
}

/* ------------------------------------------------------------------ */
/* Time                                                                 */
/* ------------------------------------------------------------------ */

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return `${d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" })} · ${d.toLocaleTimeString(
    "en-GB",
    { hour: "2-digit", minute: "2-digit" },
  )}`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/** "3 min ago" — relative to a caller-supplied `now` so SSR stays deterministic. */
export function formatRelative(iso: string | null | undefined, now: number): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const deltaSec = Math.round((now - t) / 1000);
  if (deltaSec < 5) return "just now";
  if (deltaSec < 60) return `${deltaSec}s ago`;
  const min = Math.round(deltaSec / 60);
  if (min < 60) return `${min} min ago`;
  const hrs = Math.round(min / 60);
  if (hrs < 24) return `${hrs} h ago`;
  return `${Math.round(hrs / 24)} d ago`;
}

export function formatDuration(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined || !Number.isFinite(minutes)) return "—";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

/** Percentage change between two values, null-safe. */
export function pctChange(from: number | null, to: number | null): number | null {
  if (from === null || to === null || !Number.isFinite(from) || !Number.isFinite(to) || from === 0) {
    return null;
  }
  return ((to - from) / Math.abs(from)) * 100;
}
