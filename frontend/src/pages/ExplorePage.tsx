import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { CompareToggle } from "../components/CompareToggle";
import { useDebounced } from "../components/RegionSearch";
import { Empty, ErrorNotice, Loading } from "../components/Status";
import { OUTCOME_LABELS, flagDirection, label, percentile } from "../lib/labels";

const PAGE = 25;

export function ExplorePage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const county = params.get("county") ?? "";
  const utility = params.get("utility") ?? "";
  const offset = Number(params.get("offset") ?? 0) || 0;
  const [text, setText] = useState(q);
  const debounced = useDebounced(text.trim(), 250);

  const update = (next: Record<string, string>) => {
    const merged = new URLSearchParams(params);
    for (const [key, value] of Object.entries(next)) value ? merged.set(key, value) : merged.delete(key);
    if (!("offset" in next)) merged.delete("offset");
    setParams(merged, { replace: true });
  };
  useEffect(() => {
    if (debounced !== q) update({ q: debounced });
    // Only the debounced text drives this; URL changes elsewhere must not loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  const facets = useApi(api.facets, "facets");
  const regions = useApi(
    () => api.regions({ q, county, utility, limit: PAGE, offset }),
    `regions-${q}-${county}-${utility}-${offset}`,
  );

  return (
    <div className="explore">
      <section className="hero">
        <h1>Where is distributed energy lagging what places predict?</h1>
        <p className="lede">
          Look up any California ZIP code (ZCTA) to see rooftop solar, storage, and EV charging alongside demographics, energy burden, and offline regression screening. Then compare places side by side.
        </p>
      </section>

      <div className="explore-grid">
        <section className="card" aria-labelledby="find-heading">
          <h2 id="find-heading">Find a region</h2>
          <div className="filters">
            <label className="field field-grow">
              <span>ZIP code or county</span>
              <input
                className="input"
                type="search"
                placeholder="e.g. 90001 or Fresno"
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </label>
            <label className="field">
              <span>County</span>
              <select className="input" value={county} onChange={(event) => update({ county: event.target.value })}>
                <option value="">All counties</option>
                {facets.data?.counties.map((item) => (
                  <option key={item.value} value={item.value}>{item.label} ({item.count})</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Utility</span>
              <select className="input" value={utility} onChange={(event) => update({ utility: event.target.value })}>
                <option value="">All utilities</option>
                {facets.data?.utilities.map((item) => (
                  <option key={item.value} value={item.value}>{item.value} ({item.count})</option>
                ))}
              </select>
            </label>
          </div>
          {regions.error && <ErrorNotice error={regions.error} />}
          {regions.loading && !regions.data && <Loading label="Searching regions" />}
          {regions.data && (
            <>
              <p className="result-count" aria-live="polite">
                {regions.data.total.toLocaleString()} region{regions.data.total === 1 ? "" : "s"}
              </p>
              {regions.data.items.length === 0 ? (
                <Empty>No regions match. Try a shorter ZIP prefix or clear a filter.</Empty>
              ) : (
                <div className="table-scroll">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th scope="col">ZCTA</th>
                        <th scope="col">County</th>
                        <th scope="col">Utility</th>
                        <th scope="col"><span className="sr-only">Compare</span></th>
                      </tr>
                    </thead>
                    <tbody>
                      {regions.data.items.map((region) => (
                        <tr key={region.region_id}>
                          <th scope="row"><Link to={`/regions/${region.region_id}`}>{region.region_id}</Link></th>
                          <td>{region.county ?? "—"}</td>
                          <td title={region.utility?.utility_name}>{region.utility?.utility_acronym ?? region.utility?.utility_name ?? <span className="na">Unmapped</span>}</td>
                          <td className="right"><CompareToggle regionId={region.region_id} compact /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {regions.data.total > PAGE && (
                <div className="pager">
                  <button type="button" className="btn btn-ghost btn-sm" disabled={offset === 0} onClick={() => update({ offset: String(Math.max(0, offset - PAGE)) })}>← Previous</button>
                  <span>{offset + 1}–{Math.min(offset + PAGE, regions.data.total)} of {regions.data.total}</span>
                  <button type="button" className="btn btn-ghost btn-sm" disabled={offset + PAGE >= regions.data.total} onClick={() => update({ offset: String(offset + PAGE) })}>Next →</button>
                </div>
              )}
            </>
          )}
        </section>

        <ScreeningCard outcomes={facets.data?.outcomes.map((o) => o.value) ?? []} county={county} utility={utility} />
      </div>
    </div>
  );
}

function ScreeningCard({ outcomes, county, utility }: { outcomes: string[]; county: string; utility: string }) {
  const [outcome, setOutcome] = useState("y_pv");
  const active = outcomes.includes(outcome) ? outcome : outcomes[0];
  const screening = useApi(
    active ? () => api.screening({ outcome_name: active, county, utility, limit: 10 }) : null,
    `screen-${active}-${county}-${utility}`,
  );
  const direction = active ? flagDirection(active) : "low";
  return (
    <section className="card" aria-labelledby="screen-heading">
      <h2 id="screen-heading">Priority screening</h2>
      <p className="caption">
        {direction === "high"
          ? "Regions where observed burden is higher than the models predict, ranked by how many specifications agree."
          : "Regions where observed adoption is lower than the models predict, ranked by how many specifications agree."}
        {county || utility ? ` Filtered to ${[county && `${county} County`, utility].filter(Boolean).join(", ")}.` : ""}
      </p>
      <label className="field">
        <span>Outcome</span>
        <select className="input" value={active ?? ""} onChange={(event) => setOutcome(event.target.value)}>
          {outcomes.map((value) => <option key={value} value={value}>{label(OUTCOME_LABELS, value)}</option>)}
        </select>
      </label>
      {screening.error && <ErrorNotice error={screening.error} />}
      {screening.loading && !screening.data && <Loading />}
      {screening.data && (screening.data.items.length === 0 ? (
        <Empty>No region is flagged for this outcome with the current filters.</Empty>
      ) : (
        <ol className="screen-list">
          {screening.data.items.map((row) => (
            <li key={row.region.region_id}>
              <Link to={`/regions/${row.region.region_id}`} className="screen-link">
                <span className="screen-id">{row.region.region_id}</span>
                <span className="screen-county">{row.region.county}</span>
              </Link>
              <span className="agree" aria-label={`${row.flagged_count} of ${row.specification_count} specifications flag this region`}>
                {Array.from({ length: row.specification_count }, (_, i) => (
                  <span key={i} className={`pip ${i < row.flagged_count ? "pip-on" : ""}`} />
                ))}
                <span className="agree-text">{row.flagged_count}/{row.specification_count}</span>
              </span>
              <span className="screen-pct" title="Mean residual rank across specifications">{percentile(row.mean_residual_percentile)}</span>
            </li>
          ))}
        </ol>
      ))}
      {screening.data && screening.data.total > screening.data.items.length && (
        <p className="caption">Showing the top {screening.data.items.length} of {screening.data.total} flagged regions.</p>
      )}
    </section>
  );
}
