import Link from "next/link";
import { Activity, BrainCircuit, Network, Zap } from "lucide-react";

const HIGHLIGHTS = [
  {
    icon: Network,
    title: "Eight digital twins",
    body: "Production lines, boiler, compressor, HVAC, solar, storage and the grid connection, each mirroring its measured state.",
  },
  {
    icon: BrainCircuit,
    title: "A full AI pipeline",
    body: "Random Forest forecasting, a rule-based agent layer, Genetic Algorithm scheduling, Isolation Forest detection and SHAP explanations.",
  },
  {
    icon: Activity,
    title: "Built for real data",
    body: "Every screen reads through one service layer, so the demo scenario swaps for live plant data without touching the UI.",
  },
];

/** Full-screen split layout used by the sign-in and sign-up screens. */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      {/* Brand panel */}
      <aside className="grid-backdrop relative hidden flex-1 flex-col justify-between border-r border-line bg-surface-inset p-10 lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            background:
              "radial-gradient(60% 45% at 20% 10%, rgba(56,189,248,0.10), transparent 70%), radial-gradient(50% 40% at 85% 85%, rgba(167,139,250,0.08), transparent 70%)",
          }}
          aria-hidden
        />

        <Link href="/" className="relative flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-info/12 ring-1 ring-info/25">
            <Zap className="h-4 w-4 text-info" aria-hidden />
          </span>
          <span>
            <span className="block text-sm font-semibold tracking-tight text-content">EnerTwin</span>
            <span className="block text-2xs text-content-faint">Digital Twin Control Centre</span>
          </span>
        </Link>

        <div className="relative max-w-xl">
          <p className="label-eyebrow mb-3">Final-year project · Industrial energy systems</p>
          <h2 className="text-2xl font-semibold leading-snug tracking-tight text-content">
            Generative Digital Twin for Real-Time Energy Management and Autonomous Load Optimization
          </h2>
          <p className="mt-3 text-[13px] leading-relaxed text-content-muted">
            A control centre that keeps a live model of a manufacturing site, predicts what it is about
            to draw, decides what to do about it, and shows its reasoning.
          </p>

          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map((h) => {
              const Icon = h.icon;
              return (
                <li key={h.title} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-line bg-surface">
                    <Icon className="h-3.5 w-3.5 text-info" aria-hidden />
                  </span>
                  <div>
                    <p className="text-[13px] font-medium text-content">{h.title}</p>
                    <p className="mt-0.5 max-w-md text-xs leading-relaxed text-content-muted">{h.body}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        <p className="relative text-2xs text-content-faint">
          Project 11983UG02 · Guided by Dr. Archana T
        </p>
      </aside>

      {/* Form panel */}
      <main className="flex flex-1 items-center justify-center px-5 py-12 sm:px-8">
        <div className="w-full max-w-sm">{children}</div>
      </main>
    </div>
  );
}
