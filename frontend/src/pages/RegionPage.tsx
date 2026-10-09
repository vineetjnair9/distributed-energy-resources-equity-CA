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

  if (detail.loading && !detail.data) return <Loading label={`Loading ZCTA ${regionId}`} />;
  if (detail.error) {
    return detail.error instanceof ApiError && detail.error.status === 404 ? (
      <div className="card narrow">
        <h1>ZCTA {regionId} not found</h1>
        <p>This ZIP code is not in the dataset. <Link to="/">Search for another region</Link>.</p>
      </div>
    ) : (
      <ErrorNotice error={detail.error} />
    );
  }
  if (!detail.data) return null;
  const { region, metrics, missing_metric_categories: missing, geometry } = detail.data;

  return (
    <article className="region">
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/">Explore</Link> / {region.region_id}</nav>
      <header className="region-head">
        <div>
          <p className="eyebrow">{region.region_type.toUpperCase()} · {region.state}</p>
          <h1>{region.region_id}</h1>
          <p className="region-sub">
            {region.county ? `${region.county} County` : "County unknown"} ·{" "}
            {region.utility ? `${region.utility.utility_name}${region.utility.utility_type ? ` (${region.utility.utility_type})` : ""}` : "No utility mapping"}
          </p>
        </div>
        <CompareToggle regionId={region.region_id} />
      </header>

      <div className="region-top">
        {geometry ? <RegionMap wkt={geometry.geometry_wkt} label={`ZCTA ${region.region_id}`} /> : <div className="map map-empty">No boundary available</div>}
        <KeyStats metrics={metrics} keys={KEY_METRICS} />
      </div>

      <SummaryPanel regionId={region.region_id} />

      <section aria-labelledby="models-heading">
        <h2 id="models-heading" className="section-title">Model screening</h2>
        <p className="caption section-caption">
          Residuals from offline regressions of each outcome on demographic, housing, climate, and infrastructure controls. A residual compares this ZCTA to places with similar characteristics; it is a screening signal, not a causal estimate.
        </p>
        {models.error && <ErrorNotice error={models.error} />}
        {models.loading && !models.data && <Loading label="Loading model outputs" />}
        {models.data && (models.data.items.length ? <ModelTable outputs={models.data.items} /> : <Empty>No model outputs: this ZCTA was not in the fitted sample, usually because demographic data is missing.</Empty>)}
      </section>

      <section aria-labelledby="metrics-heading">
        <h2 id="metrics-heading" className="section-title">Indicators</h2>
        {metrics.length ? <MetricGroups metrics={metrics} missing={missing} /> : <Empty>No indicators are reported for this ZCTA.</Empty>}
      </section>
    </article>
  );
}
