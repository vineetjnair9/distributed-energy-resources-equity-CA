import { useState } from "react";
import { api, type Evidence, type SummaryResponse } from "../api/client";
import { useApi } from "../api/useApi";
import { safeHref } from "../lib/safeHref";
import { ErrorNotice, Loading } from "./Status";

const PREVIEW = 6;

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!evidence.length) return <p className="empty">No evidence records were retrieved.</p>;
  const shown = expanded ? evidence : evidence.slice(0, PREVIEW);
  return (
    <>
      <ol className="evidence">
        {shown.map((item) => (
          <li key={item.evidence_id} id={`evidence-${item.evidence_id}`}>
            <span className="evidence-id">E{item.evidence_id}</span>
            <span className="evidence-text">{item.evidence_text}</span>
            <span className="evidence-source">
              {item.evidence_type === "model_output" ? "Model output" : "Metric"} ·{" "}
              {safeHref(item.source_url) ? (
                <a href={safeHref(item.source_url)!} target="_blank" rel="noopener noreferrer">{item.source_name}</a>
              ) : (
                item.source_name
              )}
            </span>
          </li>
        ))}
      </ol>
      {evidence.length > PREVIEW && (
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show fewer" : `Show all ${evidence.length} evidence records`}
        </button>
      )}
    </>
  );
}

export function SummaryBody({ summary }: { summary: SummaryResponse }) {
  const available = summary.status === "available";
  return (
    <div className="summary-body">
      {summary.warnings.length > 0 && (
        <ul className={`warnings ${available ? "" : "warnings-strong"}`}>
          {summary.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      )}
      {available ? (
        <blockquote className="summary-text">{summary.summary_text}</blockquote>
      ) : (
        <p className="summary-unavailable">No grounded summary is shown for this category.</p>
      )}
      <p className="meta">
        {available ? (
          <>
            Summary #{summary.summary_id} · {summary.model_version} · generated{" "}
            {summary.generated_at ? new Date(summary.generated_at).toLocaleDateString(undefined, { timeZone: "UTC" }) : "unknown"} · cites{" "}
            {summary.evidence_ids.length} evidence records
          </>
        ) : (
          <>Retrieved evidence for this category ({summary.evidence.length} records)</>
        )}
      </p>
      <h4 className="evidence-heading">{available ? "Cited evidence" : "Retrieved evidence"}</h4>
      <EvidenceList evidence={summary.evidence} />
    </div>
  );
}

export function SummaryPanel({ regionId }: { regionId: string }) {
  const labels = useApi(api.summaryCategories, "summary-categories");
  const stored = useApi(() => api.summaries(regionId), `summaries-${regionId}`);
  const [category, setCategory] = useState("overview");
  const summary = useApi(() => api.summary(regionId, category), `summary-${regionId}-${category}`);

  const names = labels.data ?? {};
  const storedSet = new Set(stored.data?.items.map((item) => item.category));
  const all = Object.keys(names);
  const tabs = ["overview", ...all.filter((key) => key !== "overview" && storedSet.has(key))];
  const others = all.filter((key) => !tabs.includes(key));

  return (
    <section className="card summary-panel" aria-labelledby="summary-heading">
      <header className="summary-head">
        <div>
          <h2 id="summary-heading">Grounded summary</h2>
          <p className="caption">
            Generated offline from retrieved evidence only. Each summary lists the records it cites; a summary that cannot be traced to this region's evidence is withheld.
          </p>
        </div>
      </header>
      <div className="tabs" role="tablist" aria-label="Summary category">
        {tabs.map((key) => (
          <button
            key={key}
            role="tab"
            type="button"
            aria-selected={category === key}
            className={`tab ${category === key ? "tab-active" : ""}`}
            onClick={() => setCategory(key)}
          >
            {names[key] ?? key}
          </button>
        ))}
        {others.length > 0 && (
          <select
            aria-label="Other categories"
            className="tab-select"
            value={others.includes(category) ? category : ""}
            onChange={(event) => event.target.value && setCategory(event.target.value)}
          >
            <option value="">Other categories…</option>
            {others.map((key) => (
              <option key={key} value={key}>{names[key] ?? key} (no stored summary)</option>
            ))}
          </select>
        )}
      </div>
      <div role="tabpanel">
        {summary.loading && !summary.data && <Loading label="Retrieving summary" />}
        {summary.error && <ErrorNotice error={summary.error} />}
        {summary.data && <SummaryBody summary={summary.data} />}
      </div>
    </section>
  );
}
