export function AboutPage() {
  return (
    <article className="prose card narrow">
      <h1>How this works</h1>
      <p>
        Every record in the tool hangs off one key: the five-character California ZCTA (<code>region_id</code>). Metrics, model outputs, evidence, and summaries are stored in separate tables and joined only on that key.
      </p>
      <h2>Indicators</h2>
      <p>
        Observed DER (LBNL Tracking the Sun PV, CEC storage and EV charger exports, USGS wind turbines) are aggregated to ZCTAs and merged with ACS 2023 five-year demographics, CEC energy-burden indicators, utility usage reports, and NASA POWER climate. Weather and resource values are coarse gridded estimates at each ZCTA's centroid.
      </p>
      <h2>Model screening</h2>
      <p>
        Regressions are fit offline (<code>notebooks/regression.ipynb</code>) across a ladder of specifications, from climate controls only to demographic, housing, and infrastructure controls with county fixed effects. Each ZCTA's residual is ranked within the fitted sample. For DER outcomes, a residual at or below the 25th percentile flags a <strong>priority</strong> region: adoption lower than similar places would predict. For energy burden, at or above the 75th percentile flags burden higher than predicted. Agreement across specifications is the robustness signal. Residuals are screening signals, not causal effects.
      </p>
      <h2>Grounded summaries</h2>
      <p>
        Summaries are generated offline, never per request. For each region and category the generator retrieves a bounded evidence packet of metric and model records, generates from that packet with structured output, and stores the evidence IDs it cited. The API then:
      </p>
      <ul>
        <li>returns the cited evidence with every summary, with sources;</li>
        <li>withholds a summary that cites no evidence or cites another region's evidence;</li>
        <li>when no summary exists, says so and shows the retrieved evidence instead of text;</li>
        <li>flags thin regions with an explicit not-enough-data overview.</li>
      </ul>
      <p>
        Full API reference: <a href="/api/docs">/api/docs</a>.
      </p>
    </article>
  );
}
