export interface ForecastPoint {
  date: string;
  predicted_value: number;
  h3_cell?: string;
}

export interface CityForecastResponse {
  forecasts: ForecastPoint[];
  model_name: string;
  target: string;
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
  generated_at: string;
}

export interface TopHotspotsResponse {
  hotspots: HotspotSummary[];
  generated_at: string;
}
