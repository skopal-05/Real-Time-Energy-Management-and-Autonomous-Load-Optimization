/** Minimal class-name joiner — avoids pulling in clsx for one helper. */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function sum(values: number[]): number {
  return values.reduce((acc, v) => acc + v, 0);
}

export function mean(values: number[]): number | null {
  if (values.length === 0) return null;
  return sum(values) / values.length;
}

/**
 * Deterministic pseudo-random generator (mulberry32).
 * Mock data must be identical on the server and the client, otherwise React
 * hydration mismatches. Every generator in `src/data` seeds from this.
 */
export function createRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Stable numeric hash of a string — used to seed per-asset generators. */
export function hashString(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function roundTo(value: number, digits = 1): number {
  const f = 10 ** digits;
  return Math.round(value * f) / f;
}

/** Sorts a copy of `rows` by `key`, tolerant of null values. */
export function sortRows<T>(rows: T[], key: keyof T, direction: "asc" | "desc"): T[] {
  const dir = direction === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    if (av === bv) return 0;
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
    return String(av).localeCompare(String(bv)) * dir;
  });
}
