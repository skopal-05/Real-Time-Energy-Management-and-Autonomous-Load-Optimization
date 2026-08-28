"use client";

import { Filter, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SelectFilter<T extends string> {
  id: string;
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

interface FilterBarProps {
  /** Rendered left-to-right; each is a labelled native select for accessibility. */
  filters: SelectFilter<string>[];
  onReset?: () => void;
  /** e.g. "6 of 24 anomalies". */
  resultLabel?: string;
  className?: string;
  children?: React.ReactNode;
}

export function Select<T extends string>({ id, label, value, options, onChange }: SelectFilter<T>) {
  return (
    <label htmlFor={id} className="flex items-center gap-2">
      <span className="text-2xs uppercase tracking-wider text-content-faint">{label}</span>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="rounded-md border border-line bg-surface-inset px-2 py-1 text-xs text-content transition-colors hover:border-line-strong focus:border-info/60"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-surface">
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function FilterBar({ filters, onReset, resultLabel, className, children }: FilterBarProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-line bg-surface-inset px-3 py-2",
        className,
      )}
    >
      <span className="flex items-center gap-1.5 text-2xs uppercase tracking-wider text-content-faint">
        <Filter className="h-3 w-3" aria-hidden />
        Filters
      </span>
      {filters.map((f) => (
        <Select key={f.id} {...f} />
      ))}
      {children}
      <div className="ml-auto flex items-center gap-3">
        {resultLabel ? <span className="text-xs tabular text-content-muted">{resultLabel}</span> : null}
        {onReset ? (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-2xs text-content-faint transition-colors hover:text-content"
          >
            <X className="h-3 w-3" aria-hidden />
            Reset
          </button>
        ) : null}
      </div>
    </div>
  );
}
