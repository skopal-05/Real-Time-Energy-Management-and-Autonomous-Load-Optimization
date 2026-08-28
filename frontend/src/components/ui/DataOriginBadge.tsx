import { FlaskConical, Radio, Unplug } from "lucide-react";
import type { DataOrigin } from "@/lib/types";
import { cn } from "@/lib/utils";
import { InfoTip } from "./InfoTip";

const COPY: Record<DataOrigin, { label: string; hint: string; className: string }> = {
  live: {
    label: "Live data",
    hint: "Values on this screen come from the connected backend API.",
    className: "border-ok/30 bg-ok/10 text-ok",
  },
  simulated: {
    label: "Demo data",
    hint: "Values on this screen are produced by the built-in simulation, not measured from plant instrumentation. Connect the backend API to replace them.",
    className: "border-warn/30 bg-warn/10 text-warn",
  },
  unavailable: {
    label: "No data source",
    hint: "No data source is currently returning values for this screen.",
    className: "border-idle/30 bg-idle/10 text-content-faint",
  },
};

/**
 * Provenance marker. Every screen shows one so simulated figures can never be
 * mistaken for measurements during a demo.
 */
export function DataOriginBadge({
  origin,
  className,
  withHint = true,
}: {
  origin: DataOrigin;
  className?: string;
  withHint?: boolean;
}) {
  const copy = COPY[origin];
  const Icon = origin === "live" ? Radio : origin === "simulated" ? FlaskConical : Unplug;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-1.5 py-0.5 text-2xs font-medium",
        copy.className,
        className,
      )}
    >
      <Icon className="h-3 w-3" aria-hidden />
      {copy.label}
      {withHint ? <InfoTip text={copy.hint} align="right" /> : null}
    </span>
  );
}
