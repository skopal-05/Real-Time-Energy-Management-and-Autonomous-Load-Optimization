"use client";

import { CalendarRange } from "lucide-react";
import { Segmented, type SegmentedOption } from "./Segmented";

export type RangeKey = "1h" | "6h" | "12h" | "24h" | "7d";

const OPTIONS: SegmentedOption<RangeKey>[] = [
  { value: "1h", label: "1H", title: "Last hour" },
  { value: "6h", label: "6H", title: "Last 6 hours" },
  { value: "12h", label: "12H", title: "Last 12 hours" },
  { value: "24h", label: "24H", title: "Last 24 hours" },
  { value: "7d", label: "7D", title: "Last 7 days" },
];

export const RANGE_HOURS: Record<RangeKey, number> = {
  "1h": 1,
  "6h": 6,
  "12h": 12,
  "24h": 24,
  "7d": 168,
};

/** Chart resolution paired to each range so series stay readable. */
export const RANGE_STEP_MINUTES: Record<RangeKey, number> = {
  "1h": 5,
  "6h": 10,
  "12h": 15,
  "24h": 30,
  "7d": 180,
};

interface DateRangeSelectorProps {
  value: RangeKey;
  onChange: (value: RangeKey) => void;
  options?: RangeKey[];
  showIcon?: boolean;
}

export function DateRangeSelector({
  value,
  onChange,
  options,
  showIcon = true,
}: DateRangeSelectorProps) {
  const list = options ? OPTIONS.filter((o) => options.includes(o.value)) : OPTIONS;
  return (
    <div className="flex items-center gap-2">
      {showIcon ? <CalendarRange className="h-3.5 w-3.5 text-content-faint" aria-hidden /> : null}
      <Segmented options={list} value={value} onChange={onChange} label="Time range" />
    </div>
  );
}
