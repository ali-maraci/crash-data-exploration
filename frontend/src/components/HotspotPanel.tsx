import { useQuery } from "@tanstack/react-query";

import { fetchHotspot } from "../api/client";
import type { HotspotDetailResponse } from "../types/api";
import ForecastChart from "./ForecastChart";

interface HotspotPanelProps {
  h3Cell: string | null;
  horizon: number;
}

export default function HotspotPanel({ h3Cell, horizon }: HotspotPanelProps) {
  const { data, isLoading } = useQuery<HotspotDetailResponse>({
    queryKey: ["hotspot", h3Cell, horizon],
    queryFn: () => fetchHotspot(h3Cell!, horizon),
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
