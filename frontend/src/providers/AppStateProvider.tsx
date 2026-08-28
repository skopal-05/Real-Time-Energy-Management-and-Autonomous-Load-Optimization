"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { apiConfig, isLiveMode, subscribe } from "@/services";

interface AppState {
  /** True while the simulated stream is driving periodic refreshes. */
  streaming: boolean;
  setStreaming: (value: boolean) => void;
  /** Increments on every refresh tick; resources depend on it. */
  tick: number;
  /** Epoch ms of the last tick — null until the client has mounted. */
  lastRefreshedAt: number | null;
  refreshNow: () => void;
  /** True when the app is serving the deterministic demo scenario. */
  isDemoData: boolean;
  sourceName: string;
  pollIntervalMs: number;
}

const AppStateContext = createContext<AppState | null>(null);

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [streaming, setStreaming] = useState(true);
  const [tick, setTick] = useState(0);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<number | null>(null);
  const mounted = useRef(false);

  const refreshNow = useCallback(() => {
    setTick((t) => t + 1);
    setLastRefreshedAt(Date.now());
  }, []);

  // First paint on the client establishes the baseline timestamp. Doing this in
  // an effect (rather than during render) keeps server and client markup equal.
  useEffect(() => {
    if (mounted.current) return;
    mounted.current = true;
    setLastRefreshedAt(Date.now());
  }, []);

  useEffect(() => {
    if (!streaming) return undefined;
    return subscribe(() => {
      setTick((t) => t + 1);
      setLastRefreshedAt(Date.now());
    });
  }, [streaming]);

  const value = useMemo<AppState>(
    () => ({
      streaming,
      setStreaming,
      tick,
      lastRefreshedAt,
      refreshNow,
      isDemoData: !isLiveMode,
      sourceName: isLiveMode ? `Live API · ${apiConfig.baseUrl}` : "Demo scenario",
      pollIntervalMs: apiConfig.pollIntervalMs,
    }),
    [streaming, tick, lastRefreshedAt, refreshNow],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState(): AppState {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used inside <AppStateProvider>");
  return ctx;
}
