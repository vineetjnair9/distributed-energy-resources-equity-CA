# Nature Sustainability submission plan — `site/index.docx`

**Target:** *Nature Sustainability*, Article format
**Source of truth for decisions:** Vineet's 33 comments on the pre-submission audit
(artifact `ebb5c054`), the 8/21/26 paper-review meeting notes, and the 13 unresolved
comments inside `site/index.docx`. Every decision is transcribed into §1 — do not
re-litigate them.
**Companion doc:** `REGRESSION_ROBUSTNESS_PLAN.md` (the C1–C5 rebuild, already
implemented) and `REGRESSION_ROBUSTNESS_RESULTS.html` (its results).
**Status when this plan was written:** manuscript unchanged since 8/19; the C1–C5 ladder,
spec curve, and Oster δ all exist in `outputs/` but nothing in the prose references them.

---

## 0. Ground rules for the implementer

1. **Phase A (analysis) blocks Phase C (prose).** Several rewrites depend on numbers that
   do not exist yet. Do not write the abstract, Results, or Discussion until §2 is done.
   Phase B (restructure) can run in parallel with Phase A.
2. **Never invent a number.** Every figure quoted in the manuscript must trace to a file
   in `outputs/tables/` or `outputs/standardized_figures/`. If a number is needed and no
   file has it, add it to the §2 task list rather than estimating.
3. **Standardized coefficients everywhere** (decision B6). One scale, labelled in every
   table header, figure axis, and sentence. Raw coefficients appear only in SI.
4. **The word "ladder" is reserved** for the new nested C1–C5 sequence. The old M1–M9
   fan is a **"model series"** or **"control-block sensitivity analysis"** — never a
   ladder, never "increasingly rigorous" (meeting decision; also `REGRESSION_ROBUSTNESS_PLAN.md` §1).
5. **No development-log language.** Nothing about parsing faults, refreshed baselines,
   regenerated audits, repos, or asset folders. See §6.
6. **Cross-references become Word fields**, not typed numbers, so the next structural
   edit does not reopen §7.
7. **Work on a branch.** `git checkout -b claude/nature-sust-revision`. Commit
   `site/index.docx` after each phase so diffs are recoverable.

### Hard limits (Nature Sustainability, Article)

| Element | Limit | Current | Delta |
|---|---|---|---|
| Title | ≤10 words / 90 chars | 17 words | cut ~7 words |
| Abstract | ≤150 words, unreferenced | 255 | cut 105 |
| Main text | ≤3,500 words (excl. abstract, Methods, refs, legends) | 6,816 | **cut 3,316** |
| Display items | ≤6 figures and/or tables | 30 | move 24 to SI |
| References | ~50 | 36 | headroom |
| Structure | Introduction (no heading) → Results → Discussion → Methods | 8 numbered sections | restructure |

The main-text cut is the single largest job in this plan. §4 allocates it line by line.

---

## 1. Decision register

Vineet's decision is authoritative. "Action" is the implementation.

### Tier 1 — blocking

| ID | Issue | Decision | Action | Phase |
|---|---|---|---|---|
| **B1** | Level 1 chargers described as "household outlets" | *"Ignore — state as assumption about dataset"* | **Upgrade to a verified statement, not an assumption.** `data/processed/ev_chargers.csv` has `access_type` = `Public` for all 18,453 station rows, and only 256 Level 1 ports statewide. So the inventory is public/shared-use only and residential charging is genuinely unobserved. Say that in one Methods sentence and delete "household outlets" everywhere. This *helps* the paper — it is direct support for "counts measure infrastructure, not usable access." | A+C |
| **B2** | Level 1 null rests on R²=0.006 | *"Look into accounting for 0-count ZCTAs"* | **97.8% of ZCTAs have zero Level 1 chargers** (median 0, max 52). The Level 1 model is uninterpretable. Drop Level 1 as a reported outcome in main text; state the zero share and say it is too sparse to test. Zero shares for every outcome go in a SI table (§2.1). | A+C |
| **B3** | Workplace/commercial siting asserted with no host data | *"No running new model — slightly reframe text to clarify"* | Reframe to a hypothesis in abstract, Results, and Discussion. Meeting note adds: state plainly that the trends are **driven by Level 2, likely commercial and industrial**. Optional zero-cost support: tabulate `station_name` / `street_address` keywords descriptively — no new model. | C |
| **B4** | Storage never stated to be behind-the-meter | *"yes modify text"* | **Verified answerable:** `data/raw/storage/EnergyStorage_Cleaned_August2024_ada.xlsx` has a `Customer Sector` column — 4,957 Residential, 41 Commercial, 2 Utility. Storage is essentially all customer-sited. **First confirm which raw file feeds `aggregated_storage.csv`** — the second file (`Storage_Map_Zip_Pie…xlsx`) splits 3,931/1,069, which would change the statement. Then add the Methods sentence and a SI sensitivity dropping non-residential rows. | A+C |
| **B5** | Table 3 uses a different climate control per outcome | *"we used the climate controls that are most relevant for each DER — so we think this is OK?"* | **Keep the design, defend it explicitly.** Add two sentences to Methods stating that each outcome takes its physically relevant resource control (GHI for PV, degree days for storage, CDD65 for charging) and that this is a deliberate choice, not an inconsistency. Also note the C1–C5 ladder holds the control fixed within outcome, so cross-outcome comparability rests on the standardized scale rather than on an identical RHS. Drop the phrase "one consistent model ladder across all three DER types." | C |
| **B6** | Raw and standardized coefficients mixed | *"Yes use/report standardized coeffs throughout"* | Standardized only in main text. Label every table header, figure axis, and in-text number. Raw tables → SI. | C |

