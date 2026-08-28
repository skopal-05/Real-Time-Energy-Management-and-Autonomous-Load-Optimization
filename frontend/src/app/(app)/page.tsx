"use client";

import { useCallback } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CircleDollarSign,
  GaugeCircle,
  GraduationCap,
  Network,
  Target,
  TriangleAlert,
  Users,
} from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useAuth } from "@/providers/AuthProvider";
import { useAppState } from "@/providers/AppStateProvider";
import { ASSET_IDS, DEMAND_CAP_KW } from "@/lib/constants";
import type { SystemStatus } from "@/lib/types";
import { formatKw, formatPct } from "@/lib/format";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { Chip, StatusBadge } from "@/components/ui/StatusBadge";
import { DataOriginBadge } from "@/components/ui/DataOriginBadge";
import { Skeleton } from "@/components/ui/States";
import { PipelineExplainer } from "@/components/overview/PipelineExplainer";

const FRAMING = [
  {
    icon: TriangleAlert,
    eyebrow: "The problem",
    title: "Industrial sites pay for peaks they never see coming",
    body: `A manufacturing plant runs dozens of loads that interact — lines, compressed air, steam, cooling. Demand charges are set by a handful of half-hour peaks, on-site solar rarely lines up with them, and by the time an operator notices a peak forming it has already been billed. Most plants also have no way to tell "this asset is drifting" from "this asset is just working hard today".`,
  },
  {
    icon: Network,
    eyebrow: "The approach",
    title: "A live model of the plant, with AI reasoning on top",
    body: "Every asset gets a digital twin that mirrors its measured state and derives what instruments do not report directly. On top of those twins sits a pipeline that predicts demand, decides what to do about it, searches for a cheaper schedule, flags abnormal behaviour, and explains each of those outputs in terms of the measurements that drove them.",
  },
  {
    icon: CircleDollarSign,
    eyebrow: "The outcome",
    title: "Peaks shaved, drift caught early, every decision auditable",
    body: `The optimiser returns a schedule that holds site demand under the contracted ${DEMAND_CAP_KW} kW cap while conserving total energy; the agent layer surfaces the actions that get it there with the rule that fired; the detector raises deviations with a score, not a guess; and SHAP shows which features moved each model output.`,
  },
];

const TEAM = ["Udit Mittal", "Aryan Pundir", "Kopal Sachan"];

