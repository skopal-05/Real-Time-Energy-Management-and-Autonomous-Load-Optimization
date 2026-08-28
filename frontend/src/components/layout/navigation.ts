import {
  Activity,
  BookOpen,
  Boxes,
  BrainCircuit,
  FileBarChart,
  LayoutDashboard,
  Lightbulb,
  Network,
  ShieldAlert,
  Sliders,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Shown under the label in the expanded sidebar. */
  description: string;
  /** Pipeline module this page represents, shown as a small tag. */
  module?: string;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    id: "operations",
    label: "Operations",
    items: [
      {
        href: "/",
        label: "Introduction",
        icon: BookOpen,
        description: "What this system does",
        module: "Start here",
      },
      {
        href: "/overview",
        label: "Overview",
        icon: LayoutDashboard,
        description: "Command centre",
        module: "Command centre",
      },
      {
        href: "/twins",
        label: "Digital Twins",
        icon: Boxes,
        description: "Asset state & health",
        module: "Twin",
      },
      {
        href: "/monitoring",
        label: "Real-Time Monitoring",
        icon: Activity,
        description: "Live signals",
        module: "Acquisition",
      },
      {
        href: "/energy-flow",
        label: "Energy Flow",
        icon: Network,
        description: "System map",
      },
    ],
  },
  {
    id: "intelligence",
    label: "AI Pipeline",
    items: [
      {
        href: "/forecasting",
        label: "Forecasting",
        icon: TrendingUp,
        description: "Load prediction",
        module: "Random Forest",
      },
      {
        href: "/decisions",
        label: "AI Decisions",
        icon: BrainCircuit,
        description: "Agent reasoning",
        module: "Multi-agent",
      },
      {
        href: "/optimization",
        label: "Optimisation",
        icon: Sliders,
        description: "Load scheduling",
        module: "Genetic Algorithm",
      },
      {
        href: "/anomalies",
        label: "Anomalies & Alerts",
        icon: ShieldAlert,
        description: "Deviation detection",
        module: "Isolation Forest",
      },
      {
        href: "/explainability",
        label: "Explainable AI",
        icon: Lightbulb,
        description: "Why the model decided",
        module: "SHAP",
      },
    ],
  },
  {
    id: "analysis",
    label: "Analysis",
    items: [
      {
        href: "/reports",
        label: "Reports",
        icon: FileBarChart,
        description: "Performance summary",
      },
    ],
  },
];

export const ALL_NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);

export function findNavItem(pathname: string): NavItem | undefined {
  if (pathname === "/") return ALL_NAV_ITEMS[0];
  return ALL_NAV_ITEMS.filter((i) => i.href !== "/").find((i) => pathname.startsWith(i.href));
}
