import type { AssetId, AssetRole, AssetCategory, HealthState, Severity } from "./types";

/* ------------------------------------------------------------------ */
/* Status colour system — one source of truth for the whole app.        */
/* ------------------------------------------------------------------ */

export interface StatusStyle {
  label: string;
  /** Text colour class. */
  fg: string;
  /** Background chip class. */
  bg: string;
  /** Border class. */
  border: string;
  /** Raw hex for SVG/chart usage. */
  hex: string;
}

export const HEALTH_STYLES: Record<HealthState, StatusStyle> = {
  online: {
    label: "Online",
    fg: "text-ok",
    bg: "bg-ok/10",
    border: "border-ok/30",
    hex: "#22C55E",
  },
  healthy: {
    label: "Healthy",
    fg: "text-ok",
    bg: "bg-ok/10",
    border: "border-ok/30",
    hex: "#22C55E",
  },
  warning: {
    label: "Warning",
    fg: "text-warn",
    bg: "bg-warn/10",
    border: "border-warn/30",
    hex: "#F59E0B",
  },
  critical: {
    label: "Critical",
    fg: "text-crit",
    bg: "bg-crit/10",
    border: "border-crit/30",
    hex: "#EF4444",
  },
  offline: {
    label: "Offline",
    fg: "text-idle",
    bg: "bg-idle/10",
    border: "border-idle/30",
    hex: "#64748B",
  },
};

export const SEVERITY_STYLES: Record<Severity, StatusStyle> = {
  low: { label: "Low", fg: "text-info", bg: "bg-info/10", border: "border-info/30", hex: "#38BDF8" },
  medium: { label: "Medium", fg: "text-warn", bg: "bg-warn/10", border: "border-warn/30", hex: "#F59E0B" },
  high: { label: "High", fg: "text-crit", bg: "bg-crit/10", border: "border-crit/30", hex: "#EF4444" },
  critical: {
    label: "Critical",
    fg: "text-crit",
    bg: "bg-crit/15",
    border: "border-crit/50",
    hex: "#F87171",
  },
};

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];

/* ------------------------------------------------------------------ */
/* Chart palette                                                        */
/* ------------------------------------------------------------------ */

export const CHART_COLORS = {
  load: "#38BDF8",
  generation: "#22C55E",
  forecast: "#A78BFA",
  baseline: "#7C8BA1",
  optimised: "#22D3EE",
  solar: "#FBBF24",
  battery: "#2DD4BF",
  grid: "#60A5FA",
  thermal: "#FB7185",
  positive: "#22C55E",
  negative: "#F87171",
  axis: "#7F8EA3",
  gridline: "#1E2733",
} as const;

/* ------------------------------------------------------------------ */
/* Asset registry — static descriptors shared by mock and live adapters */
/* ------------------------------------------------------------------ */

export interface AssetDescriptor {
  id: AssetId;
  name: string;
  shortName: string;
  category: AssetCategory;
  role: AssetRole;
  description: string;
  location: string;
  ratedPowerKw: number;
  /** Lucide icon name resolved in `components/assets/assetIcon.tsx`. */
  icon: string;
  accent: string;
}

export const ASSET_REGISTRY: Record<AssetId, AssetDescriptor> = {
  "line-a": {
    id: "line-a",
    name: "Production Line A",
    shortName: "Line A",
    category: "production",
    role: "consumer",
    description:
      "Primary machining and assembly line. The twin tracks motor load, throughput and specific energy per unit produced.",
    location: "Shop Floor · Bay 1",
    ratedPowerKw: 420,
    icon: "factory",
    accent: "#38BDF8",
  },
  "line-b": {
    id: "line-b",
    name: "Production Line B",
    shortName: "Line B",
    category: "production",
    role: "consumer",
    description:
      "Secondary finishing and packaging line. Runs a two-shift pattern, so its twin models scheduled idle windows.",
    location: "Shop Floor · Bay 2",
    ratedPowerKw: 310,
    icon: "conveyor",
    accent: "#38BDF8",
  },
  boiler: {
    id: "boiler",
    name: "Boiler",
    shortName: "Boiler",
    category: "thermal",
    role: "consumer",
    description:
      "Steam generation for process heat. The twin couples fuel input, steam pressure and outlet temperature.",
    location: "Utilities Block",
    ratedPowerKw: 260,
    icon: "flame",
    accent: "#FB7185",
  },
  compressor: {
    id: "compressor",
    name: "Compressor",
    shortName: "Compressor",
    category: "utility",
    role: "consumer",
    description:
      "Compressed-air supply for pneumatics across both lines. Leakage and load/unload cycling dominate its energy signature.",
    location: "Utilities Block",
    ratedPowerKw: 180,
    icon: "gauge",
    accent: "#38BDF8",
  },
  hvac: {
    id: "hvac",
    name: "HVAC",
    shortName: "HVAC",
    category: "utility",
    role: "consumer",
    description:
      "Chillers and air handling for the shop floor and clean areas. Strongly driven by ambient temperature.",
    location: "Roof Plant Room",
    ratedPowerKw: 220,
    icon: "wind",
    accent: "#2DD4BF",
  },
  solar: {
    id: "solar",
    name: "Solar PV Array",
    shortName: "Solar",
    category: "generation",
    role: "producer",
    description:
      "Rooftop photovoltaic array. The twin models irradiance, panel temperature derating and inverter efficiency.",
    location: "Rooftop · North & South",
    ratedPowerKw: 350,
    icon: "sun",
    accent: "#FBBF24",
  },
  battery: {
    id: "battery",
    name: "Battery Storage",
    shortName: "Battery",
    category: "storage",
    role: "storage",
    description:
      "Lithium-ion energy storage used for peak shaving and solar time-shifting. The twin tracks state of charge and cycle depth.",
    location: "Energy Yard",
    ratedPowerKw: 250,
    icon: "battery",
    accent: "#2DD4BF",
  },
  grid: {
    id: "grid",
    name: "Grid Connection",
    shortName: "Grid",
    category: "supply",
    role: "bidirectional",
    description:
      "Utility point of common coupling. Import and export are metered here and priced against the tariff schedule.",
    location: "Substation · PCC",
    ratedPowerKw: 1400,
    icon: "grid",
    accent: "#60A5FA",
  },
};

export const ASSET_IDS = Object.keys(ASSET_REGISTRY) as AssetId[];

export const CONSUMER_ASSET_IDS: AssetId[] = ["line-a", "line-b", "boiler", "compressor", "hvac"];

/* ------------------------------------------------------------------ */
/* Pipeline story — used by the Overview pipeline strip                 */
/* ------------------------------------------------------------------ */

export const PIPELINE_STEPS = [
  { id: "acquisition", label: "Data Acquisition", module: "Module 1", href: "/monitoring" },
  { id: "twin", label: "Digital Twin", module: "Module 2", href: "/twins" },
  { id: "forecast", label: "Forecasting", module: "Random Forest", href: "/forecasting" },
  { id: "agents", label: "Decision Agents", module: "Rule-based multi-agent", href: "/decisions" },
  { id: "optimizer", label: "Optimisation", module: "Genetic Algorithm", href: "/optimization" },
  { id: "anomaly", label: "Anomaly Detection", module: "Isolation Forest", href: "/anomalies" },
  { id: "xai", label: "Explainability", module: "SHAP", href: "/explainability" },
] as const;

/** Contracted maximum demand at the point of common coupling, in kW. */
export const DEMAND_CAP_KW = 1050;

export const CURRENCY = "INR";
export const CURRENCY_SYMBOL = "₹";
