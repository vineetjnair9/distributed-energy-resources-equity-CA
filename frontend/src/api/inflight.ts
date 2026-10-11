/** Count of API requests in flight, shared by the whole app for the progress bar. */
type Listener = () => void;

let count = 0;
const listeners = new Set<Listener>();

function emit() {
  for (const listener of listeners) listener();
}

export const inflight = {
  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  current: () => count,
  async track<T>(work: Promise<T>): Promise<T> {
    count += 1;
    emit();
    try {
      return await work;
    } finally {
      count -= 1;
      emit();
    }
  },
};
