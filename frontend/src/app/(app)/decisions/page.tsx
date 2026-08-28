"use client";

import { useCallback, useMemo, useState } from "react";
import { ArrowRight, Bot, ShieldCheck, Target } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useNow } from "@/hooks/useNow";
import { ASSET_REGISTRY } from "@/lib/constants";
import type { Agent, AIRecommendation, DecisionStatus, OperatingObjective, Priority } from "@/lib/types";
import { formatDateTime, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/PageHeader";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { ResourceBoundary } from "@/components/ui/ResourceBoundary";
import { EmptyState, LoadingState } from "@/components/ui/States";
import { Chip } from "@/components/ui/StatusBadge";
import { FilterBar } from "@/components/ui/FilterBar";
import { RecommendationCard } from "@/components/ai/RecommendationCard";

type StatusFilter = DecisionStatus | "all";
type PriorityFilter = Priority | "all";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All statuses" },
  { value: "pending", label: "Awaiting operator" },
  { value: "accepted", label: "Accepted" },
  { value: "applied", label: "Applied" },
  { value: "rejected", label: "Rejected" },
];

const PRIORITY_OPTIONS: { value: PriorityFilter; label: string }[] = [
  { value: "all", label: "Any priority" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const DECISION_FLOW = [
  {
    title: "Observe",
    detail: "Each agent reads the twin state vectors and the latest Random Forest forecast for the assets in its scope.",
  },
  {
    title: "Evaluate rules",
    detail: "Conditions are checked against thresholds, tariff bands and forecast peaks. A rule that matches produces a candidate action.",
  },
  {
    title: "Price the action",
    detail: "The Cost Agent scores every candidate against the tariff schedule and the current optimisation objective.",
  },
  {
    title: "Safety veto",
    detail: "The Safety Agent rejects any candidate that would breach a hard process or equipment constraint. Its veto is absolute.",
  },
  {
    title: "Recommend or apply",
    detail: "Surviving actions are applied automatically where permitted, or surfaced here for an operator to accept.",
  },
];

function AgentCard({ agent, now }: { agent: Agent; now: number }) {
  return (
    <article className="panel panel-hover p-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-info/10 ring-1 ring-info/20">
            <Bot className="h-3.5 w-3.5 text-info" aria-hidden />
          </span>
          <p className="truncate text-[13px] font-semibold text-content">{agent.name}</p>
        </div>
        <Chip tone={agent.state === "active" ? "ok" : "neutral"}>{agent.state}</Chip>
      </div>

      <p className="mt-2 text-xs leading-relaxed text-content-muted">{agent.scope}</p>

      <dl className="mt-3 grid grid-cols-3 gap-2 border-t border-line-soft pt-2.5">
        <div>
          <dt className="label-eyebrow">Rules</dt>
          <dd className="text-sm font-semibold tabular text-content">{agent.ruleCount}</dd>
        </div>
        <div>
          <dt className="label-eyebrow">Decisions today</dt>
          <dd className="text-sm font-semibold tabular text-content">{agent.decisionsToday}</dd>
        </div>
        <div>
          <dt className="label-eyebrow">Last action</dt>
          <dd className="text-sm font-semibold tabular text-content">
            {agent.lastActionAt ? formatRelative(agent.lastActionAt, now) : "—"}
          </dd>
        </div>
      </dl>

      <ul className="mt-2.5 flex flex-wrap gap-1">
        {agent.watches.map((a) => (
          <li key={a}>
            <Chip>{ASSET_REGISTRY[a].shortName}</Chip>
          </li>
        ))}
      </ul>
    </article>
  );
}

export default function DecisionsPage() {
  const ds = getDataSource();
  const now = useNow();

  const objective = useResource<OperatingObjective>(useCallback(() => ds.getObjective(), [ds]));
  const agents = useResource<Agent[]>(useCallback(() => ds.getAgents(), [ds]));
  const recs = useResource<AIRecommendation[]>(useCallback(() => ds.getRecommendations(), [ds]));

  const [status, setStatus] = useState<StatusFilter>("all");
  const [priority, setPriority] = useState<PriorityFilter>("all");
  const [agentId, setAgentId] = useState<string>("all");

  const filtered = useMemo(() => {
    return (recs.data ?? []).filter(
      (r) =>
        (status === "all" || r.status === status) &&
        (priority === "all" || r.priority === priority) &&
        (agentId === "all" || r.agentId === agentId),
    );
  }, [recs.data, status, priority, agentId]);

  const pendingCount = (recs.data ?? []).filter((r) => r.status === "pending").length;

  return (
    <>
      <PageHeader
        title="AI Decision & Agent Centre"
        description="A rule-based multi-agent layer sits between the models and the plant. Each agent owns a scope, evaluates explicit rules against twin state and forecast, and either applies an action or proposes one for an operator. Every decision below carries the rule that fired and the reasoning behind it."
        module="Rule-based multi-agent"
        origin={recs.origin}
      />

      {/* Objective */}
      <ResourceBoundary resource={objective} loading={<LoadingState className="h-32" />}>
        {(obj) => (
          <Panel>
            <PanelHeader
              title="Current operating objective"
              subtitle="What every agent is currently optimising for, and the limits it must respect."
              eyebrow="Module 4 · Decisions"
              actions={<Chip tone="info">{pendingCount} awaiting operator</Chip>}
            />
            <PanelBody className="pt-3">
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-info" aria-hidden />
                    <h3 className="text-base font-semibold text-content">{obj.label}</h3>
                    <span className="text-2xs text-content-faint">
                      active since {formatDateTime(obj.since)}
                    </span>
                  </div>
                  <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-content-muted">
                    {obj.description}
                  </p>
                </div>
                <div>
                  <p className="label-eyebrow mb-1.5">Hard constraints</p>
                  <ul className="space-y-1.5">
                    {obj.constraints.map((c) => (
                      <li key={c} className="flex items-start gap-2 text-xs text-content-muted">
                        <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0 text-ok" aria-hidden />
                        <span className="leading-relaxed">{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </PanelBody>
          </Panel>
        )}
      </ResourceBoundary>

      {/* How a decision is made */}
      <Panel className="mt-3">
        <PanelHeader
          title="How a decision is made"
          subtitle="The same five steps run for every proposal, which is what makes the layer auditable."
          eyebrow="Reasoning process"
        />
        <PanelBody className="pt-3">
          <ol className="grid grid-cols-1 gap-2 sm:grid-cols-3 xl:grid-cols-5">
            {DECISION_FLOW.map((step, i) => (
              <li
                key={step.title}
                className="relative rounded-lg border border-line bg-surface-inset p-3"
              >
                <div className="flex items-center gap-1.5">
                  <span className="flex h-4 w-4 items-center justify-center rounded bg-info/15 text-[10px] font-semibold text-info">
                    {i + 1}
                  </span>
                  <p className="text-xs font-semibold text-content">{step.title}</p>
                  {i < DECISION_FLOW.length - 1 ? (
                    <ArrowRight className="ml-auto hidden h-3 w-3 text-content-faint xl:block" aria-hidden />
                  ) : null}
                </div>
                <p className="mt-1.5 text-2xs leading-relaxed text-content-muted">{step.detail}</p>
              </li>
            ))}
          </ol>
        </PanelBody>
      </Panel>

      {/* Agents */}
      <Panel className="mt-3">
        <PanelHeader
          title="Active agents"
          subtitle="Each agent owns a scope and a rule set. The safety agent can override the others."
          eyebrow="Agent roster"
        />
        <PanelBody className="pt-3">
          <ResourceBoundary resource={agents} loading={<LoadingState variant="cards" rows={6} />}>
            {(data) => (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {data.map((a) => (
                  <AgentCard key={a.id} agent={a} now={now} />
                ))}
              </div>
            )}
          </ResourceBoundary>
        </PanelBody>
      </Panel>

      {/* Decision stream */}
      <div className="mt-3">
        <FilterBar
          className="mb-3"
          filters={[
            {
              id: "dec-status",
              label: "Status",
              value: status,
              options: STATUS_OPTIONS,
              onChange: (v) => setStatus(v as StatusFilter),
            },
            {
              id: "dec-priority",
              label: "Priority",
              value: priority,
              options: PRIORITY_OPTIONS,
              onChange: (v) => setPriority(v as PriorityFilter),
            },
            {
              id: "dec-agent",
              label: "Agent",
              value: agentId,
              options: [
                { value: "all", label: "All agents" },
                ...(agents.data ?? []).map((a) => ({ value: a.id, label: a.name })),
              ],
              onChange: setAgentId,
            },
          ]}
          resultLabel={`${filtered.length} of ${(recs.data ?? []).length} decisions`}
          onReset={
            status !== "all" || priority !== "all" || agentId !== "all"
              ? () => {
                  setStatus("all");
                  setPriority("all");
                  setAgentId("all");
                }
              : undefined
          }
        />

        <ResourceBoundary resource={recs} loading={<LoadingState variant="rows" rows={4} />}>
          {() =>
            filtered.length === 0 ? (
              <EmptyState
                title="No decisions match these filters"
                description="Widen the status, priority or agent filter to see the full decision log."
              />
            ) : (
              <div className={cn("space-y-2.5")}>
                {filtered.map((r, i) => (
                  <RecommendationCard
                    key={r.id}
                    recommendation={r}
                    now={now}
                    defaultOpen={i === 0}
                  />
                ))}
              </div>
            )
          }
        </ResourceBoundary>
      </div>
    </>
  );
}