export default function IntroductionPage() {
  const ds = getDataSource();
  const { session } = useAuth();
  const { isDemoData } = useAppState();
  const status = useResource<SystemStatus>(useCallback(() => ds.getSystemStatus(), [ds]));

  const s = status.data;
  const firstName = session?.user.name.split(" ")[0];

  return (
    <>
      {/* Hero */}
      <section className="panel grid-backdrop relative mb-3 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(55% 60% at 12% 0%, rgba(56,189,248,0.10), transparent 70%), radial-gradient(45% 55% at 92% 100%, rgba(167,139,250,0.08), transparent 70%)",
          }}
          aria-hidden
        />
        <div className="relative px-5 py-8 sm:px-8 sm:py-10">
          <div className="flex flex-wrap items-center gap-2">
            <Chip tone="info">Digital Twin Control Centre</Chip>
            <DataOriginBadge origin={status.origin} />
            {s ? <StatusBadge status={s.overall} /> : null}
          </div>

          {firstName ? (
            <p className="mt-4 text-sm font-medium text-info">Welcome back, {firstName}.</p>
          ) : null}

          <h1 className="mt-2 max-w-4xl text-2xl font-semibold leading-tight tracking-tight text-content sm:text-3xl">
            Generative Digital Twin for Real-Time Energy Management and Autonomous Load Optimization
          </h1>

          <p className="mt-3 max-w-3xl text-[13px] leading-relaxed text-content-muted sm:text-sm">
            This platform keeps a continuously updated model of an industrial manufacturing site —
            two production lines, a boiler, a compressor, HVAC, rooftop solar, battery storage and the
            grid connection — and layers an AI pipeline on top of it that forecasts demand, decides
            how to meet it, optimises the load schedule, detects abnormal behaviour and explains every
            output it produces.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2">
            <Link
              href="/overview"
              className="inline-flex items-center gap-2 rounded-lg border border-info/40 bg-info/15 px-4 py-2 text-sm font-medium text-info transition-colors hover:bg-info/20"
            >
              Open the Command Centre
              <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
            <Link
              href="/energy-flow"
              className="inline-flex items-center gap-2 rounded-lg border border-line bg-surface-inset px-4 py-2 text-sm font-medium text-content-muted transition-colors hover:border-line-strong hover:text-content"
            >
              See the energy flow map
              <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
          </div>

          {/* Live vitals */}
          <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-line-soft pt-6 sm:grid-cols-4">
            {[
              { label: "Digital twins", value: s ? `${s.twinsOnline} / ${s.twinsTotal}` : null, caption: "reporting now" },
              { label: "Site demand", value: s ? formatKw(s.consumptionKw, 0) : null, caption: "across all loads" },
              { label: "Renewable share", value: s ? formatPct(s.renewableSharePct, 0) : null, caption: "of current demand" },
              { label: "Operating mode", value: s ? s.operatingModeLabel : null, caption: "chosen by the agents" },
            ].map((item) => (
              <div key={item.label}>
                <dt className="label-eyebrow">{item.label}</dt>
                <dd className="mt-1 text-xl font-semibold tabular tracking-tight text-content">
                  {item.value ?? <Skeleton className="h-6 w-20" />}
                </dd>
                <dd className="mt-0.5 text-2xs text-content-faint">{item.caption}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Problem → approach → outcome */}
      <div className="mb-3 grid grid-cols-1 gap-3 lg:grid-cols-3">
        {FRAMING.map((f) => {
          const Icon = f.icon;
          return (
            <article key={f.eyebrow} className="panel flex flex-col p-5">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-info/10 ring-1 ring-info/20">
                  <Icon className="h-3.5 w-3.5 text-info" aria-hidden />
                </span>
                <span className="label-eyebrow">{f.eyebrow}</span>
              </div>
              <h2 className="mt-3 text-sm font-semibold leading-snug text-content">{f.title}</h2>
              <p className="mt-2 text-xs leading-relaxed text-content-muted">{f.body}</p>
            </article>
          );
        })}
      </div>

      {/* Pipeline */}
      <Panel className="mb-3">
        <PanelHeader
          title="How the system works"
          subtitle="Seven modules, each feeding the next. Every card opens the page that shows that module's live output."
          eyebrow="The AI & Digital Twin pipeline"
          actions={<Chip>{ASSET_IDS.length} modelled assets</Chip>}
        />
        <PanelBody className="pt-4">
          <PipelineExplainer />
        </PanelBody>
      </Panel>

      {/* Project details + data note */}
      <div className="grid grid-cols-1 items-start gap-3 lg:grid-cols-3">
        <Panel className="lg:col-span-2">
          <PanelHeader
            title="Project details"
            subtitle="Final-year capstone in industrial energy systems."
            eyebrow="About this work"
          />
          <PanelBody className="pt-4">
            <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <dt className="label-eyebrow">Full title</dt>
                <dd className="mt-1 text-[13px] leading-relaxed text-content">
                  Generative Digital Twin for Real-Time Energy Management and Autonomous Load
                  Optimization in Industrial Manufacturing Systems
                </dd>
              </div>
              <div>
                <dt className="label-eyebrow">Project ID</dt>
                <dd className="mt-1 font-mono text-[13px] text-content">11983UG02</dd>
              </div>
              <div>
                <dt className="label-eyebrow">Guide</dt>
                <dd className="mt-1 flex items-center gap-1.5 text-[13px] text-content">
                  <GraduationCap className="h-3.5 w-3.5 text-content-faint" aria-hidden />
                  Dr. Archana T
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="label-eyebrow flex items-center gap-1.5">
                  <Users className="h-3 w-3" aria-hidden />
                  Team
                </dt>
                <dd className="mt-1.5 flex flex-wrap gap-1.5">
                  {TEAM.map((member) => (
                    <Chip key={member}>{member}</Chip>
                  ))}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="label-eyebrow flex items-center gap-1.5">
                  <Target className="h-3 w-3" aria-hidden />
                  Scope
                </dt>
                <dd className="mt-1 text-xs leading-relaxed text-content-muted">
                  Seven integrated modules covering data acquisition, digital twin modelling, AI
                  forecasting, multi-agent decision making, load optimisation, anomaly detection and
                  explainable AI — targeted at industrial manufacturing energy systems.
                </dd>
              </div>
            </dl>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader
            title="About the data on these screens"
            subtitle="Read this before quoting any number."
            eyebrow="Provenance"
          />
          <PanelBody className="space-y-3 pt-4">
            {isDemoData ? (
              <>
                <div className="flex items-start gap-2 rounded-lg border border-warn/25 bg-warn/[0.06] px-3 py-2.5">
                  <GaugeCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warn" aria-hidden />
                  <p className="text-2xs leading-relaxed text-warn/90">
                    The platform is running on its built-in demo scenario. Every figure is produced by
                    a deterministic simulation of the site, not measured from plant instrumentation,
                    and is labelled <span className="font-semibold">Demo data</span> wherever it
                    appears.
                  </p>
                </div>
                <p className="text-xs leading-relaxed text-content-muted">
                  The simulation models shift patterns, boiler and compressor cycling, ambient-driven
                  HVAC load, rooftop PV with thermal derating and a battery dispatched against a
                  three-band tariff — so the behaviour is physically coherent rather than random
                  noise.
                </p>
              </>
            ) : (
              <p className="text-xs leading-relaxed text-content-muted">
                The platform is reading from the connected backend. Values on these screens are live
                measurements and live model output.
              </p>
            )}
            <p className="text-xs leading-relaxed text-content-muted">
              Nothing here is fabricated to look complete: where a model has no result for a
              selection, the screen says so rather than inventing one.
            </p>
            <Link
              href="/monitoring"
              className="inline-flex items-center gap-1.5 text-2xs font-medium text-info hover:underline"
            >
              See the acquisition layer
              <ArrowRight className="h-3 w-3" aria-hidden />
            </Link>
          </PanelBody>
        </Panel>
      </div>
    </>
  );
}
