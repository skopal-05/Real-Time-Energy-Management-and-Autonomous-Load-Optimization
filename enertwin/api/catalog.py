"""Plant asset catalogue.

Descriptive metadata about the eight assets - names, roles, locations, rated
capacity - plus the mapping between the frontend's asset ids and Module 2's twin
keys. This is plant configuration, not module output, so it lives here rather
than being derived from a module's artifacts.

Rated capacities are sized to Module 1's dataset, not to the frontend's demo
registry: the demo used a much larger notional plant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AssetId = Literal[
    "line-a", "line-b", "boiler", "compressor", "hvac", "solar", "battery", "grid"
]


@dataclass(frozen=True)
class AssetDescriptor:
    id: str
    twin_key: str
    name: str
    short_name: str
    category: str
    role: str
    description: str
    location: str
    rated_power_kw: float
    #: Twin state field carrying this asset's electrical power, if it has one.
    power_field: str | None
    #: True when positive power in the source data means export/generation.
    power_is_generation: bool = False
    #: Twin state field carrying the asset's efficiency, if measured.
    efficiency_field: str | None = None


CATALOG: tuple[AssetDescriptor, ...] = (
    AssetDescriptor(
        id="line-a",
        twin_key="production_line_a",
        name="Production Line A",
        short_name="Line A",
        category="production",
        role="consumer",
        description=(
            "Primary machining and assembly line. The digital twin tracks motor "
            "load, throughput and vibration, and learns the load-to-throughput "
            "response online."
        ),
        location="Shop Floor - Bay 1",
        rated_power_kw=150.0,
        power_field="machine_load_kw",
    ),
    AssetDescriptor(
        id="line-b",
        twin_key="production_line_b",
        name="Production Line B",
        short_name="Line B",
        category="production",
        role="consumer",
        description=(
            "Secondary finishing and packaging line. Its twin models the same "
            "signals as Line A against an independent duty pattern."
        ),
        location="Shop Floor - Bay 2",
        rated_power_kw=150.0,
        power_field="machine_load_kw",
    ),
    AssetDescriptor(
        id="boiler",
        twin_key="boiler",
        name="Boiler",
        short_name="Boiler",
        category="thermal",
        role="consumer",
        description=(
            "Steam generation for process heat. Fuel-fired: Module 1 meters fuel "
            "flow, steam pressure and flue-gas temperature, but no electrical "
            "load, so this asset contributes fuel cost and emissions rather than "
            "site kW."
        ),
        location="Utilities Block",
        rated_power_kw=0.0,
        power_field=None,
        efficiency_field="efficiency_percent",
    ),
    AssetDescriptor(
        id="compressor",
        twin_key="compressor",
        name="Compressor",
        short_name="Compressor",
        category="utility",
        role="consumer",
        description=(
            "Compressed-air supply for pneumatics across both lines. Load/unload "
            "cycling dominates its energy signature."
        ),
        location="Utilities Block",
        rated_power_kw=80.0,
        power_field="power_kw",
        efficiency_field="efficiency_percent",
    ),
    AssetDescriptor(
        id="hvac",
        twin_key="hvac",
        name="HVAC",
        short_name="HVAC",
        category="utility",
        role="consumer",
        description=(
            "Chillers and air handling for the shop floor. Strongly driven by "
            "ambient temperature and the zone setpoint."
        ),
        location="Roof Plant Room",
        rated_power_kw=25.0,
        power_field="power_kw",
        efficiency_field="efficiency_percent",
    ),
    AssetDescriptor(
        id="solar",
        twin_key="solar",
        name="Solar PV Array",
        short_name="Solar",
        category="generation",
        role="producer",
        description=(
            "Rooftop photovoltaic array. The twin models irradiance, panel "
            "temperature derating and inverter conversion."
        ),
        location="Rooftop - North & South",
        rated_power_kw=400.0,
        power_field="inverter_power_kw",
        power_is_generation=True,
    ),
    AssetDescriptor(
        id="battery",
        twin_key="battery",
        name="Battery Storage",
        short_name="Battery",
        category="storage",
        role="storage",
        description=(
            "Lithium-ion storage used for peak shaving and solar time-shifting. "
            "In Module 1's convention positive power means charging."
        ),
        location="Energy Yard",
        rated_power_kw=100.0,
        power_field="battery_power_kw",
    ),
    AssetDescriptor(
        id="grid",
        twin_key="grid",
        name="Grid Connection",
        short_name="Grid",
        category="supply",
        role="bidirectional",
        description=(
            "Utility point of common coupling. Import and export are metered "
            "here and priced against the tariff schedule."
        ),
        location="Substation - PCC",
        rated_power_kw=600.0,
        power_field=None,  # computed as import - export
    ),
)

BY_ID: dict[str, AssetDescriptor] = {item.id: item for item in CATALOG}
BY_TWIN_KEY: dict[str, AssetDescriptor] = {item.twin_key: item for item in CATALOG}
ASSET_IDS: tuple[str, ...] = tuple(item.id for item in CATALOG)

#: Assets whose metered electrical power makes up site demand.
ELECTRICAL_CONSUMERS: tuple[str, ...] = ("line-a", "line-b", "compressor", "hvac")

#: Contracted maximum demand at the point of common coupling, in kW.
DEMAND_CAP_KW = 700.0

CURRENCY = "INR"

#: Human labels and units for twin state fields the UI surfaces as metrics.
METRIC_LABELS: dict[str, tuple[str, str]] = {
    "machine_load_kw": ("Machine Load", "kW"),
    "units_per_hour": ("Throughput", "units/h"),
    "motor_temperature_c": ("Motor Temperature", "°C"),
    "vibration_mm_s": ("Vibration RMS", "mm/s"),
    "steam_pressure_bar": ("Steam Pressure", "bar"),
    "steam_flow_kg_hr": ("Steam Flow", "kg/h"),
    "fuel_flow_m3_hr": ("Fuel Flow", "m³/h"),
    "feedwater_temperature_c": ("Feedwater Temperature", "°C"),
    "flue_gas_temperature_c": ("Flue Gas Temperature", "°C"),
    "efficiency_percent": ("Efficiency", "%"),
    "air_flow_m3_min": ("Air Flow", "m³/min"),
    "air_pressure_bar": ("Discharge Pressure", "bar"),
    "power_kw": ("Electrical Power", "kW"),
    "temperature_c": ("Temperature", "°C"),
    "airflow_m3_min": ("Air Flow", "m³/min"),
    "humidity_percent": ("Relative Humidity", "%"),
    "setpoint_temperature_c": ("Zone Setpoint", "°C"),
    "irradiance_w_m2": ("Irradiance", "W/m²"),
    "dc_power_kw": ("DC Power", "kW"),
    "inverter_power_kw": ("AC Output", "kW"),
    "panel_temperature_c": ("Panel Temperature", "°C"),
    "state_of_charge_percent": ("State of Charge", "%"),
    "battery_power_kw": ("Battery Power", "kW"),
    "voltage_v": ("Voltage", "V"),
    "current_a": ("Current", "A"),
    "grid_import_kw": ("Grid Import", "kW"),
    "grid_export_kw": ("Grid Export", "kW"),
    "frequency_hz": ("Frequency", "Hz"),
    "power_factor": ("Power Factor", ""),
    "tariff_inr_kwh": ("Tariff", "₹/kWh"),
}

#: Measured fields shown per asset, in display order. Engineered features
#: (lags, rolling statistics, calendar encodings) are deliberately excluded -
#: they are model inputs, not operator-facing readings.
ASSET_METRIC_FIELDS: dict[str, tuple[str, ...]] = {
    "line-a": (
        "machine_load_kw",
        "units_per_hour",
        "motor_temperature_c",
        "vibration_mm_s",
    ),
    "line-b": (
        "machine_load_kw",
        "units_per_hour",
        "motor_temperature_c",
        "vibration_mm_s",
    ),
    "boiler": (
        "fuel_flow_m3_hr",
        "steam_pressure_bar",
        "steam_flow_kg_hr",
        "feedwater_temperature_c",
        "flue_gas_temperature_c",
        "efficiency_percent",
    ),
    "compressor": (
        "power_kw",
        "air_pressure_bar",
        "air_flow_m3_min",
        "motor_temperature_c",
        "vibration_mm_s",
        "efficiency_percent",
    ),
    "hvac": (
        "power_kw",
        "temperature_c",
        "setpoint_temperature_c",
        "airflow_m3_min",
        "humidity_percent",
        "efficiency_percent",
    ),
    "solar": (
        "inverter_power_kw",
        "dc_power_kw",
        "irradiance_w_m2",
        "panel_temperature_c",
    ),
    "battery": (
        "battery_power_kw",
        "state_of_charge_percent",
        "voltage_v",
        "current_a",
        "temperature_c",
    ),
    "grid": (
        "grid_import_kw",
        "grid_export_kw",
        "tariff_inr_kwh",
        "frequency_hz",
        "voltage_v",
        "power_factor",
    ),
}

#: Headline metric per asset - the one shown on the asset card.
HEADLINE_FIELD: dict[str, str] = {
    "line-a": "machine_load_kw",
    "line-b": "machine_load_kw",
    "boiler": "fuel_flow_m3_hr",
    "compressor": "power_kw",
    "hvac": "power_kw",
    "solar": "inverter_power_kw",
    "battery": "state_of_charge_percent",
    "grid": "grid_import_kw",
}

#: Operating envelopes used for warning thresholds, taken from Module 2's own
#: declared twin ranges where the twins declare one.
METRIC_BOUNDS: dict[tuple[str, str], dict[str, float]] = {
    ("line-a", "motor_temperature_c"): {"warnAbove": 70.0, "min": 0.0, "max": 100.0},
    ("line-b", "motor_temperature_c"): {"warnAbove": 70.0, "min": 0.0, "max": 100.0},
    ("line-a", "vibration_mm_s"): {"warnAbove": 4.5, "min": 0.0, "max": 10.0},
    ("line-b", "vibration_mm_s"): {"warnAbove": 4.5, "min": 0.0, "max": 10.0},
    ("boiler", "efficiency_percent"): {"warnBelow": 80.0, "min": 0.0, "max": 100.0},
    ("boiler", "steam_pressure_bar"): {"min": 0.0, "max": 20.0, "warnAbove": 15.0},
    ("boiler", "flue_gas_temperature_c"): {"warnAbove": 220.0},
    ("compressor", "efficiency_percent"): {"warnBelow": 87.0, "min": 0.0, "max": 100.0},
    ("compressor", "motor_temperature_c"): {"warnAbove": 70.0},
    ("compressor", "vibration_mm_s"): {"warnAbove": 4.5},
    ("hvac", "efficiency_percent"): {"warnBelow": 87.0, "min": 0.0, "max": 100.0},
    ("hvac", "temperature_c"): {"min": 0.0, "max": 50.0, "warnAbove": 28.0},
    ("battery", "state_of_charge_percent"): {
        "min": 0.0,
        "max": 100.0,
        "warnBelow": 20.0,
    },
    ("grid", "frequency_hz"): {"min": 45.0, "max": 55.0, "warnBelow": 49.5},
    ("grid", "power_factor"): {"min": 0.0, "max": 1.0, "warnBelow": 0.90},
}
