import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

import type { ForecastPoint } from "../types/api";

interface ForecastChartProps {
  forecasts: ForecastPoint[];
  title: string;
}

export default function ForecastChart({ forecasts, title }: ForecastChartProps) {
  const data = forecasts.map((f) => ({
    date: f.date,
    predicted: Math.round(f.predicted_value * 10) / 10,
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
          <Line type="monotone" dataKey="predicted" stroke="#e63946" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
