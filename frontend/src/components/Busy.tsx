import { useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { inflight } from "../api/inflight";

/** Becomes true only after `ms` of continuous loading, so fast loads don't flicker. */
export function useDelayed(active: boolean, ms = 150) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    if (!active) {
      setShown(false);
      return;
    }
    const timer = setTimeout(() => setShown(true), ms);
    return () => clearTimeout(timer);
  }, [active, ms]);
  return shown;
}

/** Thin bar under the masthead whenever any API request is in flight. */
export function ProgressBar() {
  const pending = useSyncExternalStore(inflight.subscribe, inflight.current, inflight.current);
  const shown = useDelayed(pending > 0);
  return (
    <>
      <div className={`progress ${shown ? "progress-on" : ""}`} aria-hidden />
      <span className="sr-only" role="status" aria-live="polite">{shown ? "Loading…" : ""}</span>
    </>
  );
}

/**
 * Wraps content that is being replaced: it stays visible but dims while new
 * data loads, so a changed filter or selection visibly takes effect.
 */
export function Busy({ when, children, className = "" }: { when: boolean; children: ReactNode; className?: string }) {
  const shown = useDelayed(when);
  return (
    <div className={`busy-region ${shown ? "is-busy" : ""} ${className}`} aria-busy={when}>
      {children}
    </div>
  );
}
