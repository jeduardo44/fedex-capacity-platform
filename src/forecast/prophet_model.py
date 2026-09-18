"""Prophet forecaster."""

from __future__ import annotations

import logging
from typing import Self

import pandas as pd

from src.forecast.base import BaseForecaster

# Prophet/cmdstanpy are extremely chatty by default.
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").disabled = True


class ProphetForecaster(BaseForecaster):
    name = "prophet"

    def fit(self, df: pd.DataFrame) -> Self:
        from prophet import Prophet  # local import: heavy dependency

        yearly = len(df) >= 2 * self.season_length
        self._model = Prophet(
            yearly_seasonality=yearly,
            weekly_seasonality=self.frequency.startswith("D"),
            daily_seasonality=False,
        )
        self._model.fit(df[["ds", "y"]])
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        future = self._model.make_future_dataframe(
            periods=horizon, freq=self.frequency, include_history=False
        )
        out = self._model.predict(future)
        return out[["ds", "yhat"]].copy()
