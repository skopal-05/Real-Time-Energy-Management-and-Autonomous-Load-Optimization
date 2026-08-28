"""Module 2 twin history -> energy time series, source shares and flow.

Site demand is the sum of the metered electrical consumers (both production
lines, the compressor and HVAC). The boiler is fuel-fired and carries no metered
electrical load, so it contributes fuel cost and emissions rather than kW.

Module 1 generates each asset's telemetry independently, so metered grid import
does not equal metered demand minus generation. Nothing here forces them to
balance: measured values are reported as measured, and the flow view derives its
links from them.
"""

from __future__ import annotations

from typing import Any, Mapping

from enertwin.api.catalog import BY_ID, ELECTRICAL_CONSUMERS
from enertwin.api.mappers.common import iso, number, percent, rounded
from enertwin.orchestration import Snapshot

#: Module 1's cleaned dataset is sampled every 15 minutes.
SAMPLE_MINUTES = 15


def _reading(states: Mapping[str, Any]) -> dict[str, Any] | None:
    timestamp = None
    for state in states.values():
        if isinstance(state, Mapping) and state.get("timestamp"):
            timestamp = iso(state["timestamp"])
            break
    if timestamp is None:
        return None

    consumption = 0.0
    for asset_id in ELECTRICAL_CONSUMERS:
        descriptor = BY_ID[asset_id]
        state = states.get(descriptor.twin_key)
        value = number(state, descriptor.power_field or "") if state else None
        if value is not None:
            consumption += value

    solar = number(states.get("solar"), "inverter_power_kw") or 0.0
    # Module 1 signs battery power positive while charging; the frontend's
    # EnergyReading signs it positive while discharging to site.
    battery_raw = number(states.get("battery"), "battery_power_kw")
    battery = -battery_raw if battery_raw is not None else 0.0
    soc = number(states.get("battery"), "state_of_charge_percent")

    grid_import = number(states.get("grid"), "grid_import_kw") or 0.0
    grid_export = number(states.get("grid"), "grid_export_kw") or 0.0

    return {
        "timestamp": timestamp,
        "consumptionKw": round(consumption, 2),
        "generationKw": round(solar + max(battery, 0.0), 2),
        "solarKw": round(solar, 2),
        "batteryKw": round(battery, 2),
        "gridKw": round(grid_import - grid_export, 2),
        "batterySocPct": round(soc, 2) if soc is not None else 0.0,
    }


def build_energy_window(
    snapshot: Snapshot, hours: float, step_minutes: int
) -> list[dict[str, Any]]:
    history = (snapshot.twin or {}).get("history", []) or []
    readings = [r for r in (_reading(states) for states in history) if r]

    wanted = max(1, int(hours * 60 / SAMPLE_MINUTES))
    readings = readings[-wanted:]

    # Down-sample when the caller asks for a coarser step than the dataset has.
    stride = max(1, round(step_minutes / SAMPLE_MINUTES))
    return readings[::stride] if stride > 1 else readings


def build_source_shares(snapshot: Snapshot, hours: float) -> list[dict[str, Any]]:
    """Energy by source over the window, integrated from measured power."""

    readings = build_energy_window(snapshot, hours, SAMPLE_MINUTES)
    if not readings:
        return []

    interval_hours = SAMPLE_MINUTES / 60
    solar_kwh = sum(max(r["solarKw"], 0.0) for r in readings) * interval_hours
    battery_kwh = sum(max(r["batteryKw"], 0.0) for r in readings) * interval_hours
    grid_kwh = sum(max(r["gridKw"], 0.0) for r in readings) * interval_hours
    supplied = solar_kwh + battery_kwh + grid_kwh

    return [
        {
            "source": label,
            "energyKwh": round(value, 2),
            "sharePct": percent(value, supplied) or 0.0,
            "colorToken": token,
        }
        for label, value, token in (
            ("Solar", solar_kwh, "solar"),
            ("Battery", battery_kwh, "battery"),
            ("Grid", grid_kwh, "grid"),
        )
    ]


