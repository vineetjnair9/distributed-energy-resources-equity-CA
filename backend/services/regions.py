"""Read-only region queries. Every function takes an open connection and a
region_id, so the five-character ZCTA stays the single join key across layers."""

import sqlite3

from backend.catalog import BURDEN_PRIORITY_OUTCOMES as BURDEN_OUTCOMES
from backend.catalog import DER_PRIORITY_OUTCOMES as DER_OUTCOMES
from backend.catalog import METRIC_COLUMNS
from backend.formatting import format_metric_value

METRIC_CATEGORIES = tuple(dict.fromkeys(category for _, category, _ in METRIC_COLUMNS.values()))


class RegionNotFound(LookupError):
    pass


class UnknownOutcome(ValueError):
    pass


def flag_direction(outcome_name):
    if outcome_name in DER_OUTCOMES:
        return "low"
    if outcome_name in BURDEN_OUTCOMES:
        return "high"
    return "absolute"


def _utility(row):
    if row["utility_id"] is None:
        return None
    return {
        "utility_id": row["utility_id"],
        "utility_acronym": row["utility_acronym"],
        "utility_name": row["utility_name"],
        "utility_type": row["utility_type"],
    }


def _region(row):
    return {
        "region_id": row["region_id"],
        "region_name": row["region_name"],
        "region_type": row["region_type"],
        "state": row["state"],
        "county": row["county"],
        "utility": _utility(row),
    }


REGION_SELECT = """
    SELECT r.region_id, r.region_name, r.region_type, r.state, r.county,
           u.utility_id, u.utility_acronym, u.utility_name, u.utility_type
    FROM regions r
    LEFT JOIN utilities u ON u.utility_id = r.utility_id
"""


def search_regions(conn, *, q=None, county=None, utility=None, limit=50, offset=0):
    filters, params = [], []
    if q:
        filters.append("(r.region_id LIKE ? OR r.region_name LIKE ? OR r.county LIKE ?)")
        params += [f"{q}%", f"%{q}%", f"{q}%"]
    if county:
        filters.append("r.county = ? COLLATE NOCASE")
        params.append(county)
    if utility:
        filters.append("(u.utility_acronym = ? COLLATE NOCASE OR u.utility_name = ? COLLATE NOCASE)")
        params += [utility, utility]
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM regions r LEFT JOIN utilities u "
        f"ON u.utility_id = r.utility_id {where}", params,
    ).fetchone()[0]
    rows = conn.execute(
        f"{REGION_SELECT} {where} ORDER BY r.region_id LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset,
            "items": [_region(row) for row in rows]}


def get_region(conn, region_id):
    row = conn.execute(f"{REGION_SELECT} WHERE r.region_id = ?", (region_id,)).fetchone()
    if row is None:
        raise RegionNotFound(region_id)
    return _region(row)


def get_regions(conn, region_ids):
    """Return regions in request order; raise naming every unknown ID."""
    placeholders = ",".join("?" for _ in region_ids)
    rows = conn.execute(
        f"{REGION_SELECT} WHERE r.region_id IN ({placeholders})", region_ids
    ).fetchall()
    found = {row["region_id"]: _region(row) for row in rows}
    missing = [region_id for region_id in region_ids if region_id not in found]
    if missing:
        raise RegionNotFound(", ".join(missing))
    return [found[region_id] for region_id in region_ids]


def _metric(row):
    return {
        "metric_name": row["metric_name"],
        "metric_value": row["metric_value"],
        "display_value": format_metric_value(row["metric_value"], row["metric_unit"]),
        "metric_unit": row["metric_unit"],
        "metric_category": row["metric_category"],
        "source_name": row["source_name"],
        "observed_at": row["observed_at"],
    }


def get_metrics(conn, region_ids):
    placeholders = ",".join("?" for _ in region_ids)
    return conn.execute(
        f"""
        SELECT region_id, metric_name, metric_value, metric_unit, metric_category,
               source_name, observed_at
        FROM metric_observations
        WHERE region_id IN ({placeholders})
        ORDER BY metric_category, metric_name
        """,
        region_ids,
    ).fetchall()


def get_region_detail(conn, region_id):
    region = get_region(conn, region_id)
    metrics = [_metric(row) for row in get_metrics(conn, [region_id])]
    present = {metric["metric_category"] for metric in metrics}
    geometry = conn.execute(
        "SELECT geometry_wkt, geometry_format, crs FROM region_geometries WHERE region_id = ?",
        (region_id,),
    ).fetchone()
    return {
        "region": region,
        "metrics": metrics,
        "missing_metric_categories": [c for c in METRIC_CATEGORIES if c not in present],
        "geometry": dict(geometry) if geometry is not None else None,
    }


def _model_output(row):
    output = {key: row[key] for key in row.keys() if key != "region_id"}
    if output["priority_flag"] is not None:
        output["priority_flag"] = bool(output["priority_flag"])
    return output


def get_model_outputs(conn, region_id, *, outcome_name=None, model_version=None):
    get_region(conn, region_id)
    filters, params = ["region_id = ?"], [region_id]
    if outcome_name is not None:
        filters.append("outcome_name = ?")
        params.append(outcome_name)
    if model_version is not None:
        filters.append("model_version = ?")
        params.append(model_version)
    rows = conn.execute(
        f"""
        SELECT model_output_id, region_id, outcome_name, model_version, actual_value,
               predicted_value, residual_value, residual_percentile, priority_flag,
               assumptions, generated_at
        FROM model_outputs
        WHERE {' AND '.join(filters)}
        ORDER BY outcome_name, model_version
        """,
        params,
    ).fetchall()
    return {"region_id": region_id, "items": [_model_output(row) for row in rows]}


