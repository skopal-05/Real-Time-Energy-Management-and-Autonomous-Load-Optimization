"use client";

import { cn } from "@/lib/utils";

export interface SegmentedOption<T extends string> {
  value: T;
  label: string;
  title?: string;
}

interface SegmentedProps<T extends string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  label: string;
  size?: "sm" | "md";
  className?: string;
}

/** Compact single-select control used for horizons, periods and view modes. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
  size = "sm",
  className,
}: SegmentedProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={cn(
        "inline-flex items-center gap-0.5 rounded-lg border border-line bg-surface-inset p-0.5",
        className,
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            title={opt.title}
            onClick={() => onChange(opt.value)}
            className={cn(
              "rounded-md font-medium transition-colors",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
              active
                ? "bg-surface-overlay text-content shadow-panel"
                : "text-content-muted hover:text-content",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