### Tier 2 — substantive

| ID | Issue | Decision | Action | Phase |
|---|---|---|---|---|
| **S1** | No interpretable effect sizes | *"Yes try adding language like this wherever it makes sense"* | Meeting note: "interpret standardized coefficients in a more intuitive, policy-relevant way." For each headline result add a plain-language gloss: "a one-standard-deviation higher Black share (≈X pp) is associated with a Y% lower storage rate." Compute SDs from the analysis sample; put the conversion table in SI. | A+C |
| **S2** | R² 0.079–0.188 unaddressed | *"Yes please add that statement"* | One sentence under the baseline table: the objective is coefficient stability under conditioning, not prediction; low R² is expected for area-level cross-sections with strong local heterogeneity. Note that R² rises to 0.49 (PV) / 0.42 (storage) at C5. | C |
| **S3** | log(1+rate) OLS on zero-inflated counts | *"Ok please implement this fix"* | Meeting: "implement the zero-inflated count model fix for charger and storage, especially due to many zero counts." Run PPML / negative binomial with population offset for chargers and storage. Report sign/significance agreement in SI; one main-text sentence. | A |
| **S4** | Unweighted ZCTA regressions | *"Yes go ahead"* | Population-weighted C1 and C5 as a SI robustness table. One main-text sentence only if results move. | A |
| **S5** | ~21% of ZCTAs dropped, uncharacterized | *"Ignore this"* | **Skip.** No action. | — |
| **S6** | Spatial dependence corrected in inference only | *"Try doing it but add to results only if it looks OK"* | Fit a spatial error model (SEM) on the C1 and C5 specifications for PV, storage, chargers using `scripts/spatial_diagnostics.py` weights. **Gate:** include in Results only if focal coefficients keep sign and rough magnitude. Otherwise SI-only, or omit and keep the existing Conley HAC treatment. | A |
| **S7** | Model 9 labelled "most controlled" but conditions on `y_pv` | *"Ok go ahead"* | Rename the exported label away from "most controlled". Reframe as answering one narrow question — the storage gap is not the solar gap restated — not as a better estimate. Note it is a bad control. | A+C |
| **S8** | Model 9A labelled "predicting burden" | *"Ok go ahead"* | Rename to "DER–burden association". Keep the non-causal caveat adjacent to the result. | A+C |
| **S9** | Energy burden mean 2.2%; affordability gap undefined | *"Ok — also check for skewed affordability gap data and run models with and without the outlier ZCTAs"* | **Confirmed severe.** Per-capita gap: median **$75**, max **$236,464**; the top 100 ZCTAs hold **92.3%** of the statewide gap; **134 ZCTAs exceed $1,000 per capita**. Meeting: likely a CEC source error. Define the outlier rule, run with and without, **cleaner version to main text, alternative to appendix**. Also give `log_energy_gap_per_capita` an actual formula in Methods and reconcile the 2.2% burden level with the published range in one sentence. | A+C |
| **S10** | Multiple comparisons | *"Ok"* | One sentence in Methods. State which findings survive without p-value hair-splitting — the spec curve (§2.5) now answers this quantitatively. | C |
| **S11** | "rules out an income-based reading" | *"Ok"* | → "is hard to square with". | C |
| **S12** | §4.1 misstates Table 9 on the Asian charging coefficient | *"Ok"* | → "significant at some but not all distance cutoffs" (significant at 50 km and 200 km, not at 100 km). | C |
| **S13** | Abstract lacks the caveats the Conclusion carries | *"Ok"* | Abstract must carry the housing-attenuation qualifier and the precision caveat. See §4.1 — the 150-word rewrite handles this. | C |

### Tier 3 — consistency, references, journal

