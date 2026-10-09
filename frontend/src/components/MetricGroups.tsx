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
    <div className="facts">
      {order
        .filter((category) => groups.has(category) || missing.includes(category))
        .map((category) => {
          const rows = groups.get(category);
          return (
            <section key={category} className="fact-group" aria-labelledby={`cat-${category}`}>
              <h3 id={`cat-${category}`}>{label(CATEGORY_LABELS, category)}</h3>
              {rows ? (
                <>
                  <dl>
                    {rows.map((metric) => (
                      <div key={metric.metric_name} className="fact">
                        <dt title={metric.metric_name}>{label(METRIC_LABELS, metric.metric_name)}</dt>
                        <dd>{metric.display_value}</dd>
                      </div>
                    ))}
                  </dl>
                  <p className="fact-source">{[...new Set(rows.map((m) => m.source_name))].join("; ")}</p>
                </>
              ) : (
                <p className="empty">Not reported for this ZIP code.</p>
              )}
            </section>
          );
        })}
    </div>
  );
}

export function KeyStats({ metrics, keys }: { metrics: Metric[]; keys: string[] }) {
  const byName = new Map(metrics.map((metric) => [metric.metric_name, metric]));
  return (
    <dl className="figures">
      {keys.map((key) => (
        <div key={key} className="figure">
          <dt>{label(METRIC_LABELS, key)}</dt>
          <dd>{byName.get(key)?.display_value ?? <span className="na">Not reported</span>}</dd>
        </div>
      ))}
    </dl>
  );
}
