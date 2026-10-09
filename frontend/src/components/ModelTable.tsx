import type { ModelOutput } from "../api/client";
import { OUTCOME_LABELS, flagDirection, flagMeaning, label, modelName, number, percentile } from "../lib/labels";

export function PercentileBar({ value, outcome }: { value: number | null; outcome: string }) {
  if (value === null) return <span className="na">—</span>;
  const direction = flagDirection(outcome);
  return (
    <span className="pbar" title={`${percentile(value)} percentile residual`}>
      <span className="pbar-track">
        {direction !== "absolute" && <span className={`pbar-zone zone-${direction}`} />}
        <span className="pbar-dot" style={{ left: `${value * 100}%` }} />
      </span>
      <span className="pbar-label">{percentile(value)}</span>
    </span>
  );
}

export function FlagBadge({ flag }: { flag: boolean | null | undefined }) {
  if (flag === null || flag === undefined) return <span className="na">—</span>;
  return flag ? <span className="badge badge-flag">Priority</span> : <span className="badge">Not flagged</span>;
}

const OUTCOME_ORDER = Object.keys(OUTCOME_LABELS);
export const outcomeRank = (outcome: string) => (OUTCOME_ORDER.indexOf(outcome) + 1 || OUTCOME_ORDER.length + 1);

export function ModelTable({ outputs }: { outputs: ModelOutput[] }) {
  const byOutcome = new Map<string, ModelOutput[]>();
  for (const output of outputs) byOutcome.set(output.outcome_name, [...(byOutcome.get(output.outcome_name) ?? []), output]);
  return (
    <div className="model-blocks">
      {[...byOutcome.entries()].sort(([a], [b]) => outcomeRank(a) - outcomeRank(b)).map(([outcome, rows]) => {
        const flagged = rows.filter((row) => row.priority_flag).length;
        return (
          <section key={outcome} className="card model-card">
            <header className="model-head">
              <h3>{label(OUTCOME_LABELS, outcome)}</h3>
              <span className={`agreement ${flagged ? "agreement-flag" : ""}`}>
                {flagged} of {rows.length} specifications flag this region
              </span>
            </header>
            <div className="table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Specification</th>
                    <th scope="col" className="num">Actual</th>
                    <th scope="col" className="num">Predicted</th>
                    <th scope="col" className="num">Residual</th>
                    <th scope="col">Residual rank</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.model_output_id}>
                      <th scope="row" className="spec">{modelName(row.model_version)}</th>
                      <td className="num">{number(row.actual_value)}</td>
                      <td className="num">{number(row.predicted_value)}</td>
                      <td className={`num ${row.residual_value !== null && row.residual_value < 0 ? "neg" : ""}`}>{number(row.residual_value)}</td>
                      <td><PercentileBar value={row.residual_percentile} outcome={outcome} /></td>
                      <td><FlagBadge flag={row.priority_flag} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="caption">{flagMeaning(outcome)} {rows[0]?.assumptions}</p>
          </section>
        );
      })}
    </div>
  );
}
