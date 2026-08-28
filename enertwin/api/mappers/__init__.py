"""Translate module artifacts into the shapes the existing frontend expects.

The contract these mappers satisfy is ``frontend/src/lib/types.ts``, already
implemented against by every screen. Because the frontend's REST adapter
(``src/services/httpDataSource.ts``) was written before the backend existed, the
endpoint paths and payload shapes here are dictated by it - no frontend code
changes to connect the real system.
"""

from enertwin.api.mappers import (
    anomalies,
    assets,
    common,
    decisions,
    energy,
    explain,
    forecasting,
    lifecycle,
    optimization,
    reports,
    system,
)

__all__ = [
    "anomalies",
    "assets",
    "common",
    "decisions",
    "energy",
    "explain",
    "forecasting",
    "lifecycle",
    "optimization",
    "reports",
    "system",
]
