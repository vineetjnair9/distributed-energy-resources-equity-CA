import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, type CompareResponse } from "../api/client";
import { useApi } from "../api/useApi";
import { FlagBadge, PercentileBar, outcomeRank } from "../components/ModelTable";
import { RegionPicker } from "../components/RegionSearch";
import { Empty, ErrorNotice, Loading } from "../components/Status";
import { SummaryBody } from "../components/SummaryPanel";
import { MAX_COMPARE, useCompareSelection } from "../lib/compareSelection";
import { CATEGORY_LABELS, CATEGORY_ORDER, METRIC_LABELS, OUTCOME_LABELS, label, modelName } from "../lib/labels";

export function ComparePage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const selection = useCompareSelection();
  const fromUrl = (params.get("ids") ?? "").split(",").map((id) => id.trim()).filter(Boolean);

  // A shared /compare?ids= link wins over the stored selection; afterwards the
  // URL follows the selection so the page stays linkable.
  useEffect(() => {
    if (fromUrl.length) selection.set(fromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const ids = selection.ids;
  useEffect(() => {
    // Plain commas keep shared links readable (URLSearchParams would encode them).
    navigate({ search: ids.length ? `?ids=${ids.join(",")}` : "" }, { replace: true });
  }, [ids, navigate]);

  const comparison = useApi(ids.length >= 2 ? () => api.compare(ids) : null, `compare-${ids.join(",")}`);

  return (
    <>
      <header className="index-head">
        <h1>Compare ZIP codes</h1>
        <p className="dek">Up to {MAX_COMPARE} side by side. ▲ and ▼ mark the highest and lowest value in each row; a dash means not reported.</p>
      </header>
      <div className="picked" aria-label="Selected regions">
        {ids.map((id) => (
          <span key={id} className="picked-item">
            <Link to={`/regions/${id}`}>{id}</Link>
            <button type="button" aria-label={`Remove ${id}`} onClick={() => selection.toggle(id)}>×</button>
          </span>
        ))}
        {ids.length > 0 && <button type="button" className="textbtn" onClick={selection.clear}>clear all</button>}
      </div>
      {ids.length < MAX_COMPARE ? (
        <RegionPicker exclude={ids} onPick={(region) => selection.toggle(region.region_id)} />
      ) : (
        <p className="note">That's the maximum. Remove one to add another.</p>
      )}
      {ids.length < 2 && <Empty>Add {2 - ids.length} more to compare.</Empty>}
      {comparison.error && <ErrorNotice error={comparison.error} />}
      {comparison.loading && !comparison.data && <Loading label="Comparing" />}
      {comparison.data && ids.length >= 2 && <CompareTables data={comparison.data} />}
    </>
  );
}

export function extremes(values: (number | null | undefined)[]) {
  const present = values.filter((value): value is number => value !== null && value !== undefined);
  if (present.length < 2) return { max: null, min: null };
  const max = Math.max(...present);
  const min = Math.min(...present);
  return max === min ? { max: null, min: null } : { max, min };
}

export function CompareTables({ data }: { data: CompareResponse }) {
  const ids = data.region_ids;
  const categories = [...new Set(data.metrics.map((metric) => metric.metric_category ?? "other"))].sort(
    (a, b) => (CATEGORY_ORDER.indexOf(a) + 1 || 99) - (CATEGORY_ORDER.indexOf(b) + 1 || 99),
  );
  const head = (first: string) => (
    <thead>
      <tr>
        <th scope="col" className="sticky-col">{first}</th>
        {data.regions.map((region) => (
          <th key={region.region_id} scope="col" className="num">
            <Link to={`/regions/${region.region_id}`} className="id">{region.region_id}</Link>
            <span className="sub">{region.county}</span>
          </th>
        ))}
      </tr>
    </thead>
  );
  return (
    <>
      <section className="section">
        <div className="section-head"><h2>Indicators</h2></div>
        <div className="table-scroll">
          <table className="table compare-table">
            {head("")}
            {categories.map((category) => (
              <tbody key={category}>
                <tr className="group-row"><th colSpan={ids.length + 1} scope="colgroup">{label(CATEGORY_LABELS, category)}</th></tr>
                {data.metrics.filter((metric) => (metric.metric_category ?? "other") === category).map((metric) => {
                  const { max, min } = extremes(ids.map((id) => metric.values[id]));
                  return (
                    <tr key={metric.metric_name}>
                      <th scope="row" className="sticky-col">{label(METRIC_LABELS, metric.metric_name)}</th>
                      {ids.map((id) => {
                        const value = metric.values[id];
                        const mark = value === max ? "hi" : value === min ? "lo" : "";
                        return (
                          <td key={id} className={`num ${mark ? `cell-${mark}` : ""}`}>
                            {metric.display_values[id] ?? <span className="na">—</span>}
                            {mark && <span className="sr-only">{mark === "hi" ? " (highest)" : " (lowest)"}</span>}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            ))}
          </table>
        </div>
      </section>

      <section className="section">
        <div className="section-head"><h2>Model results</h2></div>
        {data.model_outputs.length === 0 ? <Empty>None of these ZIP codes has model results.</Empty> : (
          <div className="table-scroll">
            <table className="table compare-table">
              {head("Outcome and specification")}
              <tbody>
                {[...data.model_outputs].sort((a, b) => outcomeRank(a.outcome_name) - outcomeRank(b.outcome_name)).map((row) => (
                  <tr key={`${row.outcome_name}-${row.model_version}`}>
                    <th scope="row" className="sticky-col">
                      {label(OUTCOME_LABELS, row.outcome_name)}
                      <span className="sub">{modelName(row.model_version)}</span>
                    </th>
                    {ids.map((id) => (
                      <td key={id}>
                        <PercentileBar value={row.residual_percentile[id] ?? null} outcome={row.outcome_name} />
                        <FlagBadge flag={row.priority_flag[id]} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <div className="section-head"><h2>Summaries</h2></div>
        <div className="overview-grid">
          {data.regions.map((region) => (
            <div key={region.region_id}>
              <h3><Link to={`/regions/${region.region_id}`} className="id">{region.region_id}</Link> <span className="sub" style={{ display: "inline" }}>{region.county}</span></h3>
              <SummaryBody summary={data.overviews[region.region_id]} />
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
