"use client";

import { useState } from "react";
import { FlaskConical, X } from "lucide-react";
import { useAppState } from "@/providers/AppStateProvider";

/**
 * Persistent, dismissible notice that the screen is showing simulated data.
 * Rendered only when no live backend is configured.
 */
export function DemoBanner() {
  const { isDemoData, streaming, pollIntervalMs } = useAppState();
  const [dismissed, setDismissed] = useState(false);

  if (!isDemoData || dismissed) return null;

  return (
    <div className="flex items-center gap-2 border-b border-warn/20 bg-warn/[0.07] px-3 py-1.5 sm:px-5">
      <FlaskConical className="h-3.5 w-3.5 shrink-0 text-warn" aria-hidden />
      <p className="min-w-0 flex-1 text-2xs leading-relaxed text-warn/90">
        <span className="font-semibold">Demo mode.</span> All values come from the built-in simulation
        in <code className="rounded bg-warn/10 px-1 font-mono">src/data</code> — no plant instrumentation
        is connected.{" "}
        {streaming
          ? `The scenario advances every ${Math.round(pollIntervalMs / 1000)} s.`
          : "Live updates are paused."}{" "}
        Set <code className="rounded bg-warn/10 px-1 font-mono">NEXT_PUBLIC_API_MODE=live</code> to read
        from the backend instead.
      </p>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="shrink-0 rounded p-1 text-warn/70 transition-colors hover:text-warn"
        aria-label="Dismiss demo notice"
      >
        <X className="h-3 w-3" aria-hidden />
      </button>
    </div>
  );
}
