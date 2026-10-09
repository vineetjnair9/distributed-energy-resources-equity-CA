import type { Metric } from "../api/client";
import { CATEGORY_LABELS, CATEGORY_ORDER, METRIC_LABELS, label } from "../lib/labels";

export function MetricGroups({ metrics, missing }: { metrics: Metric[]; missing: string[] }) {
  const groups = new Map<string, Metric[]>();
  for (const metric of metrics) {
    const key = metric.metric_category ?? "other";
    groups.set(key, [...(groups.get(key) ?? []), metric]);
  }
  const order = [...CATEGORY_ORDER, ...[...groups.keys()].filter((key) => !CATEGORY_ORDER.includes(key))];
  return (
    <div className="metric-groups">
      {order
        .filter((category) => groups.has(category) || missing.includes(category))
        .map((category) => (
          <section key={category} className="card metric-card" aria-labelledby={`cat-${category}`}>
            <h3 id={`cat-${category}`}>{label(CATEGORY_LABELS, category)}</h3>
            {groups.has(category) ? (
              <dl>
                {groups.get(category)!.map((metric) => (
                  <div key={metric.metric_name} className="metric-row">
                    <dt title={metric.metric_name}>{label(METRIC_LABELS, metric.metric_name)}</dt>
                    <dd>{metric.display_value}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="missing">Not reported for this ZCTA.</p>
            )}
            {groups.has(category) && (
              <p className="source">Source: {[...new Set(groups.get(category)!.map((m) => m.source_name))].join("; ")}</p>
            )}
          </section>
        ))}
    </div>
  );
}

export function KeyStats({ metrics, keys }: { metrics: Metric[]; keys: string[] }) {
  const byName = new Map(metrics.map((metric) => [metric.metric_name, metric]));
  return (
    <dl className="key-stats">
      {keys.map((key) => (
        <div key={key} className="stat">
          <dt>{label(METRIC_LABELS, key)}</dt>
          <dd>{byName.get(key)?.display_value ?? <span className="na">Not reported</span>}</dd>
        </div>
      ))}
    </dl>
  );
}
