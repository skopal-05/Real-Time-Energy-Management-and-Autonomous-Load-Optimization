"""
Project-wide configuration constants for the Digital Twin System.
"""

from pathlib import Path

# =============================================================================
# Project Directories
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Module 1 Output Directory
MODULE1_BASE_DIR = BASE_DIR.parent / "Module 1 - Data Acquisition"
MODULE1_OUTPUT_DIRECTORY = MODULE1_BASE_DIR / "outputs"

OUTPUT_DIRECTORY = BASE_DIR / "outputs"
STATE_DIRECTORY = OUTPUT_DIRECTORY / "states"
SIMULATION_DIRECTORY = OUTPUT_DIRECTORY / "simulations"
LOG_DIRECTORY = OUTPUT_DIRECTORY / "logs"

# =============================================================================
# Time Settings
# =============================================================================

SAMPLING_INTERVAL = 5          # seconds between sensor updates
SIMULATION_INTERVAL = 60       # seconds between simulation cycles

# =============================================================================
# System Thresholds
# =============================================================================

POWER_THRESHOLD = 0.85         # 85% utilization
TEMPERATURE_THRESHOLD = 30.0   # Celsius

# =============================================================================
# HVAC Operating Limits
# =============================================================================

HVAC_MIN_POWER = 15.0
HVAC_MAX_POWER = 25.0

HVAC_MIN_TEMP = 20.0
HVAC_MAX_TEMP = 30.0

# =============================================================================
# Compressor Operating Limits
# =============================================================================

COMPRESSOR_MIN_POWER = 30.0
COMPRESSOR_MAX_POWER = 60.0

COMPRESSOR_MIN_TEMP = 35.0
COMPRESSOR_MAX_TEMP = 70.0

# =============================================================================
# Default Values
# =============================================================================

DEFAULT_STATUS = "RUNNING"
DEFAULT_HEALTH = "NORMAL"

# =============================================================================
# Logging
# =============================================================================

LOG_LEVEL = "INFO"

# =============================================================================
# Supported Digital Twins
# =============================================================================

SUPPORTED_SYSTEMS = [
    "production_line_a",
    "production_line_b",
    "boiler",
    "solar",
    "battery",
    "grid",
    "hvac",
    "compressor",
]