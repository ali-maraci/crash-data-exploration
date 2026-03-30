const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchCityForecast(
  horizon = 7,
  target = "crash_count"
): Promise<import("../types/api").CityForecastResponse> {
  return fetchJSON(`/forecast/city?horizon=${horizon}&target=${target}`);
}

export async function fetchHotspot(
  h3Cell: string,
  horizon = 7
): Promise<import("../types/api").HotspotDetailResponse> {
  return fetchJSON(`/hotspot/${h3Cell}?horizon=${horizon}`);
}

export async function fetchTopHotspots(
  n = 20
): Promise<import("../types/api").TopHotspotsResponse> {
  return fetchJSON(`/hotspots/top?n=${n}`);
}
