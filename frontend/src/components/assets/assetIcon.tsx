import {
  BatteryCharging,
  Factory,
  Flame,
  Gauge,
  PlugZap,
  Sun,
  Wind,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { ASSET_REGISTRY } from "@/lib/constants";
import type { AssetId } from "@/lib/types";

const ICONS: Record<string, LucideIcon> = {
  factory: Factory,
  conveyor: Workflow,
  flame: Flame,
  gauge: Gauge,
  wind: Wind,
  sun: Sun,
  battery: BatteryCharging,
  grid: PlugZap,
};

export function assetIcon(assetId: AssetId): LucideIcon {
  return ICONS[ASSET_REGISTRY[assetId].icon] ?? Gauge;
}

export function assetAccent(assetId: AssetId): string {
  return ASSET_REGISTRY[assetId].accent;
}
