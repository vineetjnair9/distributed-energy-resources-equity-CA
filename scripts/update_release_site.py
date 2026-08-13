#!/usr/bin/env python3
"""Synchronize the release HTML tables and exact claims with generated artifacts."""

from __future__ import annotations

import html
import re

import numpy as np
import pandas as pd

from update_release_manuscript import (
    ROOT, coefficient_with_se, fit_release_baselines, spatial_stars, stars,
)


SITE_PATH = ROOT / "site" / "paper.html"


def replace_table_part(text: str, table_id: str, tag: str, content: str) -> str:
    pattern = rf'(<div class="table-wrap" id="{re.escape(table_id)}">.*?<{tag}>).*?(</{tag}>)'
    updated, count = re.subn(pattern, rf"\1\n{content}\n              \2", text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Expected one {tag} in {table_id}, found {count}")
    return updated


def replace_paragraph(text: str, starts_with: str, replacement: str) -> str:
    pattern = rf"<p>{re.escape(starts_with)}.*?</p>"
    updated, count = re.subn(pattern, f"<p>{replacement}</p>", text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Expected one paragraph beginning {starts_with!r}, found {count}")
    return updated


def replace_caption(text: str, starts_with: str, replacement: str) -> str:
    pattern = rf"<figcaption>{re.escape(starts_with)}.*?</figcaption>"
    updated, count = re.subn(pattern, f"<figcaption>{replacement}</figcaption>", text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Expected one caption beginning {starts_with!r}, found {count}")
    return updated


def code_cell(value: str) -> str:
    return f'<td><span class="coef">{html.escape(value)}</span></td>'


def coefficient_cell(result, term: str) -> str:
    estimate = f"{result.params[term]:.3f}{stars(result.pvalues[term])}"
    error = f"({result.bse[term]:.3f})"
    return f'<td><span class="coef">{estimate}</span><span class="se">{error}</span></td>'


def cluster_profile() -> pd.DataFrame:
    assignments = pd.read_csv(
        ROOT / "outputs" / "tables" / "pca_kmeans_cluster_assignments.csv",
        dtype={"zip_code": "string"},
    )
    source = pd.read_csv(
        ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv",
        dtype={"zip_code": "string"},
    )
    frame = assignments.merge(source, on="zip_code", validate="one_to_one")
    population = frame["total_population"]
    frame["income_k"] = frame["median_household_income"] / 1000
    frame["residual_share"] = 1 - frame[["pct_black", "pct_hispanic", "pct_asian"]].sum(axis=1)
    frame["pv_rate"] = frame["PV_system_size_DC"] * 1000 / population
    frame["storage_rate"] = frame["storage_capacity_mw"] * 100000 / population
    frame["charger_rate"] = frame["total_chargers"] * 1000 / population
    columns = [
        "income_k", "poverty_rate", "pct_black", "pct_hispanic", "pct_asian",
        "residual_share", "pv_rate", "storage_rate", "charger_rate",
    ]
    means = frame.groupby("cluster", sort=True)[columns].mean()
    means.insert(0, "n", frame.groupby("cluster", sort=True).size())
    return means


def main() -> None:
    text = SITE_PATH.read_text()
    frame, fits = fit_release_baselines()

    summary_variables = [
        "y_pv", "y_storage", "y_chargers", "pct_black", "pct_hispanic", "pct_asian",
        "log_median_household_income", "poverty_rate", "pct_bachelors_plus",
        "ghi_mean_kwh_m2_day_2023", "log_kwh", "energy_burden_pct",
        "log_energy_gap_per_capita",
    ]
    summary_rows = []
    for variable in summary_variables:
        series = pd.to_numeric(frame[variable], errors="coerce").dropna()
        values = [series.mean(), series.median(), series.quantile(.25), series.quantile(.75)]
        summary_rows.append(
            f'                <tr><td><code>{variable}</code></td><td>{len(series):,}</td>'
            + "".join(f"<td>{value:.3f}</td>" for value in values)
            + "</tr>"
        )
    text = replace_table_part(text, "tbl-summary", "tbody", "\n".join(summary_rows))

    outcomes = ["y_pv", "y_storage", "y_chargers"]
    terms = ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate"]
    baseline_rows = []
    for term in terms:
        cells = "".join(coefficient_cell(fits[outcome], term) for outcome in outcomes)
        baseline_rows.append(f"                <tr><td><code>{term}</code></td>{cells}</tr>")
    pv, storage, chargers = (fits[outcome] for outcome in outcomes)
    pv_climate = coefficient_with_se(pv, "ghi_mean_kwh_m2_day_2023")
    charger_value = chargers.params["cdd65_2023"]
    charger_p = chargers.pvalues["cdd65_2023"]
    charger_se = chargers.bse["cdd65_2023"]
    baseline_rows.append(
        "                <tr><td>Key climate/resource control</td>"
        f'<td><span class="coef">GHI: {pv_climate.split()[0]}</span><span class="se">{pv_climate.split()[1]}</span></td>'
        '<td><span class="coef">CDD/HDD: n.s.</span></td>'
        f'<td><span class="coef">CDD65: {charger_value:.4f}{stars(charger_p)}</span>'
        f'<span class="se">({charger_se:.4f})</span></td></tr>'
    )
    text = replace_table_part(text, "tbl-baseline", "tbody", "\n".join(baseline_rows))
    baseline_foot = (
        "                <tr><td>N</td>"
        + "".join(f"<td>{int(fits[outcome].nobs):,}</td>" for outcome in outcomes)
        + "</tr>\n                <tr><td>R²</td>"
        + "".join(f"<td>{fits[outcome].rsquared:.3f}</td>" for outcome in outcomes)
        + "</tr>"
    )
    text = replace_table_part(text, "tbl-baseline", "tfoot", baseline_foot)

    model9 = pd.read_csv(
        ROOT / "outputs" / "tables" / "y_storage | Model 9 + pv control (most controlled).csv",
        index_col=0,
    )
    model9_terms = [
        "log_median_household_income", "pct_black", "pct_hispanic", "pct_asian",
        "pct_bachelors_plus", "y_pv",
    ]
    model9_rows = []
    for term in model9_terms:
        row = model9.loc[term]
        p_value = float(row["P>|z|"])
        p_text = "&lt; 0.001" if p_value < .001 else f"{p_value:.3f}"
        model9_rows.append(
            f'                <tr><td><code>{term}</code></td>'
            f'<td><span class="coef">{float(row["Coef."]):.3f}{stars(p_value)}</span></td>'
            f'<td>{float(row["Std.Err."]):.3f}</td><td>{p_text}</td></tr>'
        )
    text = replace_table_part(text, "tbl-storage-m9", "tbody", "\n".join(model9_rows))

    charger_outcomes = ["y_chargers", "y_level1_chargers", "y_level2_chargers", "y_dc_fast_chargers"]
    charger_rows = []
    for term in terms:
        cells = "".join(coefficient_cell(fits[outcome], term) for outcome in charger_outcomes)
        charger_rows.append(f"                <tr><td><code>{term}</code></td>{cells}</tr>")
    text = replace_table_part(text, "tbl-charger-subtypes", "tbody", "\n".join(charger_rows))
    charger_foot = (
        "                <tr><td>N</td>"
        + "".join(f"<td>{int(fits[outcome].nobs):,}</td>" for outcome in charger_outcomes)
        + "</tr>\n                <tr><td>R²</td>"
        + "".join(f"<td>{fits[outcome].rsquared:.3f}</td>" for outcome in charger_outcomes)
        + "</tr>"
    )
    text = replace_table_part(text, "tbl-charger-subtypes", "tfoot", charger_foot)

    colors = {1: "Blue", 2: "Orange", 3: "Green", 4: "Red", 5: "Purple", 6: "Brown"}
    cluster_rows = []
    for cluster, row in cluster_profile().iterrows():
        values = [
            f"{int(row['n']):,}", f"${row['income_k']:.1f}k", f"{row['poverty_rate']:.1%}",
            f"{row['pct_black']:.1%}", f"{row['pct_hispanic']:.1%}", f"{row['pct_asian']:.1%}",
            f"{row['residual_share']:.1%}", f"{row['pv_rate']:.2f}",
            f"{row['storage_rate']:.2f}", f"{row['charger_rate']:.2f}",
        ]
        cluster_rows.append(
            f"                <tr><td>{colors[int(cluster)]} ({int(cluster)})</td>"
            + "".join(f"<td>{value}</td>" for value in values)
            + "</tr>"
        )
    text = replace_table_part(text, "tbl-clusters", "tbody", "\n".join(cluster_rows))

    moran = pd.read_csv(ROOT / "outputs" / "tables" / "morans_i_residuals.csv")
    moran = moran.loc[moran["k"] == 8].pivot(index="outcome", columns="model", values="morans_i")
    moran_labels = [
        ("y_pv", "Solar PV"), ("y_storage", "Storage"),
        ("y_chargers", "EV chargers (aggregate)"),
        ("y_level2_chargers", "EV chargers (Level 2)"),
        ("energy_burden_pct", "Energy burden"),
        ("log_energy_gap_per_capita", "Log affordability gap"),
    ]
    moran_models = ["M1 baseline", "M6A + lat/lon", "M6B county FE", "M8 + demand proxy"]
    moran_rows = []
    for outcome, label in moran_labels:
        moran_rows.append(
            f"                <tr><td>{label}</td>"
            + "".join(f"<td>{moran.loc[outcome, model]:.3f}</td>" for model in moran_models)
            + "</tr>"
        )
    text = replace_table_part(text, "tbl-moran", "tbody", "\n".join(moran_rows))

    conley = pd.read_csv(ROOT / "outputs" / "tables" / "conley_standard_errors.csv")
    term_labels = {
        "log_median_household_income": "Log median income", "pct_black": "% Black",
        "pct_hispanic": "% Hispanic", "pct_asian": "% Asian", "poverty_rate": "Poverty rate",
    }
    outcome_labels = {"y_pv": "Solar PV", "y_storage": "Storage", "y_chargers": "EV chargers (aggregate)"}
    conley_rows = []
    for outcome, outcome_label in outcome_labels.items():
        conley_rows.append(f'                <tr><td colspan="6"><strong>{outcome_label}</strong></td></tr>')
        for term, term_label in term_labels.items():
            row = conley.loc[(conley.outcome == outcome) & (conley.term == term)].iloc[0]
            cells = []
            for se_col in ["se_hc1", "se_conley_50km", "se_conley_100km", "se_conley_200km"]:
                p_col = se_col.replace("se_", "p_")
                cells.append(f"<td>{row[se_col]:.3f}{spatial_stars(row[p_col])}</td>")
            conley_rows.append(
                f'                <tr><td>{term_label}</td><td><span class="coef">{row.coef:.3f}</span></td>'
                + "".join(cells) + "</tr>"
            )
    text = replace_table_part(text, "tbl-conley", "tbody", "\n".join(conley_rows))

    m9 = {term: float(model9.loc[term, "Coef."]) for term in model9_terms}
    text = replace_paragraph(
        text,
        "I also estimate an additional robustness model",
        "I also estimate an additional robustness model, <code>Model 9</code>, that adds "
        "<code>y_pv</code> to the most controlled storage specification. The PV term is positive "
        f"(<code>{m9['y_pv']:.3f}</code>, <code>p &lt; 0.001</code>), while the race coefficients "
        "remain negative and statistically significant: "
        f"<code>pct_black = {m9['pct_black']:.3f}</code>, "
        f"<code>pct_hispanic = {m9['pct_hispanic']:.3f}</code>, and "
        f"<code>pct_asian = {m9['pct_asian']:.3f}</code> (all <code>p &lt; 0.001</code>). "
        f"The conditional education coefficient is also negative (<code>{m9['pct_bachelors_plus']:.3f}</code>, "
        "<code>p = 0.026</code>) despite the positive unadjusted education gradient, consistent "
        "with overlap among education, income, housing, and PV deployment. This suggests that "
        "the storage gap is not explained solely by unequal PV deployment upstream."
    )
    text = replace_paragraph(
        text,
        "The charger-type decomposition helps clarify",
        "The charger-type decomposition helps clarify what is going on. In the standardized "
        "baseline models, the positive aggregate association with <code>poverty_rate</code> is "
        "not present for <code>y_level1_chargers</code> (<code>0.002</code>, <code>p = 0.584</code>). "
        "Instead, it is driven primarily by <code>y_level2_chargers</code> (<code>0.166</code>, "
        "<code>p &lt; 0.001</code>). For <code>y_dc_fast_chargers</code>, the coefficient is positive "
        "but imprecise (<code>0.027</code>, <code>p = 0.202</code>)."
    )
    text = replace_paragraph(
        text,
        "The cluster map in",
        "The cluster map in <a class=\"xref\" href=\"#fig-cluster-map\">Figure 15</a> shows that "
        "these profiles are spatially coherent rather than randomly scattered. Cluster IDs are "
        "ordered by mean household income for stable interpretation. "
        "<a class=\"xref\" href=\"#tbl-clusters\">Table 6</a> shows that clusters 1 and 2 are "
        "the lowest-income and most heavily Hispanic profiles; cluster 5 combines high income, "
        "the largest Asian share, and the strongest charging outcome; and cluster 6 is the "
        "highest-income profile and has the strongest storage outcome. These differences are "
        "consistent with the broader paper argument that access is shaped by bundles of "
        "demographic, economic, housing, and infrastructural conditions."
    )
    text = replace_caption(
        text,
        "<strong>Figure 15.</strong>",
        "<strong>Figure 15.</strong> California ZIP/ZCTA clusters from the exploratory PCA plus "
        "K-means analysis. Cluster IDs are stable labels ordered from lowest to highest mean "
        "household income; the map shows that the resulting profiles are geographically structured."
    )
    text = text.replace(
        "All 72 tests (six outcomes by four specifications by three neighbour counts) return <code>p &lt; 0.001</code>",
        "All 72 tests (six outcomes by four specifications by three neighbour counts) return <code>p ≤ 0.001</code>",
    ).replace(
        "the reported standard errors are likely to be conservative rather than sufficient",
        "county clustering alone is not sufficient",
    )
    SITE_PATH.write_text(text)
    print(f"Updated {SITE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
