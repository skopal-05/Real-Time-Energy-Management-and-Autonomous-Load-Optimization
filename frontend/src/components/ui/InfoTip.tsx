"use client";

import { useId, useState } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface InfoTipProps {
  text: string;
  className?: string;
  /** Which side the bubble opens on when there is no room below. */
  align?: "left" | "right";
}

/**
 * Small hover/focus tooltip for technical terms (SHAP, MAPE, Isolation Forest…).
 * Keyboard accessible: the trigger is a real button and the bubble is linked
 * with aria-describedby.
 */
export function InfoTip({ text, className, align = "left" }: InfoTipProps) {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <span className={cn("relative inline-flex", className)}>
      <button
        type="button"
        aria-label="More information"
        aria-describedby={open ? id : undefined}
        className="rounded text-content-faint transition-colors hover:text-content-muted"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(e) => {
          e.preventDefault();
          setOpen((v) => !v);
        }}
      >
        <Info className="h-3.5 w-3.5" aria-hidden />
      </button>
      {open ? (
        <span
          id={id}
          role="tooltip"
          className={cn(
            "absolute top-6 z-50 w-64 rounded-lg border border-line-strong bg-surface-overlay p-2.5 text-xs leading-relaxed text-content-muted shadow-lift",
            align === "left" ? "left-0" : "right-0",
          )}
        >
          {text}
        </span>
      ) : null}
    </span>
  );
}
