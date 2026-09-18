"""Abstract base class for forecasters.

All forecasters consume a univariate series as a DataFrame with columns
``ds`` (datetime) and ``y`` (numeric), and produce a DataFrame with columns
``ds`` and ``yhat`` for the requested horizon. This keeps models pluggable:
the runner does not care which library sits behind a forecaster.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

import pandas as pd


class BaseForecaster(ABC):
    """Interface every forecasting model must implement."""

    #: identifier used in config/forecasts.yml under ``models:``
    name: str = "base"

    def __init__(self, frequency: str, season_length: int) -> None:
        """
        Args:
            frequency: pandas offset alias for the series (e.g. "D", "W-MON").
            season_length: seasonal period in steps (7 for daily, 52 for weekly).
        """
        self.frequency = frequency
        self.season_length = season_length

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> Self:
        """Fit on a DataFrame with columns ``ds`` and ``y``."""

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Forecast ``horizon`` steps ahead; returns columns ``ds`` and ``yhat``."""
