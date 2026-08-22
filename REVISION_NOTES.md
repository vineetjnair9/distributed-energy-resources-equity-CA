# Revision notes — Nature Sustainability build

Produced from `site/index.docx` (version saved 2026-08-22) by executing
`NATURE_SUSTAINABILITY_SUBMISSION_PLAN.md`.

## Files
- `site/index_nature_submission.docx` — main manuscript
- `site/supplementary_information.docx` — SI (16 figures, 18 tables)
- The original `site/index.docx` is untouched.

## Compliance
| Check | Result |
|---|---|
| Title | 9 words / 75 chars (limit 10 / 90) |
| Abstract | 150 words, unreferenced (limit 150) |
| Main text | 3,371 words (limit 3,500) |
| Display items | 6 (limit 6) |
| References | 29, all cited, all resolve (guideline ~50) |
| Structure | Introduction (unheaded) → Results → Discussion → Methods |
| Comments | all removed |
| SI cross-referencing | every SI item cited in main text; no dangling references |

## Main-text display items
1. **Fig. 1** — statewide ZCTA geography, three outcomes
2. **Fig. 2** — nested cumulative ladder C1→C5 (`coefficient_path_c1_c5.png`)
3. **Fig. 3** — housing structure and tenure attenuation
4. **Fig. 4** — charger-type decomposition
5. **Table 1** — baseline associations, rebuilt from `outputs/standardized_tables/`
6. **Table 2** — consolidated robustness (β C1, β C5, Conley HAC, spec curve, Oster δ)

## New analysis run for this revision
Outputs in `outputs/nature_revision/`:
- `zero_shares.csv` — Level 1 charging is zero in **97.8%** of ZCTAs; wind 97.5%
- `ppml_negbin.csv` — PPML with population offset; every headline sign and significance holds
- `population_weighted.csv` — weighted vs unweighted baseline
- `spatial_error_model.csv` — ML spatial error model, 8-NN weights (λ = 0.85 / 0.65 / 0.45)
- `affordability_outliers.csv` — with and without the 134 ZCTAs above $1,000 per capita
- `ladder_c1_c5.csv` — reproduction of the nested ladder (matches `REGRESSION_ROBUSTNESS_RESULTS.html`)
- `sd_conversion.csv` — predictor SDs for interpreting standardised coefficients
- `spec_curve_counts.csv` — n/48 significant and same-signed

## Three things that need your decision

**1. Table 3 in the old draft was stale.** The current `outputs/standardized_tables/`
give a *positive and significant* Hispanic-share coefficient for rooftop PV
(0.219, p < 0.001); the old table reported 0.017, not significant. My independent
re-fit matches the current exports, so the old table predates a data refresh. The new
Results text says the PV racial gradient is a Black- and Asian-share result and that
Hispanic share runs the other way for PV alone. **Confirm this is the intended data
vintage before submitting.**

**2. Excluding the affordability outliers kills a published finding.** With the 134
high-gap ZCTAs removed, the positive Asian-share association with the affordability gap
goes from 0.090 (p = 0.010) to −0.019 (p = 0.477), and R² rises from 0.32 to 0.45. The
main text no longer reports it as a finding. The $1,000-per-capita threshold is
documented in Methods and can be changed.

**3. Storage is 98.2% residential — B4 resolves in your favour.** The CEC records are
193,070 residential, 3,211 commercial, 291 utility. A residential-only re-fit reproduces
every sign and significance (Supplementary Table S16). One caveat: my residential-only
reconstruction correlates 0.589 with the `storage_capacity_mw` column in
`combined_der_dataset_w_controls_predictors.csv`, not 1.0, which suggests the processed
file was built from a different vintage or file. Worth tracing.

## Deviations from the plan
- **Figure 3 is the housing attenuation panel and Figure 4 the charger subtype panel**,
  rather than combining the cross-outcome dot-whisker with the subtype figure. The
  dot-whisker is largely redundant with Fig. 2 and the combined image was 4,081 × 8,285 px.
  The dot-whisker is Supplementary Fig. S16.
- **Six uncited references were dropped** (Caballero-Peña, FERC, McAllister, Stokes &
  Warshaw, Borenstein & Bushnell, SEIA/Vote Solar) because the compressed Introduction
  no longer cites them. The duplicate Light et al. entry was merged, and the four
  reference-manager-garbled entries were retyped.
- **The Mendeley field is edited in place.** Do not click "refresh bibliography" in
  Mendeley — it will restore the duplicate and the garbled titles. Fix the Mendeley
  records, or convert the field to static text.

## Still outstanding
- Author list, affiliations, CRediT contributions, funding — placeholders in the file
- Zenodo DOI — `scripts/make_zenodo_bundle.py` exists; deposit and replace the placeholder
- Figure background/crop consistency (meeting note) — not addressed
- Cover letter — Danielle
