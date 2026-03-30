interface FiltersProps {
  horizon: number;
  target: string;
  asOfDate: string;
  onHorizonChange: (h: number) => void;
  onTargetChange: (t: string) => void;
  onAsOfDateChange: (d: string) => void;
}

export default function Filters({
  horizon,
  target,
  asOfDate,
  onHorizonChange,
  onTargetChange,
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
      <label>
        Target:{" "}
        <select value={target} onChange={(e) => onTargetChange(e.target.value)}>
          <option value="crash_count">All crashes</option>
          <option value="injury_crash_count">Injury crashes</option>
        </select>
      </label>
    </div>
  );
}
