"use client";

import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  Boxes,
  Lightbulb,
  Radio,
  ShieldAlert,
  Sliders,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/StatusBadge";

interface Module {
  step: number;
  title: string;
  method: string;
  icon: LucideIcon;
  /** What this stage receives. */
  input: string;
  /** What it hands to the next stage. */
  output: string;
  body: string;
  href: string;
}

const MODULES: Module[] = [
  {
    step: 1,
    title: "Data Acquisition",
    method: "Sensor ingest & preprocessing",
    icon: Radio,
    input: "Plant instrumentation",
    output: "Clean, time-aligned signals",
    body: "Power, temperature, pressure, flow and throughput signals are polled from every asset, timestamped onto a common grid and quality-checked before anything downstream sees them.",
    href: "/monitoring",
  },
  {
    step: 2,
    title: "Digital Twin",
    method: "State estimation",
    icon: Boxes,
    input: "Clean signals",
    output: "Live state vector per asset",
    body: "Each of the eight assets carries a twin that holds its current state and derives what instruments do not measure directly — efficiency, utilisation, specific energy per unit produced.",
    href: "/twins",
  },
  {
    step: 3,
    title: "Forecasting",
    method: "Random Forest",
    icon: TrendingUp,
    input: "Twin state + calendar + weather",
    output: "Load prediction with intervals",
    body: "A Random Forest regressor trained on lagged load, production setpoints, ambient conditions and shift patterns predicts site and per-asset demand, and reports its own error honestly.",
    href: "/forecasting",
  },
  {
    step: 4,
    title: "Decision Agents",
    method: "Rule-based multi-agent",
    icon: BrainCircuit,
    input: "Twin state + forecast",
    output: "Proposed or applied actions",
    body: "Six agents own separate scopes — demand, generation, storage, thermal, cost and safety. Each evaluates explicit rules; the safety agent can veto any proposal the others make.",
    href: "/decisions",
  },
  {
    step: 5,
    title: "Optimisation",
    method: "Genetic Algorithm",
    icon: Sliders,
    input: "Forecast + tariff + constraints",
    output: "A cheaper, flatter schedule",
    body: "A GA searches 24-hour load schedules, shifting deferrable load out of demand peaks and expensive tariff bands while respecting production and process limits.",
    href: "/optimization",
  },
  {
    step: 6,
    title: "Anomaly Detection",
    method: "Isolation Forest",
    icon: ShieldAlert,
    input: "Twin state vectors",
    output: "Scored detections",
    body: "An Isolation Forest scores each measurement window against learned normal operation, catching drift that no single fixed threshold would flag.",
    href: "/anomalies",
  },
  {
    step: 7,
    title: "Explainability",
    method: "SHAP",
    icon: Lightbulb,
    input: "Any model output",
    output: "Signed feature attributions",
    body: "SHAP decomposes a prediction or detection into the contribution of every input feature, so a recommendation can always be traced back to the measurements behind it.",
    href: "/explainability",
  },
];

const CHAIN = [
  "Sensors",
  "Digital Twin",
  "Forecast",
  "Decide",
  "Optimise",
  "Detect",
  "Explain",
];

/** The project's seven modules, explained end to end with links into each one. */
export function PipelineExplainer({ className }: { className?: string }) {
  return (
    <div className={className}>
      {/* Compact chain */}
      <ol className="mb-5 flex flex-wrap items-center gap-x-1 gap-y-2">
        {CHAIN.map((label, i) => (
          <li key={label} className="flex items-center gap-1">
            <span className="rounded-md border border-line bg-surface-inset px-2 py-1 text-2xs font-medium text-content-muted">
              {label}
            </span>
            {i < CHAIN.length - 1 ? (
              <ArrowRight className="h-3 w-3 text-content-faint" aria-hidden />
            ) : null}
          </li>
        ))}
      </ol>

      <ol className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {MODULES.map((m) => {
          const Icon = m.icon;
          return (
            <li key={m.step}>
              <Link
                href={m.href}
                className="panel panel-hover group flex h-full flex-col p-4"
              >
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-info/12 text-2xs font-semibold text-info">
                    {m.step}
                  </span>
                  <Icon className="h-3.5 w-3.5 text-content-faint" aria-hidden />
                  <span className="ml-auto">
                    <Chip tone="info">{m.method}</Chip>
                  </span>
                </div>

                <h3 className="mt-2.5 text-[13px] font-semibold text-content transition-colors group-hover:text-info">
                  {m.title}
                </h3>
                <p className="mt-1.5 text-xs leading-relaxed text-content-muted">{m.body}</p>

                <dl className="mt-3 space-y-1.5 border-t border-line-soft pt-2.5">
                  <div className="flex gap-2">
                    <dt className="w-12 shrink-0 text-2xs uppercase tracking-wider text-content-faint">In</dt>
                    <dd className="text-2xs text-content-muted">{m.input}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-12 shrink-0 text-2xs uppercase tracking-wider text-content-faint">Out</dt>
                    <dd className="text-2xs text-content-muted">{m.output}</dd>
                  </div>
                </dl>

                <span
                  className={cn(
                    "mt-3 inline-flex items-center gap-1 text-2xs font-medium text-content-faint",
                    "transition-colors group-hover:text-info",
                  )}
                >
                  Open this module
                  <ArrowRight className="h-3 w-3" aria-hidden />
                </span>
              </Link>
            </li>
          );
        })}

        {/* Closes the grid and sends the reader into the live system. */}
        <li>
          <Link
            href="/overview"
            className="group flex h-full flex-col justify-center rounded-xl border border-dashed border-info/30 bg-info/[0.05] p-4 transition-colors hover:border-info/50 hover:bg-info/[0.09]"
          >
            <p className="text-[13px] font-semibold text-info">See it all running</p>
            <p className="mt-1.5 text-xs leading-relaxed text-content-muted">
              The Command Centre shows every stage of this pipeline against the current state of the
              plant, on one screen.
            </p>
            <span className="mt-3 inline-flex items-center gap-1 text-2xs font-medium text-info">
              Open the Command Centre
              <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </span>
          </Link>
        </li>
      </ol>
    </div>
  );
}