| ID | Issue | Decision | Action |
|---|---|---|---|
| **C1** | All Methods cross-refs off by one subsection | *"Fix"* | §7 has the table. Convert to Word fields. Mostly moot after the Nature restructure — but verify every one. |
| **C2** | Roadmap paragraph wrong | *"Keep limitations as a subsection but fix cross ref"* | Limitations stays a Methods subsection. Nature format has no numbered sections, so the roadmap paragraph is **deleted entirely** (Nature Articles do not use them) — this also recovers ~90 words. |
| **C3** | Display items out of order | *"Fix at end"* | Renumber in order of first appearance after §5 settles. Last step before delivery. |
| **C4** | Appendix headings skip a level (8.0.1–8.0.5) | *"Fix at end"* | Moot — the appendix becomes Supplementary Information with its own numbering (S1, S2…). |
| **C5** | Two passages point at a folder on disk | *"Delete"* | Delete both sentences outright. |
| **C6** | Development-log language | *"Ok please fix all of these"* | §6 has the five passages and their replacements. |
| **C7** | Per-model N never reported | *"Ok"* | Add N (and cluster count where clustered) to every table. `outputs/tables/*fit stats.csv` already carries these. |
| **C8** | "ZIP/ZCTA" compound; "significant remainder" ambiguous | *"Yes just define & use ZCTA throughout. Also remove ambiguity"* | Global replace (§6). Define ZCTA once in Methods. |
| **R1–R5** | Bibliography | *"Please fix all these"* | §8. |
| **J2** | No front/back matter | *"Take a 1st pass at these — we'll fix later"* | §9. First pass only; Vineet finalises authorship and funding. |
| **J3** | 30 display items | *"Try to consolidate/combine some of the main text tables + take a 1st pass at moving more items to SI"* | §5. |
| **J4** | Wind | *"Yes move to SI"* | Remove §4.8 and Figure 16 from main text; drop the Wind MW panel from the cross-outcome figure. Note: **97.5% of ZCTAs have zero wind capacity** — another reason it does not belong. |
| **J5** | 13 open comments in the docx | *"Please fix any unresolved threads"* | §9.3. |

---

## 2. Phase A — analysis work that must complete first

All new work goes in `notebooks/regression_robustness_ladder.ipynb` or a new
`notebooks/nature_revision_extras.ipynb`. Do not modify `regression.ipynb`.

### 2.1 Zero-count audit (blocks B2, S3, J4)

Emit `outputs/tables/zero_shares.csv` — for each outcome: N, % zero, median, max, raw
mean. Already computed on the pop ≥ 1,000 sample (N=1,422); reproduce inside the
notebook so it tracks the analysis sample:

| Outcome | % zero | median | max |
|---|---|---|---|
| PV capacity | 5.3 | 6.38 | 142.1 |
| Storage MW | 6.6 | 0.95 | 8.2 |
| Chargers (aggregate) | 19.0 | 16 | 800 |
| **Level 1 chargers** | **97.8** | **0** | 52 |
| Level 2 chargers | 22.3 | 9 | 768 |
| DC fast chargers | 44.2 | 2 | 235 |
| Wind MW | 97.5 | 0 | 1,542.5 |

**Statewide Level 1 port count is 256**, against 40,078 Level 2 and 13,852 DC fast.

### 2.2 Charger data provenance (blocks B1, B3)

Confirm and document: `access_type` is `Public` for 100% of rows in
`data/processed/ev_chargers.csv`. Write the finding into `data/raw/SOURCES.md` and the
Methods text. Optionally tabulate `station_name`/`street_address` keyword classes
(retail, workplace, municipal, hotel, multifamily) as a descriptive SI table — this is
free and directly supports B3 without a new model.

### 2.3 Storage sector confirmation (blocks B4)

1. Trace which raw file produces `data/processed/aggregated_storage.csv`.
2. Report the `Customer Sector` distribution for that file.
3. Emit a SI sensitivity: storage models re-fit excluding non-Residential rows.
4. If the aggregation already filters to Residential, say so in Methods and skip 3.

### 2.4 Affordability-gap outliers (blocks S9)

1. Define the outlier rule. Recommended: per-capita gap > $1,000 (134 ZCTAs, ~9.4% of
   the sample) — but check the distribution for a natural break first and document
   whichever rule is used.
2. Re-fit the two affordability outcomes with and without those ZCTAs.
3. **Cleaner (outlier-excluded) version → main text; full-sample version → SI.**
4. Add a Methods sentence attributing the anomaly to the CEC source.

### 2.5 Assemble the robustness numbers already computed

No new fitting — read from existing files and build the two consolidated main-text
tables in §5:

- `outputs/tables/spec_curve.csv` — 1,920 rows (48 specs × 10 outcomes × 4 terms)
- `outputs/tables/oster_delta.csv`
- `outputs/tables/*fit stats.csv` — N, clusters, R² per model
- `outputs/tables/conley_standard_errors.csv`
- `outputs/tables/morans_i_residuals.csv`

### 2.6 New models

| Task | Spec | Output | Gate |
|---|---|---|---|
| PPML / negative binomial (S3) | count outcome, `log(population)` offset, C1 and C5 RHS; chargers + storage | SI table | none — report either way |
| Population weighting (S4) | C1 and C5, `weights=total_population` | SI table | main text only if results move |
| Spatial error model (S6) | C1 and C5, SEM on the 8-NN weights from `scripts/spatial_diagnostics.py` | SI table | **main text only if signs and magnitudes hold** |

