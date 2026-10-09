import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { useApi } from "../api/useApi";
import { CompareToggle } from "../components/CompareToggle";
import { KeyStats, MetricGroups } from "../components/MetricGroups";
import { ModelTable } from "../components/ModelTable";
import { RegionMap } from "../components/RegionMap";
import { Empty, ErrorNotice, Loading } from "../components/Status";
import { SummaryPanel } from "../components/SummaryPanel";
import { KEY_METRICS } from "../lib/labels";

export function RegionPage() {
  const { regionId = "" } = useParams();
  const detail = useApi(() => api.region(regionId), `region-${regionId}`);
  const models = useApi(() => api.modelOutput(regionId), `models-${regionId}`);

  if (detail.loading && !detail.data) return <Loading label={`Loading ${regionId}`} />;
  if (detail.error) {
    return detail.error instanceof ApiError && detail.error.status === 404 ? (
      <div className="prose">
        <h1>No data for {regionId}</h1>
        <p>This ZIP code isn't in the dataset. <Link to="/">Search for another</Link>.</p>
      </div>
    ) : (
      <ErrorNotice error={detail.error} />
    );
  }
  if (!detail.data) return null;
  const { region, metrics, missing_metric_categories: missing, geometry } = detail.data;
  const utility = region.utility
    ? `${region.utility.utility_name}${region.utility.utility_type ? ` (${region.utility.utility_type.toLowerCase()})` : ""}`
    : "No utility mapping";

  return (
    <article>
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/">Regions</Link> / {region.region_id}</nav>
      <header className="region-head">
        <div>
          <p className="kicker">ZCTA · {region.state}</p>
          <h1><span className="id">{region.region_id}</span></h1>
          <p className="region-sub">{region.county ? `${region.county} County` : "County unknown"} · {utility}</p>
        </div>
        <CompareToggle regionId={region.region_id} />
      </header>

      <KeyStats metrics={metrics} keys={KEY_METRICS} />

      <div className="region-body">
        <SummaryPanel regionId={region.region_id} />
        <aside>
          {geometry ? <RegionMap wkt={geometry.geometry_wkt} label={`ZCTA ${region.region_id}`} /> : <div className="map map-empty">No boundary on file</div>}
          <p className="map-caption">ZCTA {region.region_id} boundary, 2023 Census TIGER/Line.</p>
        </aside>
      </div>

      <section className="section" aria-labelledby="models-heading">
        <div className="section-head">
          <h2 id="models-heading">How it compares with similar places</h2>
        </div>
        <p className="note" style={{ marginBottom: "1rem" }}>
          Each row is one regression of the outcome on demographic, housing, climate, and infrastructure controls. A negative residual
          means less than predicted. Flags mark the bottom quarter for adoption and the top quarter for energy burden.
        </p>
        {models.error && <ErrorNotice error={models.error} />}
        {models.loading && !models.data && <Loading label="Loading model results" />}
        {models.data && (models.data.items.length
          ? <ModelTable outputs={models.data.items} />
          : <Empty>No model results: this ZIP code wasn't in the fitted sample, usually because census data is missing.</Empty>)}
      </section>

      <section className="section" aria-labelledby="metrics-heading">
        <div className="section-head">
          <h2 id="metrics-heading">All indicators</h2>
        </div>
        {metrics.length ? <MetricGroups metrics={metrics} missing={missing} /> : <Empty>No indicators are reported for this ZIP code.</Empty>}
      </section>
    </article>
  );
}
