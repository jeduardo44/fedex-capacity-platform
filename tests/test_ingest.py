"""Unit tests for the ingest layer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.ingest.csv_ingestor import CsvIngestor
from src.ingest.registry import get_ingestor
from src.utils.config import SourceConfig, load_forecasts, load_sources


@pytest.fixture
def csv_source(tmp_path: Path) -> SourceConfig:
    (tmp_path / "sample.csv").write_text(
        "Hub,Date,Vehicle Type,vehicles_available\n"
        "MEM,2026-01-01,van,100\n"
        "MEM,2026-01-01,van,100\n"  # duplicate on key columns
        "IND,2026-01-02,truck,80\n"
    )
    return SourceConfig(
        name="test_source",
        type="csv",
        path=str(tmp_path),
        file_pattern="*.csv",
        key_columns=["hub", "date", "vehicle_type"],
        timestamp_column="date",
    )


def test_registry_routes_by_type(csv_source: SourceConfig) -> None:
    assert isinstance(get_ingestor(csv_source), CsvIngestor)


def test_registry_rejects_unknown_type(csv_source: SourceConfig) -> None:
    with pytest.raises(Exception):
        SourceConfig(name="x", type="parquet", path="data/raw/x/")  # type: ignore[arg-type]


def test_csv_read_and_clean(csv_source: SourceConfig) -> None:
    # csv_source.path is absolute, so raw_dir resolves straight to the tmp dir.
    ingestor = CsvIngestor(csv_source)

    files = ingestor.validate()
    assert len(files) == 1

    df = ingestor.clean(ingestor.read(files))
    # Column names normalized to snake_case.
    assert {"hub", "date", "vehicle_type", "vehicles_available"} <= set(df.columns)
    # Duplicate row on key columns dropped.
    assert len(df) == 2
    # Timestamp parsed, metadata added.
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert "_ingested_at" in df.columns and "_source_file" in df.columns


def test_validate_fails_on_missing_dir() -> None:
    cfg = SourceConfig(name="ghost", type="csv", path="data/raw/does_not_exist/")
    with pytest.raises(FileNotFoundError):
        CsvIngestor(cfg).validate()


def test_project_configs_are_valid() -> None:
    """The real YAML configs in config/ must parse into Pydantic models."""
    sources = load_sources()
    forecasts = load_forecasts()
    assert {s.name for s in sources} >= {"weekly_demand", "fleet_capacity"}
    assert {f.name for f in forecasts} >= {"demand_by_region", "capacity_utilization"}
