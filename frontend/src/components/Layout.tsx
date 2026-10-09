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
      <header className="masthead">
        <div className="masthead-inner">
          <div>
            <Link to="/" className="wordmark">California DER Atlas</Link>
            {health.data?.synthetic && (
              <span
                className="demo-tag"
                role="note"
                title="Values, model outputs, and summaries are synthetic demo data, not research findings."
              >
                SYNTHETIC DATA
              </span>
            )}
          </div>
          <nav aria-label="Primary">
            <NavLink to="/" end>Regions</NavLink>
            <NavLink to={selection.ids.length ? `/compare?ids=${selection.ids.join(",")}` : "/compare"}>
              Compare{selection.ids.length ? <span className="count">({selection.ids.length})</span> : null}
            </NavLink>
            <NavLink to="/about">Method</NavLink>
            <a href="/api/docs">API</a>
          </nav>
        </div>
      </header>
      {health.error && (
        <div className="service-down" role="alert">
          The data service is not ready: {health.error.message}
        </div>
      )}
      <main id="main" className="page">
        <Outlet />
      </main>
      <footer className="colophon">
        <div className="colophon-inner">
          <span>Sources: ACS 2023 5-year, LBNL Tracking the Sun, CEC, USGS, NASA POWER.</span>
          <span>Model results are screening signals, not causal estimates.</span>
        </div>
      </footer>
    </div>
  );
}
