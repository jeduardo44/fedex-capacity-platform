"""statsforecast models (AutoARIMA, ETS)."""

from __future__ import annotations

from typing import Self

import pandas as pd

from src.forecast.base import BaseForecaster


class _StatsForecaster(BaseForecaster):
    """Shared wrapper around statsforecast's fit/predict API."""

    def _build_model(self):  # noqa: ANN202 - statsforecast model instance
        raise NotImplementedError

    def fit(self, df: pd.DataFrame) -> Self:
        from statsforecast import StatsForecast

        sf_df = df[["ds", "y"]].copy()
        sf_df["unique_id"] = "series"
        self._model_name = type(self._build_model()).__name__
        self._sf = StatsForecast(
            models=[self._build_model()], freq=self.frequency, n_jobs=1
        )
        self._sf.fit(sf_df)
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        out = self._sf.predict(h=horizon).reset_index()
        out = out.rename(columns={self._model_name: "yhat"})
        return out[["ds", "yhat"]].copy()


class AutoArimaForecaster(_StatsForecaster):
    name = "autoarima"

    def _build_model(self):  # noqa: ANN202
        from statsforecast.models import AutoARIMA

        return AutoARIMA(season_length=self.season_length)


class EtsForecaster(_StatsForecaster):
    name = "ets"

    def _build_model(self):  # noqa: ANN202
        from statsforecast.models import AutoETS

        return AutoETS(season_length=self.season_length)
