"""Production-line load balancing agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class LoadBalancingAgent:
    """Allocate limited power across production lines using weighted fairness."""

    name = "load_balancing_agent"

    def balance(
        self,
        lines: Mapping[str, Mapping[str, Any]],
        available_power_kw: float,
    ) -> AgentRecommendation:
        if not lines:
            raise ValueError("at least one production line is required")
        available = number(
            {"available_power_kw": available_power_kw},
            "available_power_kw",
            minimum=0,
        )

        parsed: dict[str, dict[str, float]] = {}
        for line_id, line in lines.items():
            requested = number(line, "requested_power_kw", minimum=0)
            minimum = number(line, "minimum_power_kw", default=0, minimum=0)
            maximum = number(
                line,
                "maximum_power_kw",
                default=requested,
                minimum=minimum,
            )
            priority = number(line, "priority_weight", default=1, minimum=0.01)
            parsed[str(line_id)] = {
                "requested": min(requested, maximum),
                "minimum": min(minimum, requested, maximum),
                "priority": priority,
            }

        total_requested = sum(item["requested"] for item in parsed.values())
        allocations = {line_id: 0.0 for line_id in parsed}
        total_minimum = sum(item["minimum"] for item in parsed.values())

        if available < total_minimum:
            weighted_minimum = sum(
                item["minimum"] * item["priority"] for item in parsed.values()
            )
            if weighted_minimum:
                for line_id, item in parsed.items():
                    share = item["minimum"] * item["priority"] / weighted_minimum
                    allocations[line_id] = min(item["minimum"], available * share)
                unallocated = available - sum(allocations.values())
                for line_id, item in sorted(
                    parsed.items(), key=lambda pair: pair[1]["priority"], reverse=True
                ):
                    addition = min(item["minimum"] - allocations[line_id], unallocated)
                    allocations[line_id] += addition
                    unallocated -= addition
                    if unallocated <= 1e-9:
                        break
        else:
            allocations = {
                line_id: item["minimum"] for line_id, item in parsed.items()
            }
            remaining = min(available, total_requested) - total_minimum
            active = set(parsed)
            while remaining > 1e-9 and active:
                weight_total = sum(parsed[line_id]["priority"] for line_id in active)
                distributed = 0.0
                for line_id in tuple(active):
                    item = parsed[line_id]
                    unmet = item["requested"] - allocations[line_id]
                    addition = min(unmet, remaining * item["priority"] / weight_total)
                    allocations[line_id] += addition
                    distributed += addition
                    if item["requested"] - allocations[line_id] <= 1e-9:
                        active.remove(line_id)
                if distributed <= 1e-9:
                    break
                remaining -= distributed

        allocated = sum(allocations.values())
        curtailed = max(0.0, total_requested - allocated)
        return AgentRecommendation(
            agent=self.name,
            action="rebalance_load" if curtailed > 0.01 else "serve_requested_load",
            priority="high" if curtailed > total_requested * 0.20 else (
                "medium" if curtailed > 0.01 else "low"
            ),
            reason=(
                "Available power is below requested production demand."
                if curtailed > 0.01
                else "Available power can serve all production requests."
            ),
            setpoints={
                "line_power_targets_kw": rounded(allocations),
                "total_power_target_kw": round(allocated, 2),
            },
            expected_impact=rounded(
                {
                    "requested_power_kw": total_requested,
                    "allocated_power_kw": allocated,
                    "curtailed_power_kw": curtailed,
                }
            ),
            constraints=(
                "line minimum and maximum power limits",
                "priority-weighted fairness during shortages",
            ),
        )

    decide = balance
