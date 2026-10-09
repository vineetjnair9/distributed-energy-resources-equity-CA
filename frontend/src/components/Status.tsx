import type { ReactNode } from "react";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="status" role="status" aria-live="polite">
      {label}…
    </div>
  );
}

export function ErrorNotice({ error, children }: { error: Error; children?: ReactNode }) {
  return (
    <div className="notice" role="alert">
      {error.message}
      {children}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
