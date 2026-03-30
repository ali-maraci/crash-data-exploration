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
