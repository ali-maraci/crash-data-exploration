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
