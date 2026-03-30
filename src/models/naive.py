"""Baseline forecasting models."""

import pandas as pd


class SeasonalNaive:
    """Predict by repeating the last full season."""

    def __init__(self, season_length: int = 7):
        self.season_length = season_length
        self._last_season: list[float] = []
        self._last_date: pd.Timestamp | None = None

    def fit(self, train: pd.DataFrame) -> "SeasonalNaive":
        train = train.sort_values("date")
        self._last_season = train["crash_count"].iloc[-self.season_length :].tolist()
        self._last_date = train["date"].iloc[-1]
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        preds = [self._last_season[i % self.season_length] for i in range(horizon)]
        dates = pd.date_range(self._last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        return pd.DataFrame({"date": dates, "predicted": preds})


class MovingAverage:
    """Predict using trailing window mean."""

    def __init__(self, window: int = 7):
        self.window = window
        self._mean: float = 0.0
        self._last_date: pd.Timestamp | None = None

    def fit(self, train: pd.DataFrame) -> "MovingAverage":
        train = train.sort_values("date")
        self._mean = train["crash_count"].iloc[-self.window :].mean()
        self._last_date = train["date"].iloc[-1]
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        dates = pd.date_range(self._last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        return pd.DataFrame({"date": dates, "predicted": [self._mean] * horizon})
