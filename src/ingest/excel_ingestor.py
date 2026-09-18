"""Ingestor for Excel files (.xlsx, .xls)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ingest.base import BaseIngestor


class ExcelIngestor(BaseIngestor):
    def read(self, files: list[Path]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for f in files:
            frame = pd.read_excel(
                f,
                sheet_name=self.config.sheet,
                skiprows=self.config.skip_rows,
            )
            frame["_source_file"] = f.name
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)
