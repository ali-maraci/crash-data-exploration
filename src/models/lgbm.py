"""LightGBM crash count forecaster."""

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

# Columns used for training (everything except identifiers and targets)
_EXCLUDE_COLS = {"date", "h3_cell", "crash_count", "injury_crash_count", "fatal_crash_count"}


def _feature_cols(df: pd.DataFrame) -> list[str]:
    return [
        c for c in df.columns
        if c not in _EXCLUDE_COLS and pd.api.types.is_numeric_dtype(df[c])
    ]


class CrashForecaster:
    """LightGBM regression forecaster for daily crash counts."""

    def __init__(
        self,
        target: str = "crash_count",
        params: dict | None = None,
    ):
        self.target = target
        self.params = params or {
            "objective": "regression",
            "metric": "mae",
            "n_estimators": 500,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_child_samples": 20,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "verbose": -1,
        }
        self._model: lgb.LGBMRegressor | None = None
        self._feature_cols: list[str] = []

    def fit(self, train: pd.DataFrame) -> "CrashForecaster":
        self._feature_cols = _feature_cols(train)
        X = train[self._feature_cols]
        y = train[self.target]
        self._model = lgb.LGBMRegressor(**self.params)
        self._model.fit(X, y)
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Recursive multi-step forecast with updated calendar and lag features."""
        has_cells = "h3_cell" in panel.columns
        last_date = panel["date"].max()
        results = []

        if has_cells:
            cells = panel["h3_cell"].unique()
            groups = {cell: panel[panel["h3_cell"] == cell].sort_values("date") for cell in cells}
        else:
            cells = ["__city__"]
            groups = {"__city__": panel.sort_values("date")}

        # Build per-group recent history for lag updates
        histories: dict[str, list[float]] = {}
        for key, grp in groups.items():
            histories[key] = grp[self.target].tolist()

        for step in range(1, horizon + 1):
            forecast_date = last_date + pd.Timedelta(days=step)

            for key in cells:
                row = groups[key].iloc[-1:].copy()

                # Update calendar features for the forecast date
                for col in self._feature_cols:
                    if col == "day_of_week":
                        row[col] = forecast_date.dayofweek
                    elif col == "month":
                        row[col] = forecast_date.month
                    elif col == "is_weekend":
                        row[col] = int(forecast_date.dayofweek >= 5)
                    elif col == "day_of_year":
                        row[col] = forecast_date.dayofyear

                # Update lag features from history + prior predictions
                history = histories[key]
                for col in self._feature_cols:
                    if col.startswith(f"{self.target}_lag_"):
                        lag = int(col.split("_")[-1])
                        if lag <= len(history):
                            row[col] = history[-lag]
                    elif col.startswith(f"{self.target}_roll_") and "_mean" in col:
                        window = int(col.split("_")[3])
                        vals = history[-window:] if len(history) >= window else history
                        row[col] = np.mean(vals) if vals else 0.0
                    elif col.startswith(f"{self.target}_roll_") and "_sum" in col:
                        window = int(col.split("_")[3])
                        vals = history[-window:] if len(history) >= window else history
                        row[col] = np.sum(vals) if vals else 0.0

                X = row[self._feature_cols]
                pred = max(0.0, float(self._model.predict(X)[0]))

                result = {"date": forecast_date, "predicted": pred}
                if has_cells:
                    result["h3_cell"] = key
                results.append(result)

                histories[key].append(pred)

        return pd.DataFrame(results).reset_index(drop=True)

    def feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"feature": self._feature_cols, "importance": self._model.feature_importances_}
        ).sort_values("importance", ascending=False)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model.booster_.save_model(str(path))
        # Save metadata alongside
        meta = {"target": self.target, "feature_cols": self._feature_cols}
        Path(str(path) + ".meta.json").write_text(json.dumps(meta))

    @classmethod
    def load(cls, path: Path, target: str = "crash_count") -> "CrashForecaster":
        obj = cls(target=target)
        booster = lgb.Booster(model_file=str(path))
        obj._model = lgb.LGBMRegressor()
        obj._model._Booster = booster
        obj._model.fitted_ = True
        obj._model._n_features = booster.num_feature()

        meta_path = Path(str(path) + ".meta.json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            obj._feature_cols = meta["feature_cols"]
        return obj
