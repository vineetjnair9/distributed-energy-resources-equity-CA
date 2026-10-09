import { useEffect, useState } from "react";
import { api, type Region } from "../api/client";
import { useApi } from "../api/useApi";

function useDebounced<T>(value: T, ms = 200) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return debounced;
}

/** Type-ahead picker used on the compare page. */
export function RegionPicker({ onPick, exclude }: { onPick: (region: Region) => void; exclude: string[] }) {
  const [text, setText] = useState("");
  const q = useDebounced(text.trim());
  const results = useApi(q ? () => api.regions({ q, limit: 8 }) : null, `pick-${q}`);
  const items = (results.data?.items ?? []).filter((region) => !exclude.includes(region.region_id));
  return (
    <div className="picker">
      <label htmlFor="picker-input" className="sr-only">Add a region by ZIP code or county</label>
      <input
        id="picker-input"
        className="input"
        placeholder="Add a ZIP code or county…"
        value={text}
        autoComplete="off"
        onChange={(event) => setText(event.target.value)}
      />
      {q && items.length > 0 && (
        <ul className="picker-results" role="listbox">
          {items.map((region) => (
            <li key={region.region_id}>
              <button
                type="button"
                role="option"
                aria-selected={false}
                onClick={() => {
                  onPick(region);
                  setText("");
                }}
              >
                <strong>{region.region_id}</strong> {region.county} County
                {region.utility ? ` · ${region.utility.utility_acronym ?? region.utility.utility_name}` : ""}
              </button>
            </li>
          ))}
        </ul>
      )}
      {q && results.data && items.length === 0 && <p className="picker-none">No matching regions.</p>}
    </div>
  );
}

export { useDebounced };
