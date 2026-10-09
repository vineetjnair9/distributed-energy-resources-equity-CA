import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { CompareToggle } from "../components/CompareToggle";
import { useDebounced } from "../components/RegionSearch";
import { Empty, ErrorNotice, Loading } from "../components/Status";
import { OUTCOME_PHRASES, flagDirection, label, percentile } from "../lib/labels";

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
    <>
      <header className="index-head">
        <h1>Distributed energy across California, ZIP code by ZIP code</h1>
        <p className="dek">
          Rooftop solar, batteries, and EV chargers next to who lives there and what they pay for energy, with regression
          estimates of where adoption falls short of what similar places have.
        </p>
        <label className="search field">
          <span className="sr-only">Search by ZIP code or county</span>
          <input
            className="input input-lg"
            type="search"
            placeholder="ZIP code or county"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </label>
      </header>

      <div className="index-grid">
        <section aria-labelledby="regions-heading">
          <div className="section-head">
            <h2 id="regions-heading">Regions</h2>
          </div>
          <div className="filters">
            <label className="field">
              <span>County</span>
              <select className="select" value={county} onChange={(event) => update({ county: event.target.value })}>
                <option value="">All</option>
                {facets.data?.counties.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Utility</span>
              <select className="select" value={utility} onChange={(event) => update({ utility: event.target.value })}>
                <option value="">All</option>
                {facets.data?.utilities.map((item) => (
                  <option key={item.value} value={item.value}>{item.value}</option>
                ))}
              </select>
            </label>
          </div>
          {regions.error && <ErrorNotice error={regions.error} />}
          {regions.loading && !regions.data && <Loading label="Searching" />}
          {regions.data && (
            <>
              <p className="result-count" aria-live="polite">
                {regions.data.total.toLocaleString()} region{regions.data.total === 1 ? "" : "s"}
              </p>
              {regions.data.items.length === 0 ? (
                <Empty>Nothing matches. Try a shorter ZIP prefix or clear a filter.</Empty>
              ) : (
                <div className="table-scroll">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th scope="col">ZIP</th>
                        <th scope="col">County</th>
                        <th scope="col">Utility</th>
                        <th scope="col" className="right"><span className="sr-only">Compare</span></th>
                      </tr>
                    </thead>
                    <tbody>
                      {regions.data.items.map((region) => (
                        <tr key={region.region_id}>
                          <th scope="row" className="id"><Link to={`/regions/${region.region_id}`}>{region.region_id}</Link></th>
                          <td>{region.county ?? "—"}</td>
                          <td title={region.utility?.utility_name}>{region.utility?.utility_acronym ?? region.utility?.utility_name ?? <span className="na">unmapped</span>}</td>
                          <td className="right"><CompareToggle regionId={region.region_id} compact /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {regions.data.total > PAGE && (
                <div className="pager">
                  <button type="button" className="textbtn" disabled={offset === 0} onClick={() => update({ offset: String(Math.max(0, offset - PAGE)) })}>Previous</button>
                  <span className="mono">{offset + 1}–{Math.min(offset + PAGE, regions.data.total)} of {regions.data.total}</span>
                  <button type="button" className="textbtn" disabled={offset + PAGE >= regions.data.total} onClick={() => update({ offset: String(offset + PAGE) })}>Next</button>
                </div>
              )}
            </>
          )}
        </section>

        <ScreeningCard outcomes={facets.data?.outcomes.map((o) => o.value) ?? []} county={county} utility={utility} />
      </div>
    </>
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
  const picker = (
    <select aria-label="Outcome" className="inline-select" value={active ?? ""} onChange={(event) => setOutcome(event.target.value)}>
      {outcomes.map((value) => <option key={value} value={value}>{label(OUTCOME_PHRASES, value)}</option>)}
    </select>
  );
  return (
    <section aria-labelledby="screen-heading">
      <div className="section-head">
        <h2 id="screen-heading">Falling short</h2>
      </div>
      <p className="lead-sentence">
        Where {picker} {direction === "high" ? "runs higher" : direction === "low" ? "is lower" : "differs most from"} than models
        {direction === "absolute" ? " predict" : " predict for similar places"}
        {county || utility ? ` in ${[county && `${county} County`, utility].filter(Boolean).join(", ")}` : ""}.
      </p>
      {screening.error && <ErrorNotice error={screening.error} />}
      {screening.loading && !screening.data && <Loading />}
      {screening.data && (screening.data.items.length === 0 ? (
        <Empty>No region is flagged for this outcome with the current filters.</Empty>
      ) : (
        <table className="table table-hover" style={{ marginTop: "1rem" }}>
          <thead>
            <tr>
              <th scope="col">ZIP</th>
              <th scope="col">County</th>
              <th scope="col" className="num">Models flagging</th>
              <th scope="col" className="num" title="Mean residual rank across specifications">Mean rank</th>
            </tr>
          </thead>
          <tbody>
            {screening.data.items.map((row) => (
              <tr key={row.region.region_id}>
                <th scope="row" className="id"><Link to={`/regions/${row.region.region_id}`}>{row.region.region_id}</Link></th>
                <td>{row.region.county}</td>
                <td className="num">
                  <span className={row.flagged_count === row.specification_count ? "flag" : undefined}>
                    {row.flagged_count} of {row.specification_count}
                  </span>
                </td>
                <td className="num">{percentile(row.mean_residual_percentile)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
      {screening.data && screening.data.total > screening.data.items.length && (
        <p className="note" style={{ marginTop: "0.6rem" }}>Top {screening.data.items.length} of {screening.data.total} flagged.</p>
      )}
      <p className="note" style={{ marginTop: "0.6rem" }}>
        Ranked by how many model specifications agree. <Link to="/about">How the models work</Link>
      </p>
    </section>
  );
}
