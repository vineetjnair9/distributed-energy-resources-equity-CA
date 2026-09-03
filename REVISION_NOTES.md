# Revision notes — Nature Sustainability submission

Produced from `site/index.docx` by executing `NATURE_SUSTAINABILITY_SUBMISSION_PLAN.md`.
Rebuild both documents with `scripts/manuscript/build_manuscript.py` and
`scripts/manuscript/build_supplementary.py` (see `scripts/manuscript/README.md`).

## Files
- `site/index_nature_submission.docx` — main manuscript
- `site/supplementary_information.docx` — SI: 13 Notes, 17 figures, 19 tables
- The original `site/index.docx` is untouched.

## Compliance
| Check | Result |
|---|---|
| Title | 9 words / 75 chars (limit 10 / 90) |
| Abstract | 149 words, unreferenced (limit 150) |
| Main text | 3,276 words (limit 3,500) |
| Display items | 6 (limit 6) |
| References | 29, all cited, all resolve (guideline ~50) |
| Structure | Introduction (unheaded) → Results → Discussion → Methods |
| Comments | all removed |
| SI cross-referencing | all 49 SI items cited in main text; no dangling references |
| Spelling | American English throughout (`scripts/manuscript/spelling.py`) |

## Main-text display items
1. **Fig. 1** — statewide ZCTA geography, three outcomes
2. **Fig. 2** — focal coefficients across the **model series**, by technology
   (`coefficient_path_across_models.png`) — the paper's central comparison
3. **Fig. 3** — housing structure and tenure attenuation
4. **Fig. 4** — charger-type decomposition
5. **Table 1** — baseline associations, rebuilt from `outputs/standardized_tables/`
6. **Table 2** — consolidated robustness (β C1, β C5, Conley HAC, spec curve, Oster δ)

Results are ordered by evidential strength, not technology convention: divergence →
**storage** (strongest on every measure) → solar → **charging** (most distinctive) →
stacked specification → affordability. The nested cumulative ladder is a short Results
subsection; it corroborates the model series rather than replacing it, and lives in full
in Supplementary Note S2.

## What to submit now, and what waits

**Initial submission does not need Extended Data, and does not need final formatting.**
Nature's policy: *"For initial submission you may include Extended Data items as regular
display items in the body of the manuscript or as Supplementary Information. But if
accepted for publication, all Extended Data will need to be properly formatted."* Nature
Sustainability adds that an initial submission *"does not need to be specially
formatted, as long as the study is described in a way that is suitable for editorial
assessment and peer review"* — PDF, Word or LaTeX all accepted, with detailed formatting
required only on acceptance. The 10-item Extended Data cap and its styling rules live on
the **AIP** (Accepted In Principle) page and apply then, not now.

**Supplementary Information is a separate file, and must be a single combined PDF.** Not
merged into the main manuscript. Convert `supplementary_information.docx` to PDF before
uploading and check that the 17 figures survive at usable resolution. Complex tables may
go separately as .xlsx or .csv if any prove unwieldy. SI is published as supplied and is
not copy-edited, which is the reason it is written as readable prose rather than a
caption list.

**If the paper reaches revision, revisit Extended Data.** Up to 10 Extended Data display
items are permitted, on top of the six main items and the SI. Extended Data sits between
the two: styled to journal standards and cited as discrete items in the main text, where
SI is not. The natural candidates, in order:

1. Supplementary Figs. S1–S3 — the three per-outcome model-series robustness panels
2. Supplementary Fig. S4 — the C1–C5 nested ladder coefficient paths
3. Supplementary Fig. S5 — the specification curve
4. Supplementary Table S5 — the full C1–C5 coefficient table

Promoting the first two would give the robustness evidence real prominence without
touching the six main display items. It is a genuine restructure — a third tier in both
builders and a third numbering series to keep in sync — so it is not worth doing
speculatively before the paper has an editor's attention.

