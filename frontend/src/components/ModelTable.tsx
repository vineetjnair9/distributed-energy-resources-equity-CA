import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import type { ModelOutput } from "../api/client";
import { outcomeHref, termHref } from "../lib/anchors";
import { OUTCOME_LABELS, flagDirection, isKeySpec, label, modelName, number, percentile } from "../lib/labels";

const OUTCOME_ORDER = Object.keys(OUTCOME_LABELS);
export const outcomeRank = (outcome: string) => OUTCOME_ORDER.indexOf(outcome) + 1 || OUTCOME_ORDER.length + 1;

export function PercentileBar({ value, outcome }: { value: number | null; outcome: string }) {
  if (value === null) return <span className="na">—</span>;
  const direction = flagDirection(outcome);
  return (
    <span className="rank" title={`Residual ranks at the ${percentile(value)} percentile`}>
      <span className="rank-track" aria-hidden>
        {direction !== "absolute" && <span className={`rank-zone zone-${direction}`} />}
        <span className="rank-dot" style={{ left: `${value * 100}%` }} />
      </span>
      <span className="rank-label">{percentile(value)}</span>
    </span>
  );
}

export function FlagBadge({ flag }: { flag: boolean | null | undefined }) {
  if (flag === null || flag === undefined) return <span className="na">—</span>;
  return flag ? <Link to={termHref("Priority")} className="flag deflink">Priority</Link> : <span className="noflag">—</span>;
}

export function ModelTable({ outputs }: { outputs: ModelOutput[] }) {
  const [showAll, setShowAll] = useState(false);
  const hidden = outputs.filter((row) => !isKeySpec(row.model_version)).length;
  const byOutcome = new Map<string, ModelOutput[]>();
  for (const output of outputs) byOutcome.set(output.outcome_name, [...(byOutcome.get(output.outcome_name) ?? []), output]);
  const outcomes = [...byOutcome.entries()].sort(([a], [b]) => outcomeRank(a) - outcomeRank(b));
  return (
    <div className="table-scroll">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Specification</th>
            <th scope="col" className="num">Actual</th>
            <th scope="col" className="num">Predicted</th>
            <th scope="col" className="num">Residual</th>
            <th scope="col"><Link to={termHref("Residual rank")} className="deflink">Residual rank</Link></th>
            <th scope="col">Flag</th>
          </tr>
        </thead>
        <tbody>
          {outcomes.map(([outcome, rows]) => {
            const flagged = rows.filter((row) => row.priority_flag).length;
            return (
              <Fragment key={outcome}>
                <tr className="group-row">
                  <th colSpan={6} scope="colgroup">
                    <Link to={outcomeHref(outcome)} className="deflink" >{label(OUTCOME_LABELS, outcome)}</Link>{" "}
                    <span className={flagged ? "flag" : "muted"} style={{ fontFamily: "var(--sans)", fontSize: "0.8rem", fontWeight: 500 }}>
                      {flagged ? `flagged by ${flagged} of ${rows.length} specifications` : `not flagged by any of ${rows.length} specifications`}
                    </span>
                  </th>
                </tr>
                {rows.filter((row) => showAll || isKeySpec(row.model_version) || !rows.some((r) => isKeySpec(r.model_version))).map((row) => (
                  <tr key={row.model_output_id}>
                    <th scope="row">{modelName(row.model_version)}</th>
                    <td className="num">{number(row.actual_value)}</td>
                    <td className="num">{number(row.predicted_value)}</td>
                    <td className="num">{number(row.residual_value)}</td>
                    <td><PercentileBar value={row.residual_percentile} outcome={outcome} /></td>
                    <td><FlagBadge flag={row.priority_flag} /></td>
                  </tr>
                ))}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      {hidden > 0 && (
        <p style={{ marginTop: "0.75rem" }}>
          <button type="button" className="textbtn" onClick={() => setShowAll(!showAll)}>
            {showAll ? "Show headline specifications only" : `Show all ${outputs.length} specifications (${hidden} more)`}
          </button>
        </p>
      )}
    </div>
  );
}
