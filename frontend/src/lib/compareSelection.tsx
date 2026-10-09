import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export const MAX_COMPARE = 6;
const STORAGE_KEY = "der-compare-selection";

interface Selection {
  ids: string[];
  has: (id: string) => boolean;
  toggle: (id: string) => void;
  set: (ids: string[]) => void;
  clear: () => void;
}

const SelectionContext = createContext<Selection | null>(null);

function readStored(): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(value) ? value.filter((id) => typeof id === "string").slice(0, MAX_COMPARE) : [];
  } catch {
    return [];
  }
}

export function CompareSelectionProvider({ children }: { children: ReactNode }) {
  const [ids, setIds] = useState<string[]>(readStored);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    } catch {
      // Private windows can refuse storage; the selection still works in memory.
    }
  }, [ids]);
  const toggle = useCallback(
    (id: string) =>
      setIds((current) =>
        current.includes(id) ? current.filter((x) => x !== id) : current.length >= MAX_COMPARE ? current : [...current, id],
      ),
    [],
  );
  const value = useMemo<Selection>(
    () => ({
      ids,
      has: (id) => ids.includes(id),
      toggle,
      set: (next) => setIds([...new Set(next)].slice(0, MAX_COMPARE)),
      clear: () => setIds([]),
    }),
    [ids, toggle],
  );
  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

export function useCompareSelection() {
  const value = useContext(SelectionContext);
  if (!value) throw new Error("useCompareSelection outside CompareSelectionProvider");
  return value;
}
