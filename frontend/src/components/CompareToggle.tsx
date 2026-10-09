import { MAX_COMPARE, useCompareSelection } from "../lib/compareSelection";

export function CompareToggle({ regionId, compact = false }: { regionId: string; compact?: boolean }) {
  const selection = useCompareSelection();
  const selected = selection.has(regionId);
  const full = !selected && selection.ids.length >= MAX_COMPARE;
  const label = compact ? (selected ? "added" : "compare") : selected ? "In comparison" : "Add to comparison";
  return (
    <button
      type="button"
      className={`toggle ${compact ? "toggle-sm" : ""}`}
      aria-pressed={selected}
      aria-label={compact ? `${selected ? "Remove" : "Add"} ${regionId} ${selected ? "from" : "to"} comparison` : undefined}
      disabled={full}
      title={full ? `Compare holds up to ${MAX_COMPARE} regions` : undefined}
      onClick={() => selection.toggle(regionId)}
    >
      {label}
    </button>
  );
}
