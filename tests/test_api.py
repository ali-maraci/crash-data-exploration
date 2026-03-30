from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.deps import get_model, get_panel


@pytest.fixture
def mock_model():
    model = MagicMock()
    model.predict.return_value = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=7, freq="D"),
            "h3_cell": ["cell_a"] * 7,
            "predicted": [5.0] * 7,
        }
    )
    return model


@pytest.fixture
def mock_panel():
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    rows = []
    for d in dates:
        for cell in ["cell_a", "cell_b"]:
            rows.append(
                {
                    "date": d,
                    "h3_cell": cell,
                    "crash_count": 3,
                    "injury_crash_count": 1,
                    "fatal_crash_count": 0,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def client(mock_model, mock_panel):
    app = create_app()
    app.dependency_overrides[get_model] = lambda: mock_model
    app.dependency_overrides[get_panel] = lambda: mock_panel
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_forecast_city_returns_200(client):
    resp = client.get("/forecast/city")
    assert resp.status_code == 200
    data = resp.json()
    assert "forecasts" in data
    assert "model_name" in data


def test_forecast_city_custom_horizon(client):
    resp = client.get("/forecast/city?horizon=14")
    assert resp.status_code == 200


def test_hotspot_returns_404_for_invalid_cell(client):
    resp = client.get("/hotspot/invalid_cell_id")
    assert resp.status_code == 404


def test_hotspots_top_returns_list(client):
    resp = client.get("/hotspots/top?n=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "hotspots" in data
    assert len(data["hotspots"]) <= 5


def test_forecast_city_with_as_of_date(client):
    resp = client.get("/forecast/city?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "forecasts" in data
    assert "as_of_date" in data
    assert data["as_of_date"] == "2023-01-15"


def test_forecast_city_with_as_of_date_includes_actuals(client):
    resp = client.get("/forecast/city?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    for point in data["forecasts"]:
        assert "actual_value" in point


def test_forecast_city_without_as_of_date_uses_panel_end(client):
    resp = client.get("/forecast/city?horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "as_of_date" in data


def test_hotspot_with_as_of_date(client):
    resp = client.get("/hotspot/cell_a?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "as_of_date" in data