### 2.7 Standard-deviation conversion table (S1)

For each focal predictor, emit its SD on the analysis sample so the prose can convert a
standardized coefficient into a percentage-point change. Ship as a SI table.

### 2.8 Label renames (S7, S8)

In `regression.ipynb`'s label constants:
- `Model 9 + pv control (most controlled)` → `Model 9 (storage, conditional on local PV)`
- `Model 9A (predicting burden)` → `Model 9A (DER–burden association)`

Re-export affected tables and figures.

---

## 3. Phase B — restructure to Nature Sustainability format

### 3.1 Target skeleton

```
Title (≤10 words)
Authors, affiliations, corresponding author
Abstract (≤150 words, unreferenced)
[Introduction — NO heading]              ~750 words
Results                                  ~1,550 words
  <topical subheadings>
Discussion                               ~1,200 words
  <topical subheadings>
Methods                                  no cap; target ≤3,000
  <topical subheadings, incl. Limitations>
Data availability
Code availability
References (~36)
Author contributions
Competing interests
Figure legends
Supplementary Information (separate file)
```

### 3.2 Section mapping

| Current | Destination |
|---|---|
| §1 Abstract | Abstract, rewritten to 150 words (§4.1) |
| §2 Introduction (424 w) + §3 Background (1,401 w) | **Merged into the unheaded Introduction, 750 words total.** This is the largest single cut: 1,825 → 750. |
| §4 Results (3,192 w) | Results, 1,550 words (§4.3) |
| §5 Discussion (1,455 w) + §7 Conclusion (344 w) | **Merged Discussion, 1,200 words.** Conclusion disappears as a section; its last two sentences become the Discussion's closing paragraph. |
| §6 Methods (3,896 w) | Methods, ≤3,000. §6.11 Limitations stays as a Methods subheading (decision C2). |
| §8 Appendix | Supplementary Information, separate file, renumbered S1… |

### 3.3 Numbered sections are removed

Nature Articles do not number sections. Delete all section numbers and the §2.2 roadmap
paragraph. Every "Section X.Y" cross-reference in the body must become either a named
reference ("see Methods") or be deleted — this resolves most of §7 automatically, but
**verify each one** rather than assuming.

---

## 4. Phase C — section-by-section rewrite spec

### 4.1 Abstract — rewrite to ≤150 words

Must contain, in this order:
1. The question: does DER inequity repeat across technologies, or change form?
2. The data: 1,390 California ZCTAs, three technologies, one harmonized dataset.
3. The headline: the technologies do not share a disparity pattern.
4. **The housing qualifier (S13):** area-level housing type and tenure absorb 32–53% of
   the race coefficients for PV and storage.
5. **What survives the fully stacked specification (§4.4):** storage disparities survive
   for all three race terms; PV survives for Asian share only; aggregate charging does
   not survive.
6. Charging: counts rise with poverty, concentrated in Level 2 — infrastructure, not
   usable access.
7. The claim: race-neutral, count-based planning frameworks are insufficient.

**Delete:** "at household outlets" (B1); bare coefficients `2.00` and `2.24` with no
scale (S1/B6); "A significant remainder does not" (C8 ambiguity).
**Unreferenced** — remove any bracketed citations.

### 4.2 Title — cut to ≤10 words / 90 chars

Current (17 words): *"The Unequal Energy Transition: Racial and Socioeconomic Disparities
in Distributed Energy Resource Adoption Across California"*

Candidates:
- "Racial disparities in distributed energy adoption differ by technology" (9)
- "Clean energy inequity changes form across distributed energy technologies" (9)
- "Distributed energy inequity is technology-specific, not uniform, in California" (9)

Prefer one that carries the paper's actual novelty — that the *form* of inequity changes
by technology — rather than restating that disparities exist.

### 4.3 Results — 3,192 → ~1,550 words

Keep, compressed:

| Subheading | Source | Target |
|---|---|---|
| Disparities differ by technology | §4.1 | 300 |
| Rooftop solar and storage | §4.2 + §4.3 merged | 400 |
| Charging measures infrastructure, not access | §4.4 | 350 |
| **Disparities under a fully stacked specification** | **NEW — §4.4 below** | 400 |
| Energy burden context | §4.5, cut hard | 100 |

