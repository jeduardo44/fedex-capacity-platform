"""Ingest runner: entry point for ``make ingest``.

Reads config/sources.yml and runs every source independently — a failure in
one source is logged and the pipeline continues with the others.
"""

from __future__ import annotations

import sys

from src.ingest.registry import get_ingestor
from src.utils.config import load_sources
from src.utils.logger import log


def main() -> int:
    sources = load_sources()
    if not sources:
        log.warning("No sources defined in config/sources.yml")
        return 0

    failures: list[str] = []
    for source in sources:
        try:
            ingestor = get_ingestor(source)
            ingestor.run()
        except Exception as exc:  # noqa: BLE001 - isolate per-source failures
            log.error("[{}] ingestion failed: {}", source.name, exc)
            failures.append(source.name)

    ok = len(sources) - len(failures)
    log.info("Ingestion finished: {}/{} sources succeeded", ok, len(sources))
    if failures:
        log.warning("Failed sources: {}", ", ".join(failures))
    # Only fail the command when *everything* failed.
    return 1 if ok == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
