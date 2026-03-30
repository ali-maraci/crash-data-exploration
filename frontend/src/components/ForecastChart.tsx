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
