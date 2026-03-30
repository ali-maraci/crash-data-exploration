interface FiltersProps {
  horizon: number;
  asOfDate: string;
  onHorizonChange: (h: number) => void;
  onAsOfDateChange: (d: string) => void;
}

export default function Filters({
  horizon,
  asOfDate,
  onHorizonChange,
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
    </div>
  );
}
