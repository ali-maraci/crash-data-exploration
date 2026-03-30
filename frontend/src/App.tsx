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
