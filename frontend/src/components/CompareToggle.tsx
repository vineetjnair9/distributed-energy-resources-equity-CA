import { MAX_COMPARE, useCompareSelection } from "../lib/compareSelection";

export function CompareToggle({ regionId, compact = false }: { regionId: string; compact?: boolean }) {
  const selection = useCompareSelection();
  const selected = selection.has(regionId);
  const full = !selected && selection.ids.length >= MAX_COMPARE;
  return (
    <button
      type="button"
      className={`btn ${selected ? "btn-selected" : "btn-ghost"} ${compact ? "btn-sm" : ""}`}
      aria-pressed={selected}
      disabled={full}
      title={full ? `Compare holds up to ${MAX_COMPARE} regions` : undefined}
      onClick={() => selection.toggle(regionId)}
    >
      {selected ? "✓ In compare" : "+ Compare"}
    </button>
  );
}