def get_evidence(conn, region_id, evidence_type=None):
    get_region(conn, region_id)
    query = """
        SELECT evidence_id, region_id, evidence_text, evidence_type, source_name, source_url
        FROM evidence_chunks WHERE region_id = ?
    """
    params = [region_id]
    if evidence_type is not None:
        query += " AND evidence_type = ?"
        params.append(evidence_type)
    return [dict(row) for row in conn.execute(query + " ORDER BY evidence_type, evidence_id",
                                              params)]


def compare_regions(conn, region_ids, overview_lookup):
    """Side-by-side metrics and screening flags; a missing value stays None."""
    regions = get_regions(conn, region_ids)
    metric_rows = {}
    for row in get_metrics(conn, region_ids):
        entry = metric_rows.setdefault(row["metric_name"], {
            "metric_name": row["metric_name"],
            "metric_unit": row["metric_unit"],
            "metric_category": row["metric_category"],
            "values": dict.fromkeys(region_ids),
            "display_values": dict.fromkeys(region_ids),
        })
        entry["values"][row["region_id"]] = row["metric_value"]
        entry["display_values"][row["region_id"]] = format_metric_value(
            row["metric_value"], row["metric_unit"])

    placeholders = ",".join("?" for _ in region_ids)
    model_rows = {}
    for row in conn.execute(
        f"""
        SELECT region_id, outcome_name, model_version, residual_percentile, priority_flag
        FROM model_outputs WHERE region_id IN ({placeholders})
        ORDER BY outcome_name, model_version
        """,
        region_ids,
    ):
        entry = model_rows.setdefault((row["outcome_name"], row["model_version"]), {
            "outcome_name": row["outcome_name"],
            "model_version": row["model_version"],
            "residual_percentile": dict.fromkeys(region_ids),
            "priority_flag": dict.fromkeys(region_ids),
        })
        entry["residual_percentile"][row["region_id"]] = row["residual_percentile"]
        flag = row["priority_flag"]
        entry["priority_flag"][row["region_id"]] = None if flag is None else bool(flag)

    return {
        "region_ids": region_ids,
        "regions": regions,
        "metrics": sorted(metric_rows.values(),
                          key=lambda m: (m["metric_category"] or "", m["metric_name"])),
        "model_outputs": list(model_rows.values()),
        "overviews": {region_id: overview_lookup(region_id) for region_id in region_ids},
    }


def get_facets(conn):
    counties = conn.execute(
        "SELECT county, COUNT(*) AS n FROM regions WHERE county IS NOT NULL "
        "GROUP BY county ORDER BY county"
    ).fetchall()
    utilities = conn.execute(
        """
        SELECT COALESCE(u.utility_acronym, u.utility_name) AS value, u.utility_name,
               COUNT(*) AS n
        FROM regions r JOIN utilities u ON u.utility_id = r.utility_id
        GROUP BY u.utility_id ORDER BY n DESC, value
        """
    ).fetchall()
    outcomes = conn.execute(
        "SELECT outcome_name, COUNT(DISTINCT region_id) AS n FROM model_outputs "
        "GROUP BY outcome_name ORDER BY outcome_name"
    ).fetchall()
    return {
        "counties": [{"value": r["county"], "label": r["county"], "count": r["n"]}
                     for r in counties],
        "utilities": [{"value": r["value"], "label": r["utility_name"], "count": r["n"]}
                      for r in utilities],
        "outcomes": [{"value": r["outcome_name"], "label": r["outcome_name"], "count": r["n"]}
                     for r in outcomes],
    }


def screen_regions(conn, outcome_name, *, county=None, utility=None, limit=20):
    """Regions ranked by how many specifications flag them for one outcome.

    Agreement across specifications is the robustness signal: a region flagged
    by one model only is weaker evidence than one flagged by all of them.
    """
    if conn.execute(
        "SELECT 1 FROM model_outputs WHERE outcome_name = ? LIMIT 1", (outcome_name,)
    ).fetchone() is None:
        raise UnknownOutcome(outcome_name)
    direction = flag_direction(outcome_name)
    # Within equal agreement, the most extreme mean rank comes first.
    tiebreak = "mean_pct DESC" if direction == "high" else "mean_pct ASC"
    filters, params = ["m.outcome_name = ?"], [outcome_name]
    if county:
        filters.append("r.county = ? COLLATE NOCASE")
        params.append(county)
    if utility:
        filters.append(
            "(u.utility_acronym = ? COLLATE NOCASE OR u.utility_name = ? COLLATE NOCASE)")
        params += [utility, utility]
    rows = conn.execute(
        f"""
        SELECT m.region_id,
               SUM(COALESCE(m.priority_flag, 0)) AS flagged,
               COUNT(*) AS specs,
               AVG(m.residual_percentile) AS mean_pct
        FROM model_outputs m
        JOIN regions r ON r.region_id = m.region_id
        LEFT JOIN utilities u ON u.utility_id = r.utility_id
        WHERE {' AND '.join(filters)}
        GROUP BY m.region_id
        HAVING flagged > 0
        ORDER BY flagged * 1.0 / specs DESC, {tiebreak}, m.region_id
        """,
        params,
    ).fetchall()
    shown = rows[:limit]
    regions = {r["region_id"]: r for r in get_regions(conn, [row["region_id"] for row in shown])} \
        if shown else {}
    return {
        "outcome_name": outcome_name,
        "direction": direction,
        "total": len(rows),
        "items": [{
            "region": regions[row["region_id"]],
            "flagged_count": row["flagged"],
            "specification_count": row["specs"],
            "mean_residual_percentile": row["mean_pct"],
        } for row in shown],
    }
