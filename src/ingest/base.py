"""Abstract base class for ingestors.

Every ingestor follows the same lifecycle:

    validate() -> read() -> clean() -> to_parquet() -> load_to_duckdb()

``run()`` orchestrates the full lifecycle. Adding a new source type means
subclassing :class:`BaseIngestor`, implementing :meth:`read`, and registering
the class in :mod:`src.ingest.registry`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.config import PROCESSED_DIR, SourceConfig
from src.utils.duckdb_utils import load_parquet_to_table, warehouse_connection
from src.utils.logger import log


class BaseIngestor(ABC):
    """Base class implementing the shared ingestion lifecycle."""

    def __init__(self, config: SourceConfig) -> None:
        self.config = config

    # ------------------------------------------------------------------ #
    # Lifecycle steps
    # ------------------------------------------------------------------ #
    def validate(self) -> list[Path]:
        """Check the source is usable and return the files to ingest."""
        raw_dir = self.config.raw_dir
        if not raw_dir.exists():
            raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")
        files = sorted(raw_dir.glob(self.config.file_pattern))
        if not files:
            raise FileNotFoundError(
                f"No files matching '{self.config.file_pattern}' in {raw_dir}"
            )
        return files

    @abstractmethod
    def read(self, files: list[Path]) -> pd.DataFrame:
        """Read raw files into a single DataFrame."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Light, source-agnostic cleaning. Heavier logic belongs in dbt."""
        # Normalize column names: strip, lowercase, snake_case.
        df = df.rename(
            columns=lambda c: str(c).strip().lower().replace(" ", "_").replace("-", "_")
        )
        # Drop fully-empty rows and exact duplicates on key columns (keep latest file).
        df = df.dropna(how="all")
        if self.config.key_columns:
            keys = [k for k in self.config.key_columns if k in df.columns]
            if keys:
                df = df.drop_duplicates(subset=keys, keep="last")
        # Parse the timestamp column if declared.
        ts = self.config.timestamp_column
        if ts and ts in df.columns:
            df[ts] = pd.to_datetime(df[ts], errors="coerce")
        # Ingestion metadata.
        df["_ingested_at"] = datetime.now(timezone.utc)
        return df

    def to_parquet(self, df: pd.DataFrame) -> Path:
        """Write the cleaned DataFrame to data/processed/<source>.parquet."""
        out_dir = PROCESSED_DIR / self.config.name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{self.config.name}.parquet"
        df.to_parquet(out_path, index=False)
        return out_path

    def load_to_duckdb(self, parquet_path: Path) -> int:
        """Load the Parquet file into the raw schema of the warehouse."""
        with warehouse_connection() as con:
            return load_parquet_to_table(con, str(parquet_path), self.config.raw_table)

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    def run(self) -> int:
        """Run the full lifecycle and return the number of rows loaded."""
        files = self.validate()
        log.info("[{}] reading {} file(s)", self.config.name, len(files))
        df = self.read(files)
        df = self.clean(df)
        parquet_path = self.to_parquet(df)
        rows = self.load_to_duckdb(parquet_path)
        log.info("[{}] loaded {} rows into {}", self.config.name, rows, self.config.raw_table)
        return rows
