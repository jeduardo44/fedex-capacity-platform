"""Template ingestor for REST API sources.

For API sources there are no local files: ``validate()`` checks the URL is
configured and ``read()`` pulls JSON records into a DataFrame. Adapt the
pagination/auth logic per API when a real source shows up.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

from src.ingest.base import BaseIngestor


class ApiIngestor(BaseIngestor):
    def validate(self) -> list[Path]:
        if not self.config.url:
            raise ValueError(f"Source '{self.config.name}' is type=api but has no url")
        return []  # no local files

    def read(self, files: list[Path]) -> pd.DataFrame:
        assert self.config.url is not None
        with urllib.request.urlopen(self.config.url, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        # Assumes the API returns a list of records; adjust per real API shape.
        records = payload if isinstance(payload, list) else payload.get("data", [])
        df = pd.DataFrame.from_records(records)
        df["_source_file"] = self.config.url
        return df
