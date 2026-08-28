"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Lightbulb, MinusCircle, PlusCircle } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { ASSET_REGISTRY } from "@/lib/constants";
import type { AssetId, ExplainableModel, Explanation, FeatureContribution } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { EmptyState, LoadingState } from "@/components/ui/States";
import { Chip } from "@/components/ui/StatusBadge";
import { Select } from "@/components/ui/FilterBar";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import { AIExplanationCard } from "@/components/ai/AIExplanationCard";

type Target = AssetId | "site";

const SHAP_NOTES = [
  {
    title: "Base value",
    body: "The average prediction the model makes across its training data. Every explanation starts here.",
  },
  {
    title: "Contribution",
    body: "How much one feature pushed this particular prediction above or below the base value, measured in the target's own units.",
  },
  {
    title: "Additivity",
    body: "Contributions sum exactly to the difference between the base value and the model output, which is what makes SHAP auditable.",
  },
];

export default function ExplainabilityPage() {
  const ds = getDataSource();

  const models = useResource<ExplainableModel[]>(useCallback(() => ds.getExplainableModels(), [ds]));
  const modelList = useMemo(() => models.data ?? [], [models.data]);

  const [modelId, setModelId] = useState<string>("");
  const [target, setTarget] = useState<Target>("site");

  // Default to the first available model once the roster arrives.
  useEffect(() => {
    if (modelId === "" && modelList.length > 0) {
      setModelId(modelList[0].id);
      setTarget(modelList[0].scope[0]);
    }
  }, [modelId, modelList]);

  const selectedModel = modelList.find((m) => m.id === modelId) ?? null;

  const explanation = useResource<Explanation | null>(
    useCallback(
      () =>
        modelId === ""
          ? Promise.resolve({
              data: null,
              origin: "unavailable" as const,
              fetchedAt: new Date().toISOString(),
            })
          : ds.getExplanation(modelId, target),
      [ds, modelId, target],
    ),
    { deps: [modelId, target] },
  );

  const columns: Column<FeatureContribution>[] = [
    {
      key: "label",
      header: "Feature",
      sortable: true,
      render: (c) => (
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-content">{c.label}</p>
          <p className="truncate font-mono text-2xs text-content-faint">{c.feature}</p>
        </div>
      ),
    },
    {
      key: "featureValue",
      header: "Value",
      align: "right",
      sortable: true,
      render: (c) => `${formatNumber(c.featureValue, 2)} ${c.unit}`,
    },
    {
      key: "shapValue",
      header: "SHAP contribution",
      align: "right",
      sortable: true,
      render: (c) => (
        <span
          className={cn(
            "inline-flex items-center gap-1 font-medium tabular",
            c.shapValue >= 0 ? "text-ok" : "text-crit",
          )}
        >
          {c.shapValue >= 0 ? (
            <PlusCircle className="h-3 w-3" aria-hidden />
          ) : (
            <MinusCircle className="h-3 w-3" aria-hidden />
          )}
          {formatNumber(Math.abs(c.shapValue), 2)}
        </span>
      ),
    },
    {
      key: "feature",
      header: "Direction",
      align: "right",
      render: (c) => (
        <Chip tone={c.shapValue >= 0 ? "ok" : "crit"}>
          {c.shapValue >= 0 ? "pushes prediction up" : "pushes prediction down"}
        </Chip>
      ),
    },
  ];

  const targetOptions = (selectedModel?.scope ?? []).map((s) => ({
    value: s,
    label: s === "site" ? "Whole site" : ASSET_REGISTRY[s].name,
  }));

  return (
    <>
      <PageHeader
        title="Explainable AI"
        description="SHAP attributions for the models driving this platform. Each explanation decomposes one prediction into the contribution of every input feature, so a recommendation can be traced back to the measurements behind it."
        module="SHAP"
        origin={explanation.origin}
        actions={
          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line bg-surface-inset px-3 py-2">
            <Select
              id="xai-model"
              label="Model"
              value={modelId}
              options={
                modelList.length === 0
                  ? [{ value: "", label: "Loading…" }]
                  : modelList.map((m) => ({ value: m.id, label: `${m.name} · ${m.algorithm}` }))
              }
              onChange={(v) => {
                setModelId(v);
                const next = modelList.find((m) => m.id === v);
                if (next) setTarget(next.scope[0]);
              }}
            />
            <Select
              id="xai-target"
              label="Asset"
              value={target}
              options={targetOptions.length === 0 ? [{ value: "site", label: "Whole site" }] : targetOptions}
              onChange={(v) => setTarget(v as Target)}
            />
          </div>
        }
      />

      <ResourceBoundary resource={explanation} loading={<LoadingState className="h-64" />}>
        {(data) =>
          data === null ? (
            <EmptyState
              title="No SHAP explainer for this selection"
              description="This model has no explainer fitted for the selected asset. Rather than displaying invented attributions, the page stays empty until the backend returns real SHAP values for this pair."
              icon={<Lightbulb className="h-5 w-5" />}
              className="py-16"
            />
          ) : (
            <>
              <AIExplanationCard explanation={data} />

              <div className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-5">
                <Panel className="xl:col-span-3">
                  <PanelHeader
                    title="Feature contributions"
                    subtitle="Ordered by absolute contribution. Green pushes the prediction up, red pulls it down."
                    eyebrow="SHAP values"
                    hint="Bars are signed contributions in the target's units. Their sum equals the gap between the base value and the model output."
                  />
                  <PanelBody className="pt-2">
                    <FeatureImportanceChart
                      contributions={data.contributions}
                      unit={data.unit}
                      height={340}
                    />
                  </PanelBody>
                </Panel>

                <Panel className="xl:col-span-2">
                  <PanelHeader
                    title="Reading a SHAP explanation"
                    subtitle="Three ideas are enough to interpret the chart."
                    eyebrow="Method"
                  />
                  <PanelBody className="space-y-3 pt-3">
                    {SHAP_NOTES.map((n) => (
                      <div key={n.title} className="rounded-lg border border-line bg-surface-inset p-3">
                        <p className="text-[13px] font-semibold text-content">{n.title}</p>
                        <p className="mt-1 text-xs leading-relaxed text-content-muted">{n.body}</p>
                      </div>
                    ))}
                    <div className="rounded-lg border border-info/25 bg-info/[0.06] p-3">
                      <p className="text-[13px] font-semibold text-info">In this case</p>
                      <p className="mt-1 text-xs leading-relaxed text-content-muted">
                        {data.baseValue >= 0 ? "Starting from" : "Starting from"}{" "}
                        <span className="tabular text-content">
                          {formatNumber(data.baseValue, data.unit === "" ? 3 : 1)} {data.unit}
                        </span>
                        , the listed features move the model to{" "}
                        <span className="tabular text-content">
                          {formatNumber(data.prediction, data.unit === "" ? 3 : 1)} {data.unit}
                        </span>
                        . The largest single mover is{" "}
                        <span className="font-medium text-content">
                          {data.contributions[0]?.label ?? "—"}
                        </span>
                        .
                      </p>
                    </div>
                  </PanelBody>
                </Panel>
              </div>

              <Panel className="mt-3">
                <PanelHeader
                  title="Contribution table"
                  subtitle="The same attributions with the raw feature values used for this instance."
                  eyebrow="Detail"
                  actions={
                    selectedModel ? (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Chip tone="info">{selectedModel.algorithm}</Chip>
                        <Chip>{selectedModel.target}</Chip>
                      </div>
                    ) : null
                  }
                />
                <DataTable
                  columns={columns}
                  rows={data.contributions}
                  rowKey={(c) => c.feature}
                  initialSort={{ key: "shapValue", direction: "desc" }}
                />
              </Panel>
            </>
          )
        }
      </ResourceBoundary>
    </>
  );
}
