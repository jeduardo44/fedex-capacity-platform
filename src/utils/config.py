"""Config loading with Pydantic validation.

Parses config/sources.yml and config/forecasts.yml into typed models so a
malformed config fails fast with a clear error instead of deep in the pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
WAREHOUSE_PATH = DATA_DIR / "warehouse.duckdb"
PROCESSED_DIR = DATA_DIR / "processed"


class SourceConfig(BaseModel):
    """One entry under ``sources:`` in sources.yml."""

    name: str = ""  # filled from the YAML key by load_sources()
    type: Literal["csv", "excel", "api"]
    path: str
    file_pattern: str = "*"
    delimiter: str = ","
    sheet: str | int = 0
    skip_rows: int = 0
    url: str | None = None
    key_columns: list[str] = Field(default_factory=list)
    timestamp_column: str | None = None
    description: str = ""

    @property
    def raw_dir(self) -> Path:
        return PROJECT_ROOT / self.path

    @property
    def raw_table(self) -> str:
        """Table name in the DuckDB ``raw`` schema."""
        return f"raw.{self.name}"


class ForecastConfig(BaseModel):
    """One entry under ``forecasts:`` in forecasts.yml."""

    name: str = ""
    source_table: str
    target_column: str
    group_by: list[str] = Field(default_factory=list)
    frequency: Literal["D", "W", "M"]
    horizon: int = Field(gt=0)
    models: list[Literal["prophet", "autoarima", "ets"]]
    description: str = ""

    @field_validator("models")
    @classmethod
    def at_least_one_model(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("at least one model is required")
        return v


def _read_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_sources(path: Path | None = None) -> list[SourceConfig]:
    raw = _read_yaml(path or CONFIG_DIR / "sources.yml")
    sources: list[SourceConfig] = []
    for name, cfg in (raw.get("sources") or {}).items():
        sources.append(SourceConfig(name=name, **cfg))
    return sources


def load_forecasts(path: Path | None = None) -> list[ForecastConfig]:
    raw = _read_yaml(path or CONFIG_DIR / "forecasts.yml")
    forecasts: list[ForecastConfig] = []
    for name, cfg in (raw.get("forecasts") or {}).items():
        forecasts.append(ForecastConfig(name=name, **cfg))
    return forecasts
