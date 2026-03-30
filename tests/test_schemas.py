from datetime import date, datetime

from src.api.schemas import CityForecastResponse, ForecastPoint, HotspotSummary


def test_forecast_point_serializes_correctly():
    fp = ForecastPoint(date=date(2024, 1, 1), predicted_value=12.5)
    data = fp.model_dump(mode="json")
    assert data["date"] == "2024-01-01"
    assert data["predicted_value"] == 12.5


def test_city_forecast_response_has_required_fields():
    resp = CityForecastResponse(
        forecasts=[ForecastPoint(date=date(2024, 1, 1), predicted_value=10.0)],
        model_name="lgbm_v1",
        target="crash_count",
        generated_at=datetime(2024, 1, 1, 12, 0),
    )
    assert resp.model_name == "lgbm_v1"
    assert len(resp.forecasts) == 1


def test_hotspot_summary_includes_h3_cell():
    hs = HotspotSummary(
        h3_cell="882a100d65fffff",
        crash_count=42,
        injury_crash_count=5,
    )
    assert hs.h3_cell.startswith("8")
