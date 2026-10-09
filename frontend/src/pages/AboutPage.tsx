export function AboutPage() {
  return (
    <article className="prose">
      <h1>Method</h1>
      <p className="dek">What the numbers are, where they come from, and what they can't tell you.</p>
      <h2>The unit</h2>
      <p>
        Everything is organized by ZIP Code Tabulation Area (ZCTA), the Census Bureau's approximation of a ZIP code. Each one has a
        five-digit ID that ties every indicator, model result, and summary back to the same place.
      </p>
      <h2>Indicators</h2>
      <p>
        Rooftop solar comes from LBNL's Tracking the Sun; battery storage and EV chargers from California Energy Commission exports;
        wind turbines from the USGS turbine database. These are joined to ACS 2023 five-year demographics, CEC energy-burden measures,
        utility usage reports, and NASA POWER climate data. Climate values are coarse grid estimates taken at each ZCTA's center.
      </p>
      <h2>Model results</h2>
      <p>
        Each outcome is regressed (OLS) on a ladder of specifications, from climate alone up to demographic, housing, and
        infrastructure controls with county fixed effects. A ZIP code's residual is ranked against every other ZIP code in the fit.
        For adoption, the bottom quarter is flagged: less solar, storage, or charging than similar places. For energy burden, the
        top quarter is flagged.
      </p>
      <p>
        One specification flagging a place is weak evidence; all of them agreeing is stronger. Either way it's a prompt to look closer,
        not a causal finding.
      </p>
      <h2>Summaries</h2>
      <p>
        Summaries are written ahead of time by a language model working only from a fixed packet of each ZIP code's records, and it must
        cite the records it used. The site shows a summary only when every citation checks out against that ZIP code's data; otherwise
        it says so and lists the records instead.
      </p>
      <p>
        The full API is documented at <a href="/api/docs">/api/docs</a>.
      </p>
    </article>
  );
}
