import { DeckGL } from "@deck.gl/react";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { Map as MapLibre } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

import type { HotspotSummary } from "../types/api";

interface MapProps {
  hotspots: HotspotSummary[];
  selectedCell: string | null;
  onCellClick: (cell: string) => void;
}

const INITIAL_VIEW = {
  latitude: 41.88,
  longitude: -87.63,
  zoom: 10,
  pitch: 0,
  bearing: 0,
};

// Color scale: green -> yellow -> red
function getColor(count: number, maxCount: number): [number, number, number, number] {
  const t = maxCount > 0 ? Math.min(count / maxCount, 1) : 0;
  const r = Math.round(255 * Math.min(2 * t, 1));
  const g = Math.round(255 * Math.min(2 * (1 - t), 1));
  return [r, g, 0, 180];
}

export default function CrashMap({ hotspots, selectedCell, onCellClick }: MapProps) {
  const maxCount = Math.max(...hotspots.map((h) => h.crash_count), 1);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layer = new H3HexagonLayer<HotspotSummary>({
    id: "h3-hexagons",
    data: hotspots,
    pickable: true,
    filled: true,
    extruded: false,
    getHexagon: (d: HotspotSummary) => d.h3_cell,
    getFillColor: (d: HotspotSummary) =>
      d.h3_cell === selectedCell
        ? [0, 120, 255, 220]
        : getColor(d.crash_count, maxCount),
    getLineColor: [255, 255, 255, 80],
    lineWidthMinPixels: 1,
    onClick: ({ object }: { object?: HotspotSummary }) => {
      if (object) onCellClick(object.h3_cell);
    },
  });

  return (
    <DeckGL initialViewState={INITIAL_VIEW} controller layers={[layer]}>
      <MapLibre
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        style={{ width: "100%", height: "100%" }}
      />
    </DeckGL>
  );
}
