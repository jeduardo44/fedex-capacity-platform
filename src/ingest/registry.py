"""Registry mapping source types to ingestor classes.

Adding a new source type: implement the ingestor, then add one line to
``INGESTOR_REGISTRY``.
"""

from __future__ import annotations

from src.ingest.api_ingestor import ApiIngestor
from src.ingest.base import BaseIngestor
from src.ingest.csv_ingestor import CsvIngestor
from src.ingest.excel_ingestor import ExcelIngestor
from src.utils.config import SourceConfig

INGESTOR_REGISTRY: dict[str, type[BaseIngestor]] = {
    "csv": CsvIngestor,
    "excel": ExcelIngestor,
    "api": ApiIngestor,
}


def get_ingestor(config: SourceConfig) -> BaseIngestor:
    try:
        cls = INGESTOR_REGISTRY[config.type]
    except KeyError as exc:
        raise ValueError(
            f"No ingestor registered for type '{config.type}' "
            f"(available: {sorted(INGESTOR_REGISTRY)})"
        ) from exc
    return cls(config)
