"""Generate dummy raw files so the full pipeline can run end-to-end.

Creates:
- data/raw/weekly_demand/demand_export.xlsx  (2 years of weekly demand)
- data/raw/fleet_capacity/fleet_2025.csv     (1 year of daily capacity)

This simulates the files the team would receive from SAP / operations.
Delete data/raw/* and drop real files there when they exist.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.config import PROJECT_ROOT
from src.utils.logger import log

RNG = np.random.default_rng(42)

REGIONS = ["NE", "SE", "MW", "W"]
CATEGORIES = ["express", "ground", "freight"]
HUBS = ["MEM", "IND", "OAK", "EWR"]
VEHICLE_TYPES = ["van", "truck", "trailer"]


def generate_weekly_demand() -> None:
    weeks = pd.date_range(end="2026-09-14", periods=104, freq="W-MON")
    rows = []
    for region_i, region in enumerate(REGIONS):
        base = 8000 + region_i * 3000
        for cat_i, cat in enumerate(CATEGORIES):
            scale = [1.0, 1.8, 0.5][cat_i]
            trend = np.linspace(0, 1500, len(weeks))
            seasonal = 1200 * np.sin(2 * np.pi * np.arange(len(weeks)) / 52)
            noise = RNG.normal(0, 400, len(weeks))
            packages = np.maximum(base * scale + trend + seasonal + noise, 100)
            for week, pkg in zip(weeks, packages):
                rows.append(
                    {
                        "region": region,
                        "week": week.date(),
                        "product_category": cat,
                        "packages": int(pkg),
                    }
                )

    out_dir = PROJECT_ROOT / "data/raw/weekly_demand"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "demand_export.xlsx"
    pd.DataFrame(rows).to_excel(out_path, sheet_name="Sheet1", index=False)
    log.info("Wrote {} ({} rows)", out_path, len(rows))


def generate_fleet_capacity() -> None:
    dates = pd.date_range(end="2026-09-17", periods=365, freq="D")
    rows = []
    for hub_i, hub in enumerate(HUBS):
        for vt_i, vt in enumerate(VEHICLE_TYPES):
            available = 120 + hub_i * 40 + vt_i * 20
            weekday_boost = np.where(dates.dayofweek < 5, 1.0, 0.55)
            seasonal = 0.12 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
            noise = RNG.normal(0, 0.05, len(dates))
            used = available * np.clip(0.72 * weekday_boost + seasonal + noise, 0.2, 0.98)
            for date, u in zip(dates, used):
                rows.append(
                    {
                        "hub": hub,
                        "date": date.date(),
                        "vehicle_type": vt,
                        "vehicles_available": available,
                        "vehicles_used": int(u),
                    }
                )

    out_dir = PROJECT_ROOT / "data/raw/fleet_capacity"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fleet_2025.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    log.info("Wrote {} ({} rows)", out_path, len(rows))


if __name__ == "__main__":
    generate_weekly_demand()
    generate_fleet_capacity()
    log.info("Sample data ready - run 'make ingest' next.")
