"""Export Plotly figures to standalone HTML files.

Useful outside Quarto, e.g. to email a single chart. The generated file is
fully self-contained (plotly.js inlined) and opens in any browser.
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go

from src.utils.logger import log


def figure_to_html(fig: go.Figure, output_path: Path, title: str | None = None) -> Path:
    """Write a Plotly figure as a self-contained interactive HTML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if title:
        fig.update_layout(title=title)
    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)
    log.info("Wrote {}", output_path)
    return output_path