def build_energy_flow(snapshot: Snapshot) -> dict[str, Any]:
    """Current power flow between sources, the busbar and the loads."""

    history = (snapshot.twin or {}).get("history", []) or []
    latest = _reading(history[-1]) if history else None
    states = history[-1] if history else {}

    if latest is None:
        return {
            "timestamp": snapshot.finished_at,
            "nodes": [],
            "links": [],
            "origin": "unavailable",
        }

    solar = max(latest["solarKw"], 0.0)
    battery = latest["batteryKw"]  # + discharging, - charging
    grid_import = max(latest["gridKw"], 0.0)
    grid_export = max(-latest["gridKw"], 0.0)

    nodes: list[dict[str, Any]] = [
        {
            "id": "solar",
            "label": "Solar PV",
            "kind": "source",
            "powerKw": round(solar, 2),
            "status": "online" if solar > 1 else "offline",
            "assetId": "solar",
            "detail": f"{solar:.1f} kW inverter output",
        },
        {
            "id": "grid",
            "label": "Grid",
            "kind": "source",
            "powerKw": round(grid_import - grid_export, 2),
            "status": "online",
            "assetId": "grid",
            "detail": (
                f"importing {grid_import:.1f} kW"
                if grid_import >= grid_export
                else f"exporting {grid_export:.1f} kW"
            ),
        },
        {
            "id": "bus",
            "label": "Site Busbar",
            "kind": "hub",
            "powerKw": round(latest["consumptionKw"], 2),
            "status": "online",
            "detail": f"{latest['consumptionKw']:.1f} kW metered demand",
        },
        {
            "id": "battery",
            "label": "Battery",
            "kind": "storage",
            "powerKw": round(battery, 2),
            "status": "online",
            "assetId": "battery",
            "detail": (
                f"discharging {battery:.1f} kW"
                if battery > 0
                else f"charging {abs(battery):.1f} kW"
            ),
        },
    ]

    links: list[dict[str, Any]] = [
        {
            "from": "solar",
            "to": "bus",
            "powerKw": round(solar, 2),
            "colorToken": "solar",
            "active": solar > 1,
        },
        {
            "from": "grid",
            "to": "bus",
            "powerKw": round(grid_import, 2),
            "colorToken": "grid",
            "active": grid_import > 1,
        },
        {
            "from": "battery",
            "to": "bus",
            "powerKw": round(max(battery, 0.0), 2),
            "colorToken": "battery",
            "active": battery > 1,
        },
        {
            "from": "bus",
            "to": "battery",
            "powerKw": round(max(-battery, 0.0), 2),
            "colorToken": "battery",
            "active": battery < -1,
        },
        {
            "from": "bus",
            "to": "grid",
            "powerKw": round(grid_export, 2),
            "colorToken": "grid",
            "active": grid_export > 1,
        },
    ]

    for asset_id in ELECTRICAL_CONSUMERS:
        descriptor = BY_ID[asset_id]
        state = states.get(descriptor.twin_key)
        load = number(state, descriptor.power_field or "") if state else None
        load = load or 0.0
        nodes.append(
            {
                "id": descriptor.id,
                "label": descriptor.short_name,
                "kind": "sink",
                "powerKw": round(load, 2),
                "status": "online" if load > 0.5 else "offline",
                "assetId": descriptor.id,
                "detail": descriptor.location,
            }
        )
        links.append(
            {
                "from": "bus",
                "to": descriptor.id,
                "powerKw": round(load, 2),
                "colorToken": "load",
                "active": load > 0.5,
            }
        )

    # The boiler is a real plant load but a fuel-fired one, so it appears in the
    # topology carrying no electrical power rather than being hidden.
    fuel = number(states.get("boiler"), "fuel_flow_m3_hr")
    nodes.append(
        {
            "id": "boiler",
            "label": BY_ID["boiler"].short_name,
            "kind": "sink",
            "powerKw": 0.0,
            "status": "online" if fuel else "offline",
            "assetId": "boiler",
            "detail": (
                f"fuel-fired - {fuel:.1f} m³/h, no metered electrical load"
                if fuel is not None
                else "fuel-fired - no metered electrical load"
            ),
        }
    )
    links.append(
        {
            "from": "bus",
            "to": "boiler",
            "powerKw": 0.0,
            "colorToken": "load",
            "active": False,
        }
    )

    return {
        "timestamp": latest["timestamp"],
        "nodes": nodes,
        "links": links,
        "origin": "live",
    }


def site_totals(snapshot: Snapshot, hours: float) -> dict[str, Any]:
    """Aggregate energy figures used by the status and report endpoints."""

    readings = build_energy_window(snapshot, hours, SAMPLE_MINUTES)
    if not readings:
        return {}

    interval_hours = SAMPLE_MINUTES / 60
    consumption_kwh = sum(r["consumptionKw"] for r in readings) * interval_hours
    generation_kwh = sum(r["generationKw"] for r in readings) * interval_hours
    import_kwh = sum(max(r["gridKw"], 0.0) for r in readings) * interval_hours
    export_kwh = sum(max(-r["gridKw"], 0.0) for r in readings) * interval_hours
    peak_kw = max(r["consumptionKw"] for r in readings)
    average_kw = consumption_kwh / (len(readings) * interval_hours)
    solar_kwh = sum(max(r["solarKw"], 0.0) for r in readings) * interval_hours
    supplied_kwh = solar_kwh + import_kwh

    return {
        "consumptionKwh": round(consumption_kwh, 2),
        "generationKwh": round(generation_kwh, 2),
        "gridImportKwh": round(import_kwh, 2),
        "gridExportKwh": round(export_kwh, 2),
        "renewableSharePct": percent(solar_kwh, supplied_kwh) or 0.0,
        "peakDemandKw": round(peak_kw, 2),
        "averageLoadKw": round(average_kw, 2),
        "loadFactorPct": percent(average_kw, peak_kw) or 0.0,
        "readingCount": len(readings),
        "latest": readings[-1],
        "rangeStart": readings[0]["timestamp"],
        "rangeEnd": readings[-1]["timestamp"],
    }


__all__ = [
    "SAMPLE_MINUTES",
    "build_energy_flow",
    "build_energy_window",
    "build_source_shares",
    "site_totals",
]
