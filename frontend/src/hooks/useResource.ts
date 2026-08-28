"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DataEnvelope, DataOrigin } from "@/lib/types";
import { useAppState } from "@/providers/AppStateProvider";

export interface Resource<T> {
  data: T | null;
  origin: DataOrigin;
  notice?: string;
  loading: boolean;
  error: string | null;
  /** Epoch ms the payload arrived, null before first load. */
  fetchedAt: number | null;
  reload: () => void;
}

interface Options {
  /** Re-run whenever the global refresh tick advances. Default true. */
  live?: boolean;
  /** Extra values that should trigger a re-fetch, e.g. a selected horizon. */
  deps?: readonly unknown[];
}

/**
 * Loads one resource from the active data source and tracks loading/error state.
 *
 * The loader is called on mount, whenever `deps` change, and on every global
 * refresh tick. Refresh ticks keep the previously loaded data on screen so the
 * dashboard never flashes back to a skeleton while streaming.
 */
export function useResource<T>(
  loader: () => Promise<DataEnvelope<T>>,
  options: Options = {},
): Resource<T> {
  const { live = true, deps = [] } = options;
  const { tick } = useAppState();
  const [data, setData] = useState<T | null>(null);
  const [origin, setOrigin] = useState<DataOrigin>("unavailable");
  const [notice, setNotice] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [manualTick, setManualTick] = useState(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const hasData = useRef(false);

  const reload = useCallback(() => setManualTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    if (!hasData.current) setLoading(true);

    loaderRef
      .current()
      .then((envelope) => {
        if (cancelled) return;
        hasData.current = true;
        setData(envelope.data);
        setOrigin(envelope.origin);
        setNotice(envelope.notice);
        setFetchedAt(new Date(envelope.fetchedAt).getTime());
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unexpected error loading data.");
        setOrigin("unavailable");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [live ? tick : 0, manualTick, ...deps]);

  return { data, origin, notice, loading, error, fetchedAt, reload };
}