## New analysis run for this revision
`scripts/nature_revision_analysis.py` regenerates everything in `outputs/nature_revision/`:
- `zero_shares.csv` — Level 1 charging is zero in **97.8%** of ZCTAs; wind 97.5%
- `ppml_negbin.csv` — PPML with population offset; every headline sign and significance holds
- `population_weighted.csv` — weighted vs unweighted baseline
- `spatial_error_model.csv` — ML spatial error model, 8-NN weights (λ = 0.85 / 0.65 / 0.45)
- `affordability_outliers.csv` — with and without the 134 ZCTAs above $1,000 per capita
- `storage_by_sector.csv` — all sectors vs residential-only storage capacity
- `ladder_c1_c5.csv` — reproduction of the nested ladder (matches `REGRESSION_ROBUSTNESS_RESULTS.html`)
- `sd_conversion.csv` — predictor SDs for interpreting standardized coefficients
- `spec_curve_counts.csv` — n/48 significant and same-signed

## Three things that need your decision

**1. Table 3 in the old draft was stale.** The current `outputs/standardized_tables/`
give a *positive and significant* Hispanic-share coefficient for rooftop solar
(0.219, p < 0.001); the old table reported 0.017, not significant. An independent re-fit
matches the current exports, so the old table predates a data refresh. The new Results
text treats the solar racial gradient as a Black- and Asian-share result and says
Hispanic share runs the other way for solar alone. **Confirm this is the intended data
vintage before submitting.**

**2. Excluding the affordability outliers kills a previously reported finding.** With the
134 high-gap ZCTAs removed, the positive Asian-share association with the affordability
gap goes from 0.090 (p = 0.010) to −0.019 (p = 0.477), and R² rises from 0.32 to 0.45.
The main text no longer reports it. The $1,000-per-capita threshold is documented in
Methods and in Supplementary Note S9, and can be changed.

**3. Storage is 98.2% residential — the behind-the-meter reading holds.** The CEC records
are 193,070 residential, 3,211 commercial, 291 utility. A residential-only re-fit
reproduces every sign and significance (Supplementary Table S12). One caveat: the
residential-only reconstruction correlates 0.589 with the `storage_capacity_mw` column in
`combined_der_dataset_w_controls_predictors.csv`, not 1.0, which suggests the processed
file was built from a different vintage or file. Worth tracing.

## Deviations from the plan
- **Figure 2 is the model-series coefficient-path export, not the nested ladder.** The
  first build made the stacked ladder the centrepiece and pushed every model-series
  robustness panel to the SI, which inverted the intended emphasis. The ladder is now a
  short Results subsection plus Supplementary Note S2.
- **Figure 3 is housing attenuation and Figure 4 the charger subtype panel**, rather than
  combining the cross-outcome dot-whisker with the subtype figure — the dot-whisker is
  largely redundant with Fig. 2 and the combined image was 4,081 × 8,285 px. The
  dot-whisker was dropped rather than kept as a redundant SI item.
- **Six uncited references were dropped** (Caballero-Peña, FERC, McAllister, Stokes &
  Warshaw, Borenstein & Bushnell, SEIA/Vote Solar) because the compressed Introduction no
  longer cites them. The duplicate Light et al. entry was merged and the four
  reference-manager-garbled entries were retyped.
- **The Mendeley field is edited in place.** Do not click "refresh bibliography" in
  Mendeley — it will restore the duplicate and the garbled titles. Fix the Mendeley
  records, or convert the field to static text.
- **American spelling is a drafting preference, not a requirement.** Nature journals set
  British spelling in their own house style and convert at proof stage.

## Still outstanding
- Author list, affiliations, CRediT contributions, funding — placeholders in the file
- Cover letter — Danielle
- Zenodo DOI — `scripts/make_zenodo_bundle.py` exists; deposit and replace the
  placeholder. The data availability statement is currently future-tense, which is a
  common desk-stage query.
- Convert the SI to a single PDF before upload
- Figure 2's x-axis still reads "Model ladder / M1…M8" inside the PNG. The caption calls
  it the model series; the axis label needs regenerating in the plotting script.
- Figure background and crop consistency across panels (from the 8/21 review meeting)
