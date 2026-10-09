import type { ReactNode } from "react";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="status" role="status" aria-live="polite">
      <span className="spinner" aria-hidden /> {label}…
    </div>
  );
}

export function ErrorNotice({ error, children }: { error: Error; children?: ReactNode }) {
  return (
    <div className="notice notice-error" role="alert">
      <strong>Something went wrong.</strong> {error.message}
      {children}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
