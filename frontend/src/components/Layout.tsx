import { Link, NavLink, Outlet } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { useCompareSelection } from "../lib/compareSelection";

export function Layout() {
  const health = useApi(api.health, "health");
  const selection = useCompareSelection();
  return (
    <div className="app">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <span className="brand-mark" aria-hidden>◉</span>
            <span>
              <span className="brand-name">CA DER Explorer</span>
              <span className="brand-sub">Distributed energy decision support</span>
            </span>
          </Link>
          <nav aria-label="Primary">
            <NavLink to="/" end>Explore</NavLink>
            <NavLink to={selection.ids.length ? `/compare?ids=${selection.ids.join(",")}` : "/compare"}>
              Compare{selection.ids.length ? <span className="count">{selection.ids.length}</span> : null}
            </NavLink>
            <NavLink to="/about">Method</NavLink>
            <a href="/api/docs">API</a>
          </nav>
        </div>
      </header>
      {health.data?.synthetic && (
        <div className="banner banner-synthetic" role="note">
          <strong>Synthetic demo data.</strong> Values, model outputs, and summaries are generated for development and are not research findings.
        </div>
      )}
      {health.error && (
        <div className="banner banner-error" role="alert">
          The data service is not ready: {health.error.message}
        </div>
      )}
      <main id="main" className="main">
        <Outlet />
      </main>
      <footer className="footer">
        California ZCTA-level DER adoption, ACS demographics, and regression screening. Model outputs are computed offline; summaries are generated offline from cited evidence.
      </footer>
    </div>
  );
}
