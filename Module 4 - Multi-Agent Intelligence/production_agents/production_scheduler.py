"""Tariff- and renewable-aware production scheduler."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from contracts import AgentRecommendation, number


class ProductionScheduler:
    """Assign indivisible production jobs to feasible energy time slots."""

    name = "production_scheduler"

    def schedule(
        self,
        jobs: Sequence[Mapping[str, Any]],
        slots: Sequence[Mapping[str, Any]],
    ) -> AgentRecommendation:
        if not jobs:
            raise ValueError("at least one production job is required")
        if not slots:
            raise ValueError("at least one scheduling slot is required")

        slot_state: list[dict[str, Any]] = []
        for index, slot in enumerate(slots):
            slot_id = str(slot.get("slot_id", index))
            capacity = number(slot, "capacity_kwh", minimum=0)
            renewable = number(slot, "renewable_kwh", default=0, minimum=0)
            tariff = number(slot, "tariff_inr_kwh", minimum=0)
            slot_state.append(
                {
                    "slot_id": slot_id,
                    "order": index,
                    "remaining": capacity,
                    "renewable": min(renewable, capacity),
                    "tariff": tariff,
                }
            )

        parsed_jobs: list[dict[str, Any]] = []
        for index, job in enumerate(jobs):
            job_id = str(job.get("job_id", "")).strip()
            if not job_id:
                raise ValueError(f"job at index {index} is missing job_id")
            energy = number(job, "energy_kwh", minimum=0)
            deadline = int(number(job, "deadline_slot", minimum=0))
            priority = number(job, "priority_weight", default=1, minimum=0.01)
            parsed_jobs.append(
                {
                    "job_id": job_id,
                    "energy": energy,
                    "deadline": deadline,
                    "priority": priority,
                }
            )

        parsed_jobs.sort(key=lambda job: (job["deadline"], -job["priority"], -job["energy"]))
        assignments: list[dict[str, Any]] = []
        unscheduled: list[str] = []
        cost = 0.0
        renewable_used = 0.0

        for job in parsed_jobs:
            candidates = [
                slot
                for slot in slot_state
                if slot["order"] <= job["deadline"] and slot["remaining"] >= job["energy"]
            ]
            if not candidates:
                unscheduled.append(job["job_id"])
                continue
            selected = min(
                candidates,
                key=lambda slot: (
                    max(0.0, job["energy"] - min(slot["renewable"], slot["remaining"]))
                    * slot["tariff"],
                    slot["order"],
                ),
            )
            renewable_for_job = min(job["energy"], selected["renewable"])
            grid_for_job = job["energy"] - renewable_for_job
            job_cost = grid_for_job * selected["tariff"]
            selected["remaining"] -= job["energy"]
            selected["renewable"] -= renewable_for_job
            renewable_used += renewable_for_job
            cost += job_cost
            assignments.append(
                {
                    "job_id": job["job_id"],
                    "slot_id": selected["slot_id"],
                    "energy_kwh": round(job["energy"], 2),
                    "renewable_kwh": round(renewable_for_job, 2),
                    "grid_kwh": round(grid_for_job, 2),
                    "estimated_cost_inr": round(job_cost, 2),
                }
            )

        return AgentRecommendation(
            agent=self.name,
            action="schedule_production" if not unscheduled else "schedule_with_capacity_alert",
            priority="high" if unscheduled else "low",
            reason=(
                "One or more jobs cannot meet their energy/deadline constraints."
                if unscheduled
                else "All jobs were assigned to the lowest-cost feasible slots."
            ),
            setpoints={
                "assignments": assignments,
                "unscheduled_jobs": unscheduled,
            },
            expected_impact={
                "scheduled_jobs": float(len(assignments)),
                "unscheduled_jobs": float(len(unscheduled)),
                "renewable_energy_used_kwh": round(renewable_used, 2),
                "estimated_energy_cost_inr": round(cost, 2),
            },
            constraints=(
                "jobs are indivisible",
                "jobs must complete no later than deadline_slot",
                "slot energy capacity cannot be exceeded",
            ),
        )

    decide = schedule
