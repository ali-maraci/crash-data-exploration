"""API route handlers."""

from datetime import date, datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_model, get_panel
from src.api.schemas import (
    CityForecastResponse,
    ForecastPoint,
    HotspotDetailResponse,
    HotspotSummary,
    TopHotspotsResponse,
)
from src.models.lgbm import CrashForecaster

router = APIRouter()


def _get_actuals(panel: pd.DataFrame, target: str, start_date, end_date) -> dict[str, float]:
    """Get actual daily totals for a date range, keyed by ISO date string."""
    mask = (panel["date"] >= pd.Timestamp(start_date)) & (panel["date"] <= pd.Timestamp(end_date))
    subset = panel[mask]
    if subset.empty:
        return {}
    daily = subset.groupby("date")[target].sum()
    return {d.date().isoformat(): float(v) for d, v in daily.items()}


def _get_cell_actuals(panel: pd.DataFrame, h3_cell: str, target: str, start_date, end_date) -> dict[str, float]:
    """Get actual daily values for a specific cell in a date range."""
    mask = (
        (panel["h3_cell"] == h3_cell)
        & (panel["date"] >= pd.Timestamp(start_date))
        & (panel["date"] <= pd.Timestamp(end_date))
    )
    subset = panel[mask]
    if subset.empty:
        return {}
    return {row["date"].date().isoformat(): float(row[target]) for _, row in subset.iterrows()}


@router.get("/forecast/city", response_model=CityForecastResponse)
def forecast_city(
    horizon: int = Query(default=7, ge=1, le=90),
    target: str = Query(default="crash_count"),
    as_of_date: date | None = Query(default=None),
    model: CrashForecaster = Depends(get_model),
    panel: pd.DataFrame = Depends(get_panel),
):
    # Determine as_of_date: use provided value or panel's max date
    if as_of_date is None:
        as_of_date = panel["date"].max().date()

    # Slice panel to only data <= as_of_date for prediction
    panel_slice = panel[panel["date"] <= pd.Timestamp(as_of_date)]

    preds = model.predict(panel_slice, horizon=horizon)
    # Aggregate across cells per day
    daily = preds.groupby("date")["predicted"].sum().reset_index()

    # Get forecast date range for actuals lookup
    if not daily.empty:
        forecast_start = daily["date"].min()
        forecast_end = daily["date"].max()
        actuals = _get_actuals(panel, target, forecast_start, forecast_end)
    else:
        actuals = {}

    forecasts = [
        ForecastPoint(
            date=pd.Timestamp(row["date"]).date(),
            predicted_value=round(row["predicted"], 2),
            actual_value=actuals.get(pd.Timestamp(row["date"]).date().isoformat()),
        )
        for _, row in daily.iterrows()
    ]
    return CityForecastResponse(
        forecasts=forecasts,
        model_name="lgbm_city_v1",
        target=target,
        generated_at=datetime.utcnow(),
        as_of_date=as_of_date,
    )


@router.get("/hotspot/{h3_cell}", response_model=HotspotDetailResponse)
def hotspot_detail(
    h3_cell: str,
    horizon: int = Query(default=7, ge=1, le=90),
    as_of_date: date | None = Query(default=None),
    model: CrashForecaster = Depends(get_model),
    panel: pd.DataFrame = Depends(get_panel),
):
    # Determine as_of_date: use provided value or panel's max date
    if as_of_date is None:
        as_of_date = panel["date"].max().date()

    # Slice panel to only data <= as_of_date for prediction
    panel_slice = panel[panel["date"] <= pd.Timestamp(as_of_date)]

    cell_data = panel_slice[panel_slice["h3_cell"] == h3_cell]
    if cell_data.empty:
        # Also check full panel to give a meaningful 404
        if panel[panel["h3_cell"] == h3_cell].empty:
            raise HTTPException(status_code=404, detail=f"H3 cell {h3_cell} not found")
        raise HTTPException(status_code=404, detail=f"H3 cell {h3_cell} not found in data up to {as_of_date}")

    preds = model.predict(cell_data, horizon=horizon)

    # Get forecast date range for actuals lookup
    if not preds.empty:
        forecast_start = preds["date"].min()
        forecast_end = preds["date"].max()
        actuals = _get_cell_actuals(panel, h3_cell, "crash_count", forecast_start, forecast_end)
    else:
        actuals = {}

    forecasts = [
        ForecastPoint(
            date=pd.Timestamp(row["date"]).date(),
            predicted_value=round(row["predicted"], 2),
            h3_cell=h3_cell,
            actual_value=actuals.get(pd.Timestamp(row["date"]).date().isoformat()),
        )
        for _, row in preds.iterrows()
    ]

    return HotspotDetailResponse(
        h3_cell=h3_cell,
        crash_count=int(cell_data["crash_count"].sum()),
        injury_crash_count=int(cell_data["injury_crash_count"].sum()),
        forecast=forecasts,
        generated_at=datetime.utcnow(),
        as_of_date=as_of_date,
    )


@router.get("/hotspots/top", response_model=TopHotspotsResponse)
def top_hotspots(
    n: int = Query(default=20, ge=1, le=100),
    panel: pd.DataFrame = Depends(get_panel),
):
    totals = (
        panel.groupby("h3_cell")
        .agg(crash_count=("crash_count", "sum"), injury_crash_count=("injury_crash_count", "sum"))
        .reset_index()
        .sort_values("crash_count", ascending=False)
        .head(n)
    )

    hotspots = [
        HotspotSummary(
            h3_cell=row["h3_cell"],
            crash_count=int(row["crash_count"]),
            injury_crash_count=int(row["injury_crash_count"]),
        )
        for _, row in totals.iterrows()
    ]
    return TopHotspotsResponse(hotspots=hotspots, generated_at=datetime.utcnow())
