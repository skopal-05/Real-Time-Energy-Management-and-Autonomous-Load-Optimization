"use client";

import { useAppState } from "@/providers/AppStateProvider";

/**
 * A clock that only advances on refresh ticks.
 *
 * Relative timestamps ("4 min ago") must not be computed during server
 * rendering, or the markup differs from the client's. Returning 0 until the
 * client has mounted keeps rendering deterministic; every consumer sits behind
 * a loading state until then anyway.
 */
export function useNow(): number {
  const { lastRefreshedAt } = useAppState();
  return lastRefreshedAt ?? 0;
}
