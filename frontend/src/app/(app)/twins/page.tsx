"use client";

import { useCallback, useMemo, useState } from "react";
import { Boxes } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import type { Asset, AssetCategory, HealthState } from "@/lib/types";
import { formatKw } from "@/lib/format";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { EmptyState, LoadingState } from "@/components/ui/States";
import { FilterBar } from "@/components/ui/FilterBar";
import { AssetCard } from "@/components/assets/AssetCard";
import { AssetStatusGrid } from "@/components/assets/AssetStatusGrid";

type CategoryFilter = AssetCategory | "all";
type StatusFilter = HealthState | "all";

const CATEGORY_OPTIONS: { value: CategoryFilter; label: string }[] = [
  { value: "all", label: "All categories" },
  { value: "production", label: "Production" },
  { value: "thermal", label: "Thermal" },
  { value: "utility", label: "Utility" },
  { value: "generation", label: "Generation" },
  { value: "storage", label: "Storage" },
  { value: "supply", label: "Supply" },
];

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "Any status" },
  { value: "healthy", label: "Healthy" },
  { value: "warning", label: "Warning" },
  { value: "critical", label: "Critical" },
  { value: "offline", label: "Offline" },
];

export default function DigitalTwinsPage() {
  const ds = getDataSource();
  const now = useNow();
  const assets = useResource<Asset[]>(useCallback(() => ds.getAssets(), [ds]));

  const [category, setCategory] = useState<CategoryFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");

  const filtered = useMemo(() => {
    const list = assets.data ?? [];
    return list.filter(
      (a) => (category === "all" || a.category === category) && (status === "all" || a.status === status),
    );
  }, [assets.data, category, status]);

  const totals = useMemo(() => {
    const list = assets.data ?? [];
    // Only plant loads count as consumption — adding the grid connection would
    // double-count the same kilowatts on the supply side.
    const consuming = list
      .filter((a) => a.role === "consumer")
      .reduce((acc, a) => acc + Math.max(a.powerKw, 0), 0);
    const producing = list
      .filter((a) => a.role === "producer" || a.role === "storage")
      .reduce((acc, a) => acc + Math.max(a.powerKw, 0), 0);
    return { consuming, producing, warnings: list.filter((a) => a.status !== "healthy").length };
  }, [assets.data]);

  return (
    <>
      <PageHeader
        title="Digital Twins"
        description="Each asset is represented by a digital twin that mirrors its measured state, derives efficiency and utilisation, and feeds the forecasting, decision and anomaly modules. Open a twin for its full sensor vector, history and model output."
        module="Module 2 · Digital twin"
        origin={assets.origin}
      />

      <Panel className="mb-3">
        <PanelHeader
          title="Fleet status"
          subtitle={`${formatKw(totals.consuming, 0)} consumed · ${formatKw(totals.producing, 0)} produced · ${totals.warnings} twin(s) needing attention`}
          eyebrow="At a glance"
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={assets} loading={<LoadingState className="h-24" />}>
            {(data) => <AssetStatusGrid assets={data} />}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      <FilterBar
        className="mb-3"
        filters={[
          {
            id: "twin-category",
            label: "Category",
            value: category,
            options: CATEGORY_OPTIONS,
            onChange: (v) => setCategory(v as CategoryFilter),
          },
          {
            id: "twin-status",
            label: "Status",
            value: status,
            options: STATUS_OPTIONS,
            onChange: (v) => setStatus(v as StatusFilter),
          },
        ]}
        resultLabel={`${filtered.length} of ${(assets.data ?? []).length} twins`}
        onReset={
          category !== "all" || status !== "all"
            ? () => {
                setCategory("all");
                setStatus("all");
              }
            : undefined
        }
      />

      <ResourceBoundary
        resource={assets}
        loading={<LoadingState variant="cards" rows={8} className="xl:grid-cols-4" />}
      >
        {() =>
          filtered.length === 0 ? (
            <EmptyState
              title="No twins match these filters"
              description="Reset the category or status filter to see the full fleet."
              icon={<Boxes className="h-5 w-5" />}
            />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {filtered.map((asset) => (
                <AssetCard key={asset.id} asset={asset} now={now} />
              ))}
            </div>
          )
        }
      </ResourceBoundary>
    </>
  );
}
