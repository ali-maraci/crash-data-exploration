"""FastAPI dependency injection."""

import pandas as pd

from src.models.lgbm import CrashForecaster

_model: CrashForecaster | None = None
_panel: pd.DataFrame | None = None
_city_model: CrashForecaster | None = None
_city_panel: pd.DataFrame | None = None


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


def get_city_model() -> CrashForecaster:
    assert _city_model is not None, "City model not loaded"
    return _city_model


def get_city_panel() -> pd.DataFrame:
    assert _city_panel is not None, "City panel not loaded"
    return _city_panel


def set_city_model(model: CrashForecaster) -> None:
    global _city_model
    _city_model = model


def set_city_panel(panel: pd.DataFrame) -> None:
    global _city_panel
    _city_panel = panel
