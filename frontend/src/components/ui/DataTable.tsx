"use client";

import { useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp, ChevronsUpDown } from "lucide-react";
import { cn, sortRows } from "@/lib/utils";
import { EmptyState } from "./States";

export interface Column<T> {
  key: keyof T & string;
  header: string;
  /** Custom cell renderer. Falls back to the raw value. */
  render?: (row: T) => ReactNode;
  sortable?: boolean;
  align?: "left" | "right";
  className?: string;
  headerHint?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  initialSort?: { key: keyof T & string; direction: "asc" | "desc" };
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
}

/** Sortable, keyboard-navigable table with a consistent empty state. */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  initialSort,
  onRowClick,
  emptyTitle = "Nothing to show",
  emptyDescription,
  className,
}: DataTableProps<T>) {
  const [sort, setSort] = useState(initialSort ?? null);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    return sortRows(rows, sort.key as keyof T, sort.direction);
  }, [rows, sort]);

  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const toggle = (key: keyof T & string) => {
    setSort((prev) =>
      prev && prev.key === key
        ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "desc" },
    );
  };

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-line">
            {columns.map((col) => {
              const active = sort?.key === col.key;
              const Icon = !active ? ChevronsUpDown : sort?.direction === "asc" ? ChevronUp : ChevronDown;
              return (
                <th
                  key={col.key}
                  scope="col"
                  className={cn(
                    "whitespace-nowrap px-3 py-2 text-2xs font-medium uppercase tracking-wider text-content-faint",
                    col.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => toggle(col.key)}
                      className={cn(
                        "inline-flex items-center gap-1 rounded transition-colors hover:text-content",
                        active && "text-content",
                        col.align === "right" && "flex-row-reverse",
                      )}
                      aria-label={`Sort by ${col.header}`}
                    >
                      {col.header}
                      <Icon className="h-3 w-3" aria-hidden />
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === "Enter") onRowClick(row);
                    }
                  : undefined
              }
              className={cn(
                "border-b border-line-soft transition-colors last:border-0",
                onRowClick && "cursor-pointer hover:bg-surface-raised",
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-3 py-2.5 align-middle text-content-muted",
                    col.align === "right" && "text-right tabular",
                    col.className,
                  )}
                >
                  {col.render ? col.render(row) : String(row[col.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
