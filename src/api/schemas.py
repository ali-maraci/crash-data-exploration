"""Pydantic models for API request/response."""

from datetime import date, datetime

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: date
    predicted_value: float
    h3_cell: str | None = None


class CityForecastResponse(BaseModel):
    forecasts: list[ForecastPoint]
    model_name: str
    target: str
    generated_at: datetime


class HotspotSummary(BaseModel):
    h3_cell: str
    crash_count: int
    injury_crash_count: int
    forecast: list[ForecastPoint] | None = None


class HotspotDetailResponse(BaseModel):
    h3_cell: str
    crash_count: int
    injury_crash_count: int
    forecast: list[ForecastPoint]
    generated_at: datetime


class TopHotspotsResponse(BaseModel):
    hotspots: list[HotspotSummary]
    generated_at: datetime
