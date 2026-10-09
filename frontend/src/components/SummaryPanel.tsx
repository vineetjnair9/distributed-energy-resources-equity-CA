import { useState } from "react";
import { api, type Evidence, type SummaryResponse } from "../api/client";
import { useApi } from "../api/useApi";
import { safeHref } from "../lib/safeHref";
import { ErrorNotice, Loading } from "./Status";

const PREVIEW = 5;

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!evidence.length) return <p className="empty">No source records were found.</p>;
  const shown = expanded ? evidence : evidence.slice(0, PREVIEW);
  return (
    <>
      <ol className="sources">
        {shown.map((item) => {
          const href = safeHref(item.source_url);
          return (
            <li key={item.evidence_id} id={`evidence-${item.evidence_id}`}>
              {item.evidence_text}{" "}
              <span className="source-meta">
                {href ? <a href={href} target="_blank" rel="noopener noreferrer">{item.source_name}</a> : item.source_name}
                {" · "}
                <span className="source-id">E{item.evidence_id}</span>
              </span>
            </li>
          );
        })}
      </ol>
      {evidence.length > PREVIEW && (
        <button type="button" className="textbtn" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show fewer sources" : `Show all ${evidence.length} sources`}
        </button>
      )}
    </>
  );
}

export function SummaryBody({ summary }: { summary: SummaryResponse }) {
  const available = summary.status === "available";
  return (
    <div>
      {summary.warnings.length > 0 && (
        <ul className={`caveats ${available ? "" : "caveats-strong"}`}>
          {summary.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      )}
      {available ? (
        <p className="summary-text">{summary.summary_text}</p>
      ) : (
        <p className="summary-unavailable">No grounded summary is shown for this topic.</p>
      )}
      {available && (
        <p className="byline">
          {summary.model_version} · {summary.generated_at ? new Date(summary.generated_at).toLocaleDateString(undefined, { timeZone: "UTC" }) : "undated"} · cites {summary.evidence_ids.length} evidence records
        </p>
      )}
      <h4 className="sources-head">{available ? "Cited evidence" : "Retrieved evidence"}</h4>
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
    <section aria-labelledby="summary-heading">
      <div className="section-head" style={{ marginTop: 0 }}>
        <h2 id="summary-heading">Summary</h2>
      </div>
      <div className="summary-tabs" role="tablist" aria-label="Summary topic">
        {tabs.map((key) => (
          <button
            key={key}
            role="tab"
            type="button"
            aria-selected={category === key}
            className="summary-tab"
            onClick={() => setCategory(key)}
          >
            {names[key] ?? key}
          </button>
        ))}
        {others.length > 0 && (
          <select
            aria-label="Other topics"
            className="summary-more"
            value={others.includes(category) ? category : ""}
            onChange={(event) => event.target.value && setCategory(event.target.value)}
          >
            <option value="">More topics</option>
            {others.map((key) => (
              <option key={key} value={key}>{names[key] ?? key} (sources only)</option>
            ))}
          </select>
        )}
      </div>
      <div role="tabpanel">
        {summary.loading && !summary.data && <Loading label="Loading summary" />}
        {summary.error && <ErrorNotice error={summary.error} />}
        {summary.data && <SummaryBody summary={summary.data} />}
      </div>
      <p className="note" style={{ marginTop: "1rem" }}>
        Written in advance from the sources listed. A summary that can't be traced to this ZIP code's own records is not shown.
      </p>
    </section>
  );
}
