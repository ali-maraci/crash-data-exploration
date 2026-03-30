# As-Of Date Hindcast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `as_of_date` parameter so users can simulate forecasts from any historical date and compare predictions against actuals.

**Architecture:** The API gains an `as_of_date` query param on `/forecast/city` and `/hotspot/{h3_cell}`. When set, the panel is sliced to data before that date, the model predicts the next N days, and the response includes both predicted and actual values. The frontend adds a date picker and overlays predicted vs actual lines on the chart.

**Tech Stack:** Python (FastAPI, pandas), React (TypeScript, Recharts)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/api/schemas.py` | Modify | Add `actual_value` to `ForecastPoint`, add `as_of_date` to responses |
| `src/api/routes.py` | Modify | Add `as_of_date` param, slice panel, attach actuals |
| `tests/test_api.py` | Modify | Add tests for as_of_date behavior |
| `frontend/src/types/api.ts` | Modify | Add `actual_value` field |
| `frontend/src/api/client.ts` | Modify | Pass `as_of_date` param |
| `frontend/src/components/Filters.tsx` | Modify | Add date picker |
| `frontend/src/components/ForecastChart.tsx` | Modify | Overlay predicted vs actual lines |
| `frontend/src/components/HotspotPanel.tsx` | Modify | Pass `asOfDate` through |
| `frontend/src/App.tsx` | Modify | Wire `asOfDate` state |

---

### Task 1: Add `actual_value` to schema and `as_of_date` to API (TDD)

**Files:**
- Modify: `src/api/schemas.py`
- Modify: `src/api/routes.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_api.py`:

```python
def test_forecast_city_with_as_of_date(client):
    resp = client.get("/forecast/city?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "forecasts" in data
    assert "as_of_date" in data
    assert data["as_of_date"] == "2023-01-15"


def test_forecast_city_with_as_of_date_includes_actuals(client, mock_panel):
    # mock_panel has dates 2023-01-01 to 2023-01-30, so as_of_date=2023-01-15
    # should have actuals available for the forecast period
    resp = client.get("/forecast/city?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    # Check that forecast points have actual_value field
    for point in data["forecasts"]:
        assert "actual_value" in point


def test_forecast_city_without_as_of_date_uses_panel_end(client):
    resp = client.get("/forecast/city?horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    # as_of_date should default to panel end date
    assert "as_of_date" in data


def test_hotspot_with_as_of_date(client):
    resp = client.get("/hotspot/cell_a?as_of_date=2023-01-15&horizon=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "as_of_date" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `venv/bin/pytest tests/test_api.py -v -k "as_of_date"`
Expected: FAIL — `as_of_date` not in response

- [ ] **Step 3: Update schemas.py**

Replace the full file `src/api/schemas.py`:

```python
"""Pydantic models for API request/response."""

from datetime import date, datetime

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: date
    predicted_value: float
    actual_value: float | None = None
    h3_cell: str | None = None


class CityForecastResponse(BaseModel):
    forecasts: list[ForecastPoint]
    model_name: str
    target: str
    as_of_date: date
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
    as_of_date: date
    generated_at: datetime


class TopHotspotsResponse(BaseModel):
    hotspots: list[HotspotSummary]
    generated_at: datetime
```

- [ ] **Step 4: Update routes.py**

Replace the full file `src/api/routes.py`:

```python
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
    # Slice panel to as_of_date
    if as_of_date is not None:
        panel_slice = panel[panel["date"] <= pd.Timestamp(as_of_date)]
    else:
        panel_slice = panel
        as_of_date = panel["date"].max().date()

    if panel_slice.empty:
        raise HTTPException(status_code=400, detail="No data available before as_of_date")

    preds = model.predict(panel_slice, horizon=horizon)
    daily = preds.groupby("date")["predicted"].sum().reset_index()

    # Get actuals for the forecast period
    forecast_start = daily["date"].min()
    forecast_end = daily["date"].max()
    actuals = _get_actuals(panel, target, forecast_start, forecast_end)

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
        as_of_date=as_of_date,
        generated_at=datetime.utcnow(),
    )


@router.get("/hotspot/{h3_cell}", response_model=HotspotDetailResponse)
def hotspot_detail(
    h3_cell: str,
    horizon: int = Query(default=7, ge=1, le=90),
    as_of_date: date | None = Query(default=None),
    model: CrashForecaster = Depends(get_model),
    panel: pd.DataFrame = Depends(get_panel),
):
    cell_data = panel[panel["h3_cell"] == h3_cell]
    if cell_data.empty:
        raise HTTPException(status_code=404, detail=f"H3 cell {h3_cell} not found")

    # Slice to as_of_date
    if as_of_date is not None:
        cell_slice = cell_data[cell_data["date"] <= pd.Timestamp(as_of_date)]
    else:
        cell_slice = cell_data
        as_of_date = cell_data["date"].max().date()

    if cell_slice.empty:
        raise HTTPException(status_code=400, detail="No data available before as_of_date")

    preds = model.predict(cell_slice, horizon=horizon)

    # Get actuals for forecast period
    forecast_start = preds["date"].min()
    forecast_end = preds["date"].max()
    actuals = _get_cell_actuals(panel, h3_cell, "crash_count", forecast_start, forecast_end)

    forecasts = [
        ForecastPoint(
            date=pd.Timestamp(row["date"]).date(),
            predicted_value=round(row["predicted"], 2),
            actual_value=actuals.get(pd.Timestamp(row["date"]).date().isoformat()),
            h3_cell=h3_cell,
        )
        for _, row in preds.iterrows()
    ]

    return HotspotDetailResponse(
        h3_cell=h3_cell,
        crash_count=int(cell_slice["crash_count"].sum()),
        injury_crash_count=int(cell_slice["injury_crash_count"].sum()),
        forecast=forecasts,
        as_of_date=as_of_date,
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `venv/bin/pytest tests/test_api.py -v`
Expected: All 9 tests PASS (5 existing + 4 new)

- [ ] **Step 6: Commit**

```bash
git add src/api/schemas.py src/api/routes.py tests/test_api.py
git commit -m "feat: add as_of_date param with actuals overlay to forecast endpoints"
```

---

### Task 2: Update frontend types and API client

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Update types**

Replace the full file `frontend/src/types/api.ts`:

```typescript
export interface ForecastPoint {
  date: string;
  predicted_value: number;
  actual_value?: number | null;
  h3_cell?: string;
}

export interface CityForecastResponse {
  forecasts: ForecastPoint[];
  model_name: string;
  target: string;
  as_of_date: string;
  generated_at: string;
}

export interface HotspotSummary {
  h3_cell: string;
  crash_count: number;
  injury_crash_count: number;
  forecast?: ForecastPoint[];
}

export interface HotspotDetailResponse {
  h3_cell: string;
  crash_count: number;
  injury_crash_count: number;
  forecast: ForecastPoint[];
  as_of_date: string;
  generated_at: string;
}

export interface TopHotspotsResponse {
  hotspots: HotspotSummary[];
  generated_at: string;
}
```

- [ ] **Step 2: Update API client**

Replace the full file `frontend/src/api/client.ts`:

```typescript
import type { CityForecastResponse, HotspotDetailResponse, TopHotspotsResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchCityForecast(
  horizon = 7,
  target = "crash_count",
  asOfDate?: string
): Promise<CityForecastResponse> {
  let url = `/forecast/city?horizon=${horizon}&target=${target}`;
  if (asOfDate) url += `&as_of_date=${asOfDate}`;
  return fetchJSON(url);
}

export async function fetchHotspot(
  h3Cell: string,
  horizon = 7,
  asOfDate?: string
): Promise<HotspotDetailResponse> {
  let url = `/hotspot/${h3Cell}?horizon=${horizon}`;
  if (asOfDate) url += `&as_of_date=${asOfDate}`;
  return fetchJSON(url);
}

export async function fetchTopHotspots(
  n = 20
): Promise<TopHotspotsResponse> {
  return fetchJSON(`/hotspots/top?n=${n}`);
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/api/client.ts
git commit -m "feat: add as_of_date and actual_value to frontend API types and client"
```

---

### Task 3: Add date picker to Filters and wire through App

**Files:**
- Modify: `frontend/src/components/Filters.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update Filters component**

Replace the full file `frontend/src/components/Filters.tsx`:

```tsx
interface FiltersProps {
  horizon: number;
  target: string;
  asOfDate: string;
  onHorizonChange: (h: number) => void;
  onTargetChange: (t: string) => void;
  onAsOfDateChange: (d: string) => void;
}

export default function Filters({
  horizon,
  target,
  asOfDate,
  onHorizonChange,
  onTargetChange,
  onAsOfDateChange,
}: FiltersProps) {
  return (
    <div style={{ display: "flex", gap: "1rem", padding: "0.75rem 1rem", background: "#f5f5f5", borderBottom: "1px solid #ddd", alignItems: "center" }}>
      <label>
        As-of date:{" "}
        <input
          type="date"
          value={asOfDate}
          min="2016-01-01"
          max="2023-12-31"
          onChange={(e) => onAsOfDateChange(e.target.value)}
        />
      </label>
      <label>
        Horizon:{" "}
        <select value={horizon} onChange={(e) => onHorizonChange(Number(e.target.value))}>
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={28}>28 days</option>
        </select>
      </label>
      <label>
        Target:{" "}
        <select value={target} onChange={(e) => onTargetChange(e.target.value)}>
          <option value="crash_count">All crashes</option>
          <option value="injury_crash_count">Injury crashes</option>
        </select>
      </label>
    </div>
  );
}
```

- [ ] **Step 2: Update App.tsx**

Replace the full file `frontend/src/App.tsx`:

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchCityForecast, fetchTopHotspots } from "./api/client";
import CrashMap from "./components/Map";
import Filters from "./components/Filters";
import ForecastChart from "./components/ForecastChart";
import HotspotPanel from "./components/HotspotPanel";

export default function App() {
  const [horizon, setHorizon] = useState(7);
  const [target, setTarget] = useState("crash_count");
  const [asOfDate, setAsOfDate] = useState("2023-06-15");
  const [selectedCell, setSelectedCell] = useState<string | null>(null);

  const { data: hotspots } = useQuery({
    queryKey: ["hotspots", 100],
    queryFn: () => fetchTopHotspots(100),
  });

  const { data: cityForecast } = useQuery({
    queryKey: ["cityForecast", horizon, target, asOfDate],
    queryFn: () => fetchCityForecast(horizon, target, asOfDate),
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <Filters
        horizon={horizon}
        target={target}
        asOfDate={asOfDate}
        onHorizonChange={setHorizon}
        onTargetChange={setTarget}
        onAsOfDateChange={setAsOfDate}
      />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 7, position: "relative" }}>
          <CrashMap
            hotspots={hotspots?.hotspots ?? []}
            selectedCell={selectedCell}
            onCellClick={setSelectedCell}
          />
        </div>
        <div style={{ flex: 3, borderLeft: "1px solid #ddd", overflowY: "auto", background: "#fafafa" }}>
          {cityForecast && (
            <ForecastChart forecasts={cityForecast.forecasts} title="City-wide Forecast" />
          )}
          <hr style={{ margin: "0", border: "none", borderTop: "1px solid #ddd" }} />
          <HotspotPanel h3Cell={selectedCell} horizon={horizon} asOfDate={asOfDate} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update HotspotPanel to pass asOfDate**

Replace the full file `frontend/src/components/HotspotPanel.tsx`:

```tsx
import { useQuery } from "@tanstack/react-query";

import { fetchHotspot } from "../api/client";
import type { HotspotDetailResponse } from "../types/api";
import ForecastChart from "./ForecastChart";

interface HotspotPanelProps {
  h3Cell: string | null;
  horizon: number;
  asOfDate: string;
}

export default function HotspotPanel({ h3Cell, horizon, asOfDate }: HotspotPanelProps) {
  const { data, isLoading } = useQuery<HotspotDetailResponse>({
    queryKey: ["hotspot", h3Cell, horizon, asOfDate],
    queryFn: () => fetchHotspot(h3Cell!, horizon, asOfDate),
    enabled: !!h3Cell,
  });

  if (!h3Cell) {
    return (
      <div style={{ padding: "2rem", color: "#666", textAlign: "center" }}>
        Click a hexagon on the map to view details
      </div>
    );
  }

  if (isLoading) return <div style={{ padding: "1rem" }}>Loading...</div>;
  if (!data) return null;

  return (
    <div style={{ padding: "1rem", overflowY: "auto" }}>
      <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.1rem" }}>Cell Details</h2>
      <p style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "#666" }}>{data.h3_cell}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", margin: "1rem 0" }}>
        <div style={{ background: "#fff3f3", padding: "0.75rem", borderRadius: "6px" }}>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#e63946" }}>{data.crash_count.toLocaleString()}</div>
          <div style={{ fontSize: "0.8rem", color: "#666" }}>Total crashes</div>
        </div>
        <div style={{ background: "#fff8f0", padding: "0.75rem", borderRadius: "6px" }}>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#e76f51" }}>{data.injury_crash_count.toLocaleString()}</div>
          <div style={{ fontSize: "0.8rem", color: "#666" }}>Injury crashes</div>
        </div>
      </div>
      <ForecastChart forecasts={data.forecast} title="Forecast" />
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Filters.tsx frontend/src/components/HotspotPanel.tsx frontend/src/App.tsx
git commit -m "feat: add date picker and wire as_of_date through frontend"
```

---

### Task 4: Overlay predicted vs actual lines on ForecastChart

**Files:**
- Modify: `frontend/src/components/ForecastChart.tsx`

- [ ] **Step 1: Update ForecastChart to show both lines**

Replace the full file `frontend/src/components/ForecastChart.tsx`:

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

import type { ForecastPoint } from "../types/api";

interface ForecastChartProps {
  forecasts: ForecastPoint[];
  title: string;
}

export default function ForecastChart({ forecasts, title }: ForecastChartProps) {
  const hasActuals = forecasts.some((f) => f.actual_value != null);

  const data = forecasts.map((f) => ({
    date: f.date,
    predicted: Math.round(f.predicted_value * 10) / 10,
    actual: f.actual_value != null ? Math.round(f.actual_value * 10) / 10 : undefined,
  }));

  return (
    <div style={{ padding: "1rem" }}>
      <h3 style={{ margin: "0 0 0.5rem" }}>{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          {hasActuals && <Legend />}
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#e63946"
            strokeWidth={2}
            dot={false}
            name="Predicted"
          />
          {hasActuals && (
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#2a9d8f"
              strokeWidth={2}
              dot={false}
              name="Actual"
              strokeDasharray="5 3"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ForecastChart.tsx
git commit -m "feat: overlay predicted vs actual lines on forecast chart"
```

---

## Verification

1. **Backend tests:**
   ```bash
   make test
   # All tests pass including new as_of_date tests
   ```

2. **API manual test:**
   ```bash
   make serve &
   # Without as_of_date (uses panel end)
   curl http://localhost:8000/forecast/city?horizon=7
   # With as_of_date (hindcast from mid-2022)
   curl "http://localhost:8000/forecast/city?horizon=7&as_of_date=2022-06-15"
   # Check that response includes as_of_date field and actual_value in forecast points
   ```

3. **Frontend:**
   ```bash
   cd frontend && npm run dev
   # Open http://localhost:5173
   # Pick a date like 2022-06-15, see predicted (red) vs actual (green dashed) lines
   ```
