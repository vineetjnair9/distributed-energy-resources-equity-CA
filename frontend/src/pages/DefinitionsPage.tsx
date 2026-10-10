import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../api/useApi";
import { ErrorNotice, Loading } from "../components/Status";
import { slug } from "../lib/anchors";
import { CATEGORY_LABELS, CATEGORY_ORDER, label } from "../lib/labels";
import { safeHref } from "../lib/safeHref";

const RULES = {
  low: "Flagged at or below the 25th percentile residual",
  high: "Flagged at or above the 75th percentile residual",
  absolute: "Flagged when the absolute residual is in the top quarter",
} as const;

export function DefinitionsPage() {
  const defs = useApi(api.definitions, "definitions");
  const { hash } = useLocation();

  // Content loads after navigation, so scroll to the fragment once it exists.
  useEffect(() => {
    if (!defs.data || !hash) return;
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    target?.scrollIntoView();
    target?.classList.add("target-flash");
  }, [defs.data, hash]);

  if (defs.error) return <ErrorNotice error={defs.error} />;
  if (!defs.data) return <Loading label="Loading definitions" />;
  const { terms, metrics, outcomes, specifications, standard_errors } = defs.data;
  const byCategory = CATEGORY_ORDER.map((category) => ({
    category,
    rows: metrics.filter((metric) => metric.category === category),
  })).filter((group) => group.rows.length);

  return (
    <article className="definitions">
      <header className="index-head">
        <h1>Definitions</h1>
        <p className="dek">What every term, indicator and model in the atlas means, and how each is computed.</p>
        <nav className="toc" aria-label="On this page">
          <a href="#key-terms">Key terms</a>
          <a href="#indicators">Indicators</a>
          <a href="#outcomes">Model outcomes</a>
          <a href="#specifications">Specifications</a>
        </nav>
      </header>

      <section className="section" aria-labelledby="key-terms">
        <div className="section-head"><h2 id="key-terms">Key terms</h2></div>
        <dl className="glossary">
          {terms.map(({ term, definition }) => (
            <div key={term} id={slug(term)} className="gloss">
              <dt>{term}</dt>
              <dd>{definition}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="section" aria-labelledby="indicators">
        <div className="section-head"><h2 id="indicators">Indicators</h2></div>
        <p className="note" style={{ marginBottom: "1rem" }}>
          All indicators are for 2023 and are attached to a ZCTA. A blank on a region page means the source has no value for that place.
        </p>
        {byCategory.map(({ category, rows }) => (
          <div key={category} className="def-group">
            <h3>{label(CATEGORY_LABELS, category)}</h3>
            <dl className="glossary">
              {rows.map((metric) => {
                const href = safeHref(metric.source_url);
                return (
                  <div key={metric.metric_name} id={`metric-${slug(metric.metric_name)}`} className="gloss">
                    <dt>
                      {metric.label}
                      <span className="sub mono">{metric.metric_name} · {metric.unit}</span>
                    </dt>
                    <dd>
                      {metric.definition}{" "}
                      <span className="source-meta">
                        Source: {href ? <a href={href} target="_blank" rel="noopener noreferrer">{metric.source_name}</a> : metric.source_name}
                      </span>
                    </dd>
                  </div>
                );
              })}
            </dl>
          </div>
        ))}
      </section>

      <section className="section" aria-labelledby="outcomes">
        <div className="section-head"><h2 id="outcomes">Model outcomes</h2></div>
        <p className="note" style={{ marginBottom: "1rem" }}>
          Each outcome is modeled on the scale below, so a region page's Actual, Predicted and Residual columns are on that scale too,
          not in the indicator's own units. Ranks and flags are computed within each specification's fitted sample.
        </p>
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Outcome</th>
              <th scope="col">Modeled as</th>
              <th scope="col"><a href="#priority">Priority</a> rule</th>
            </tr>
          </thead>
          <tbody>
            {outcomes.map((outcome) => (
              <tr key={outcome.outcome_name} id={`outcome-${slug(outcome.outcome_name)}`}>
                <th scope="row">{outcome.label}<span className="sub mono">{outcome.outcome_name}</span></th>
                <td>{outcome.modeled_as}</td>
                <td>{RULES[outcome.flag_rule]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section" aria-labelledby="specifications">
        <div className="section-head"><h2 id="specifications">Specifications</h2></div>
        <p className="note" style={{ marginBottom: "1rem" }}>
          Ordinary least squares on 2023 cross-sections. Unless stated, each adds to the core terms: log median household income, the
          Black, Hispanic and Asian shares, and the poverty rate. Standard errors: {standard_errors.charAt(0).toLowerCase() + standard_errors.slice(1)}
        </p>
        <dl className="glossary">
          {specifications.map((spec) => (
            <div key={spec.name} id={`spec-${slug(spec.name)}`} className="gloss">
              <dt>{spec.name}</dt>
              <dd>{spec.description}</dd>
            </div>
          ))}
        </dl>
      </section>
    </article>
  );
}
