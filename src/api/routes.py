"""API route handlers."""

from datetime import datetime

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


@router.get("/forecast/city", response_model=CityForecastResponse)
def forecast_city(
    horizon: int = Query(default=7, ge=1, le=90),
    target: str = Query(default="crash_count"),
    model: CrashForecaster = Depends(get_model),
    panel: pd.DataFrame = Depends(get_panel),
):
    preds = model.predict(panel, horizon=horizon)
    # Aggregate across cells per day
    daily = preds.groupby("date")["predicted"].sum().reset_index()

    forecasts = [
        ForecastPoint(date=pd.Timestamp(row["date"]).date(), predicted_value=round(row["predicted"], 2))
        for _, row in daily.iterrows()
    ]
    return CityForecastResponse(
        forecasts=forecasts,
        model_name="lgbm_city_v1",
        target=target,
        generated_at=datetime.utcnow(),
    )


@router.get("/hotspot/{h3_cell}", response_model=HotspotDetailResponse)
def hotspot_detail(
    h3_cell: str,
    horizon: int = Query(default=7, ge=1, le=90),
    model: CrashForecaster = Depends(get_model),
    panel: pd.DataFrame = Depends(get_panel),
):
    cell_data = panel[panel["h3_cell"] == h3_cell]
    if cell_data.empty:
        raise HTTPException(status_code=404, detail=f"H3 cell {h3_cell} not found")

    preds = model.predict(cell_data, horizon=horizon)
    forecasts = [
        ForecastPoint(
            date=pd.Timestamp(row["date"]).date(),
            predicted_value=round(row["predicted"], 2),
            h3_cell=h3_cell,
        )
        for _, row in preds.iterrows()
    ]

    return HotspotDetailResponse(
        h3_cell=h3_cell,
        crash_count=int(cell_data["crash_count"].sum()),
        injury_crash_count=int(cell_data["injury_crash_count"].sum()),
        forecast=forecasts,
        generated_at=datetime.utcnow(),
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
