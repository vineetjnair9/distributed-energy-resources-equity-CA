import { useEffect, useState } from "react";

export interface Loadable<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

/** Run an API call when its key changes; ignore responses from stale keys. */
export function useApi<T>(load: (() => Promise<T>) | null, key: string): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ data: null, error: null, loading: !!load });
  useEffect(() => {
    if (!load) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    let active = true;
    setState((previous) => ({ data: previous.data, error: null, loading: true }));
    load().then(
      (data) => active && setState({ data, error: null, loading: false }),
      (error: Error) => active && setState({ data: null, error, loading: false }),
    );
    return () => {
      active = false;
    };
    // `key` captures every input to `load`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state;
}
