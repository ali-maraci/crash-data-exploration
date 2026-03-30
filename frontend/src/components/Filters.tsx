interface FiltersProps {
  horizon: number;
  target: string;
  onHorizonChange: (h: number) => void;
  onTargetChange: (t: string) => void;
}

export default function Filters({
  horizon,
  target,
  onHorizonChange,
  onTargetChange,
}: FiltersProps) {
  return (
    <div style={{ display: "flex", gap: "1rem", padding: "0.75rem 1rem", background: "#f5f5f5", borderBottom: "1px solid #ddd" }}>
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
