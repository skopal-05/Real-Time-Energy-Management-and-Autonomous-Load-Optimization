"use client";

import { useEffect } from "react";
import { AlertOctagon, RefreshCw } from "lucide-react";

/**
 * Route-level error boundary. Anything a page throws during render lands here
 * instead of a blank screen.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Replace with the project's logging transport when one is available.
    console.error("Control centre render error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-crit/30 bg-crit/10">
        <AlertOctagon className="h-5 w-5 text-crit" aria-hidden />
      </span>
      <h2 className="text-lg font-semibold tracking-tight text-content">This screen failed to render</h2>
      <p className="max-w-md text-xs leading-relaxed text-content-muted">
        {error.message || "An unexpected error occurred while building this view."}
        {error.digest ? ` (ref ${error.digest})` : ""}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-surface-overlay px-3 py-1.5 text-xs font-medium text-content transition-colors hover:border-info/40 hover:text-info"
      >
        <RefreshCw className="h-3 w-3" aria-hidden />
        Try again
      </button>
    </div>
  );
}