**Delete from main text** (→ SI): §4.6 descriptive nonlinear gradients, §4.7 exploratory
clustering, §4.8 wind, §4.9 overall interpretation (its content belongs in the
Discussion's opening). Meeting decision covers all four.

Specific line edits:
- §4.1: fix the Table 9 misstatement (S12) — "significant at some but not all distance
  cutoffs."
- §4.4: delete "the refreshed aggregate charger baseline" and "much weaker than before"
  (C6). State the Level 1 zero share (97.8%) instead of reporting its coefficient (B2).
  State that trends are driven by Level 2, likely commercial and industrial (B3).
- §4.5: state the outlier rule and that main-text estimates exclude the high-gap ZCTAs
  (S9).

### 4.4 NEW Results subsection — "Disparities under a fully stacked specification"

**~400 words. This is the section Vineet asked for.** Source:
`REGRESSION_ROBUSTNESS_RESULTS.html`.

Content, in order:

1. **Why.** The models above vary one control block at a time — a *model series* that
   isolates which block moves which coefficient. It is not a nested sequence, and a
   reader cannot tell from it whether the controls *jointly* absorb the race
   coefficients. So we also fit a genuinely nested cumulative ladder.

2. **What.** C1 (core: income, race, poverty, climate) → C2 (+ education, housing value)
   → C3 (+ housing structure, tenure) → C4 (+ utility FE) → C5 (+ county FE,
   county-clustered SEs, climate dropped). All rungs fit on one frozen common sample —
   **N = 1,160, 42 county clusters, identical at every rung**, so movement is controls,
   not sample drift. A further over-controlled model O adds demand and infrastructure,
   which sit on the causal path; it is reported as a conservative lower bound only.

3. **Result — state it honestly, it is weaker than the headline models.** Report from the
   C1→C5 table:

   | Outcome | Term | β C1 | p | β C5 | p | Survives C5? |
   |---|---|---|---|---|---|---|
   | Solar PV | % Black | −0.154 | <0.001 | −0.017 | 0.472 | **no** |
   | | % Hispanic | −0.058 | 0.197 | +0.047 | 0.506 | no |
   | | % Asian | −0.303 | <0.001 | −0.114 | **0.010** | **yes** |
   | | Log income | +0.173 | 0.005 | +0.188 | 0.104 | no |
   | Storage | % Black | −0.103 | <0.001 | −0.034 | **0.009** | **yes** |
   | | % Hispanic | −0.196 | <0.001 | −0.113 | **0.016** | **yes** |
   | | % Asian | −0.248 | <0.001 | −0.116 | **<0.001** | **yes** |
   | EV chargers | % Hispanic | −0.097 | <0.001 | −0.037 | 0.580 | no |
   | | % Asian | +0.046 | 0.027 | +0.013 | 0.700 | no |

   The sentence to write: **storage is the one technology whose racial disparities
   survive the fully stacked specification on all three terms; solar PV survives only
   for Asian share; aggregate charging does not survive at all.** Coefficients attenuate
   by roughly two-thirds to three-quarters. Do not write "disparities still survive"
   without the per-technology qualifier — the table does not support it.

4. **Specification curve.** Across all 48 valid confounder-block combinations:

   | Outcome | Income | % Black | % Hispanic | % Asian |
   |---|---|---|---|---|
   | Solar PV | 46/48 | 28/48 | 31/48 | 34/48 |
   | Storage | 44/48 | 36/48 | 44/48 | **48/48** |
   | EV chargers (agg.) | 15/48 | **0/48** | 22/48 | 4/48 |

   The 0/48 for aggregate charging on % Black is worth one sentence — it is the
   quantitative version of the paper's existing charger-composition argument.

5. **Oster δ.** Storage % Hispanic 1.99, PV % Asian 1.57, storage % Asian 1.29 clear the
   conventional δ ≥ 1 threshold and can be cited directly. **Do not report δ for PV
   income or aggregate charging** — the full confounder set *increases* those
   coefficients, so Oster's assumption fails and the returned values (−32.6, +26.0) are
   not interpretable. One sentence noting the non-attenuation, and cross-reference to
   the Discussion (§4.5 item 4).

6. **Framing sentence to close:** the fully stacked estimates are the conservative read;
   the model series above shows *which* controls do the absorbing, and housing does most
   of it.

**Main-text display item:** `outputs/standardized_figures/coefficient_path_c1_c5.png`
→ Figure 2 (§5).
**To SI:** `y_pv_ladder.png`, `y_storage_ladder.png`, `y_chargers_ladder.png`,
`spec_curve_y_*.png`, the full C1–C5 coefficient table, `oster_delta.csv`, the VIF-by-rung
table, and the N/R² path table.

### 4.5 Discussion — 1,455 + 344 → ~1,200 words

Keep: what persists and what changes by technology; mechanisms; policy relevance;
policy measures. Fold the Conclusion's last two sentences in as the closing paragraph.

Specific edits:
- **S11:** "rules out an income-based reading" → "is hard to square with".
- **B3:** the workplace/commercial siting claim becomes explicitly a hypothesis, with
  the Level 2 / commercial-industrial framing from the meeting.
- **C6:** delete "much weaker than before".
- **NEW paragraph — PV's non-attenuating income effect.** Flagged in
  `REGRESSION_ROBUSTNESS_RESULTS.html` §6 as the most surprising result in the rebuild:
  adding the full confounder set *increases* the PV income coefficient (raw 0.43 → 0.47)
  rather than shrinking it. That is a substantive finding about non-price barriers, not
  a robustness footnote. ~100 words.
- **B4:** if storage is confirmed residential, the resilience argument stands as written;
  add the one-clause qualifier. If it is not, the resilience framing in this section must
  be softened throughout.
- Keep §5.5 (policy measures) largely intact — it is the strongest section — but compress
  the three actor paragraphs to roughly two-thirds length.

### 4.6 Methods — 3,896 → ≤3,000 words

Additions:
- **B1:** the charger inventory is public/shared-use only (`access_type` = Public,
  100% of rows); residential charging is unobserved. 2 sentences.
- **B2:** zero shares by outcome, cross-referenced to the SI table. 1 sentence.
- **B4:** storage customer-sector composition. 1–2 sentences.
- **B5:** the per-outcome resource control is deliberate; justify. 2 sentences.
- **S9:** `log_energy_gap_per_capita` formula; the outlier rule; the CEC source caveat;
  one sentence reconciling the 2.2% burden mean with published estimates. ~80 words.
- **S10:** multiple comparisons acknowledgement. 1 sentence.
- **S3/S4/S6:** one sentence each pointing to the SI robustness tables.
- **C7:** N and cluster counts in every table.
- The C1–C5 ladder specification (mirroring `REGRESSION_ROBUSTNESS_PLAN.md` §2):
  confounders vs mediators, the frozen common sample, why county FE and utility FE are
  not stacked. ~150 words.

Deletions (recovers the word budget):
- The PG&E parsing-fault passage → neutral coverage statement (§6).
- The Models 2C/2D implementation-behavior sentence (§6).
- §6.11's first paragraph, which duplicates its second almost verbatim.
- The equation-by-equation walkthrough of Models 3A/3B/3C/4R/6A/6B — compress the
  sibling series to one paragraph plus a SI table, since the C-ladder now carries the
  identification argument.

---

## 5. Display items

### 5.1 Main text — exactly 6

| # | Item | Source | Notes |
|---|---|---|---|
| **Fig 1** | California ZCTA geography, three headline outcomes | `outputs/figures/generated/california_outcome_geography_panel.png` | Existing Figure 1. Fix background/crop to match the others (meeting note). |
| **Fig 2** | **Nested C1→C5 coefficient paths, three headline outcomes** | `outputs/standardized_figures/coefficient_path_c1_c5.png` | The paper's central identification visual. Replaces old Figure 4. |
| **Fig 3** | Cross-outcome comparison **+** charger subtype, two panels | `baseline_der_outcomes_dot_whisker.png` + `charger_subtype_comparison.png` | **Combine into one two-panel figure. Drop the Wind MW panel (J4).** |
| **Fig 4** | Housing structure and tenure attenuation | `housing_structure_attenuation.png` | Old Figure 21. Carries the 32–53% result that the abstract now leads with. |
| **Table 1** | Baseline (C1) standardized coefficients, three headline outcomes | rebuild from `outputs/standardized_tables/` | Add N, R², and an interpretable-effect column (S1). Replaces old Table 3. |
| **Table 2** | **Consolidated robustness summary** | build in Phase A §2.5 | One row per outcome × focal term; columns: β C1, β C5, Conley HAC significance, spec-curve n/48, Oster δ. **Replaces old Tables 4, 5, 8, and 9** — this is the consolidation Vineet asked for in J3. |

### 5.2 To Supplementary Information

Old Tables 1, 2, 4, 5, 6, 7, 8, 9 and old Figures 2, 3, 5–20 (except those promoted
above), plus everything new from Phase A:

- Variable definitions; summary statistics; zero shares by outcome
- Full M1–M9 model-series coefficient tables (the "control-block sensitivity" fan)
- Full C1–C5 tables, per-outcome ladder panels, spec-curve figures, Oster δ table
- VIF by rung; Moran's I; Conley HAC full table
- Wind (all of it); descriptive LOWESS gradients; PCA/K-means clustering
- PPML/NB, population-weighted, and SEM robustness tables
- Affordability-gap full-sample models; storage non-residential sensitivity
- SD conversion table

Number as Supplementary Figure S1… and Supplementary Table S1… in order of first
mention.

### 5.3 Cross-referencing rule

**Every SI item must be cited at least once in the main text** — this was Vineet's
existing docx comment and it is a Nature requirement. After renumbering, run the check in
§10 and fix any orphans. Cite as "Supplementary Fig. S4" / "Supplementary Table S7".

The two SI cross-references that currently point at a folder are deleted outright (C5).

---

## 6. Global find / replace

Run these before the section rewrites so the compression work does not have to redo them.

| Find | Replace | Reason |
|---|---|---|
| `ZIP/ZCTA` | `ZCTA` | C8 |
| `model ladder` (referring to M1–M9) | `model series` | meeting decision |
| `eight-model ladder` | `model series` | meeting decision |
| `staged model ladder` | `model series` | meeting decision |
| `increasingly rigorous` / `increasingly demanding` | rephrase — the M-series is not nested | `REGRESSION_ROBUSTNESS_PLAN.md` §1 |
| `at household outlets` | delete | B1 |
| `the refreshed aggregate charger baseline` | `the aggregate charger baseline` | C6 |
| `much weaker than before` | state the value; delete the comparison | C6 |
| `The regenerated deterministic LOWESS audit` | `The LOWESS fits` | C6 |
| `source files used in the repo` | `the assembled source files` | C6 |
| `A significant remainder does not.` | `A substantial share of the gap does not.` | C8 |
| `rules out an income-based reading` | `is hard to square with an income-based reading` | S11 |

Two passages need rewriting rather than replacing:

**PG&E (Methods, demand proxy):** delete *"After correcting a parsing fault that had
silently zeroed roughly 85 percent of PG&E consumption records…"* Replace with a neutral
coverage statement: the demand proxy is available for 1,196 of the 1,390 analysis ZCTAs,
1,159 of which report positive consumption; remaining gaps fall largely outside the three
investor-owned utility territories that publish ZIP-level usage.

**Models 2C/2D (Methods):** delete *"The implementation fails rather than silently
simplifying Models 2C or 2D when a required housing variable is absent or constant."*
This is code behavior, not method.

---

## 7. Cross-reference repair

The Methods subsection numbering is off by one throughout. Most of this evaporates when
section numbers are removed (§3.3), but **verify each one** — several will become named
references and a few will become SI references.

| Location | Current | Correct (pre-restructure) | Post-restructure |
|---|---|---|---|
| Results intro; Empirical Approach | Section 6.6 (baseline equation) | 6.7 | "see Methods" |
| Results intro; Empirical Approach | Section 6.7 (model ladder) | 6.8 | "see Methods" |
| §4.2 education | Section 6.7.2 | 6.8.2 | "see Methods" |
| §4.2 county-clustered | Section 6.7.5 | 6.8.5 | "see Methods" |
| §4.5 Model 9A | Section 6.7.9 | 6.8.9 | "see Methods" |
| Appendix diagnostics | Section 6.9 | 6.10 | "see Methods" |
| §6.11 limitations | Section 6.8 | 6.11 | "see Limitations" |
| §6.11 charger ZIPs | Section 6.2 | 6.3 | "see Methods" |

Also: delete the §2.2 roadmap sentence *"Section 7 states the limitations and Section 8
concludes"* — it was already wrong and Nature format has no use for it (C2).

**Equation numbering:** Vineet's existing docx comment asks for equation cross-references
to be fixed. Convert all `Equation (n)` references to Word cross-reference fields. Most
equations move to Methods or SI in the restructure; renumber after §5 settles.

---

## 8. References

| ID | Fix |
|---|---|
| **R1** | `[9]` and `[20]` are the identical Light, McIntosh & Stephenson (2022) entry. Merge and renumber. |
| **R2** | `[3]`: text says "Kurdgelashvili, Kwon, and Larsen (2019)"; entry says "L. Kurdgelashvili, C. H. Shih, F. Yang, and M. Garg." Resolve against the actual paper. |
| **R3** | The Background paragraph names six sources (Stokes & Warshaw, Borenstein & Bushnell, Gridworks 2022, SEIA/Vote Solar, CPUC roadmap, "socio-technical planning papers") against four citation numbers `[18]`–`[21]`. Gridworks and the CPUC roadmap have no entry. "Flexible-DER coordination work at NREL and related DOE planning studies" is uncited. **Given the 750-word Introduction budget, cut this paragraph to the three sources that do real work rather than adding entries.** |
| **R4** | Reference-manager debris — retype by hand from the source documents: `[7]` title runs into cover text ("…SEPTEMBER 2020 How High Are Household Energy Burdens?"); `[14]` ends "…Acknowledgements Disclaimer"; `[16]` "Distributed Energy Resource Interconnection Roadmap." has no author, year, publisher, or URL; `[21]` uses a full-caps CPUC filing header as a title. |
| **R5** | Renumber by first appearance once the section order is final. `[25]` (Conley) currently precedes the data sources `[26]`–`[36]` but is first cited later. |

Nature Sustainability uses its own reference style — convert from IEEE numeric-bracket to
the Nature superscript format at the end, after renumbering.

---

## 9. Front and back matter

First pass only (decision J2) — Vineet finalises authorship, funding, and the cover letter.

### 9.1 Add
- Author list, affiliations, corresponding author and email
- **Data availability:** the harmonized ZCTA analysis file. **The Methods currently say
  the Zenodo record "will be deposited" — deposit it and cite the DOI before submission.**
  `scripts/make_zenodo_bundle.py` exists for this. A future-tense data statement is a
  common desk-stage query, and the dataset is one of the paper's three stated contributions.
- **Code availability:** https://github.com/vineetjnair9/distributed-energy-resources-equity-CA, MIT
- Author contributions (CRediT-style prose)
- Competing interests
- Acknowledgements / funding

### 9.2 Not required by Nature
Keywords and Highlights are Elsevier requirements — skip unless the target changes.

### 9.3 Clear the 13 open docx comments

Already satisfied by the current text — verify then delete:
- Conley citation (now ref. 25)
- DER data source citations (now refs. 26–36)
- Non-stacked model criticism pre-empted — **now fully answered by the new §4.4**

Still outstanding — action then delete:
- Table conditional formatting → handled when Tables 1 and 2 are rebuilt (§5.1)
- Asian % on all model-series plots → verify `regenerate_standardized_figures.py` includes
  `pct_asian` in every panel
- Equation cross-references → §7
- Appendix cross-referencing → §5.3
- Figure background/crop consistency → meeting note; fix during §5.1
- "I'll draft a cover letter for Nature Sust editor" → Danielle, after the final version

**Delete every comment before submission** — comments survive into the PDF on most
submission systems.

---

## 10. Verification checklist

Run before delivering. Script what can be scripted.

- [ ] Main text ≤3,500 words excluding abstract, Methods, references, figure legends
- [ ] Abstract ≤150 words, no citations
- [ ] Title ≤10 words and ≤90 characters
- [ ] Exactly 6 main-text display items
- [ ] References ≤50, no duplicates, every in-text number resolves, Nature style
- [ ] Every SI figure and table cited at least once in main text (§5.3)
- [ ] Every main-text figure and table cited at least once, in order of first appearance
- [ ] No "Section X.Y" strings remain
- [ ] No "ladder" applied to the M-series; no "ZIP/ZCTA"; none of the §6 phrases
- [ ] Every table reports N (and cluster count where clustered)
- [ ] Every coefficient in main text is standardized and labelled as such
- [ ] Every quoted number traces to a file in `outputs/`
- [ ] Abstract's claims match the C5 table — no "disparities survive" without the
      per-technology qualifier
- [ ] Zero comments remain in the docx
- [ ] Zenodo DOI present and resolving; data and code availability statements in past tense
- [ ] `git diff` on `site/index.docx` committed on the branch

### Scriptable checks

Reuse the extraction from the audit:

```python
# unzip index.docx; parse word/document.xml
# 1. word counts by Heading1 section
# 2. set(figure captions) vs set(figure references)  -> orphans both ways
# 3. same for tables and supplementary items
# 4. re.findall(r'Section \d+(?:\.\d+)*')            -> must be empty
# 5. citation numbers in body vs reference list      -> must match exactly
# 6. banned-phrase scan from §6
```

---

## Appendix — key numbers, for reference while writing

**Sample.** 1,390 ZCTAs in the published analysis; C1–C5 frozen common sample N = 1,160
(1,150 for the two affordability outcomes), 42 county clusters, identical at every rung.
Demand proxy available for 1,196 ZCTAs, 1,159 positive.

**Zero shares (pop ≥ 1,000, N = 1,422).** PV 5.3% · storage 6.6% · chargers 19.0% ·
**Level 1 97.8%** · Level 2 22.3% · DC fast 44.2% · **wind 97.5%**.

**Charger inventory.** `access_type` = Public for 100% of 18,453 station rows. Statewide
ports: 256 Level 1, 40,078 Level 2, 13,852 DC fast.

**Storage sector** (`EnergyStorage_Cleaned_August2024_ada.xlsx`): 4,957 Residential,
41 Commercial, 2 Utility. *Confirm this is the file feeding the aggregation.*

**Affordability gap.** Per-capita median $75, max $236,464. Top 100 ZCTAs = 92.3% of the
statewide gap; 134 ZCTAs exceed $1,000 per capita.

**Housing attenuation (the abstract's headline qualifier).** Standardized, baseline → M2D:
PV % Black −0.049 → −0.023 (53%) · PV % Asian −0.082 → −0.051 (38%) ·
storage % Black −0.106 → −0.059 (44%) · storage % Asian −0.252 → −0.171 (32%).

**R² path.** PV 0.109 (C1) → 0.492 (C5) → 0.658 (O). Storage 0.238 → 0.422 → 0.452.
Chargers 0.071 → 0.268 → 0.296.

**VIF.** Max focal-term VIF anywhere in C1–O is 8.15 (log income). Zero focal terms above
10. Confirms the meeting's read that collinearity is not a problem. The only VIF issue is
Model O's two wind controls (≈12.2 against each other), which do not touch the focal terms.

**Conley HAC.** SEs rise up to 3× versus HC1, plateauing between 100 and 200 km. Asian-share
PV and storage significant at 0.1% at every cutoff. Black-share significant at 5% but less
precise than HC1 implies. Aggregate-charging poverty coefficient survives at 1%.
Asian-share charging: significant at 50 km and 200 km, **not** at 100 km (S12).
