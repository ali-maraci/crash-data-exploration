"""FastAPI dependency injection."""

import pandas as pd

from src.models.lgbm import CrashForecaster

_model: CrashForecaster | None = None
_panel: pd.DataFrame | None = None


def get_model() -> CrashForecaster:
    assert _model is not None, "Model not loaded"
    return _model


def get_panel() -> pd.DataFrame:
    assert _panel is not None, "Panel not loaded"
    return _panel


def set_model(model: CrashForecaster) -> None:
    global _model
    _model = model


def set_panel(panel: pd.DataFrame) -> None:
    global _panel
    _panel = panel
