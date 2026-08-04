# Review Memo — *The Unequal Energy Transition* (index.docx)

Reviewed 29 July 2026 against the file saved at 14:36. Manuscript: ~68,400 characters of body text, 273 content blocks, 6 tables, 13 captioned figures across 20 image blocks, 43 embedded images, 90 OMML equations, **24 Mendeley citations with a complete IEEE-numeric bibliography**, 8 open Word comments.

> **Correction notice (v2).** The first version of this memo claimed the reference list was empty and that §5.5 lacked its robustness figures. **Both claims were wrong.** My extraction used a library that does not descend into Word `<w:sdt>` content-control elements, which is exactly where Mendeley stores citation markers and the bibliography — so 24 citations and a 24-entry reference list were invisible to me, and I misread the resulting blank spaces as deleted citations. I also under-counted figures because I keyed off captions rather than image blocks. Corrected findings below; superseded items are struck and explained rather than deleted, so you can see what changed.

> **Reconciliation notice (v3), 3 August 2026.** A separate code- and data-level audit
> (`AUDIT.md`) has since been run against the repository, and several items below are now
> resolved, answered, or superseded. Items are annotated in place — **RESOLVED**, **DONE**,
> **UPDATED** — rather than deleted, so the original reasoning stays visible. Every numeric
> claim in this memo was re-checked against the regenerated tables and still holds exactly
> (−0.583, −1.784, +0.413 for §2.2; −0.611 at p = 0.0093 for §2.3; 0.607 for the §5.6
> LOWESS gradient). What changed is which concerns remain open, plus a set of findings the
> audit surfaced that this memo could not see from the manuscript alone — collected in the
> new Part 0 below.
>
> One correction to this memo's own reasoning: §2.1 assumed housing controls were absent
> from every specification. They were not absent — they were implemented as Model 2C and
> silently inert, because the underlying ACS columns were 100% empty and the notebook
> dropped all-NaN columns without comment. The exported table therefore looked like a
> robustness check that had been run and passed. That is a worse failure mode than
> omission, and it is why the audit exists.

---

## Part 0 — Findings from the code audit (not visible from the manuscript)

These come from `AUDIT.md` and were not detectable by reading the draft. Several bear
directly on results reported in the paper.

- **`y_wind_mw` is not a viable outcome.** It is 97.5% structural zeros in the analysis
  sample, and its cross-validated R² is **negative under every model tested** (linear
  −0.020, random forest −0.220, XGBoost −0.180) — worse than predicting the mean. An
  18-model OLS ladder on log1p of it is not defensible. A binary `any_turbines`
  specification has been restored as the honest alternative.
- **Wind is utility-scale, not distributed.** The 5 MW DER threshold applied to storage
  and small plants was never applied to wind; one ZIP carries 1,542 MW. Presenting it
  beside rooftop PV as a DER invites an obvious objection.
- **`y_level1_chargers` is 97.8% zeros.** Better used as a descriptive fact supporting
  the §2.7 charger-composition argument than as a modelled outcome.
- **The utility crosswalk contains only the three IOUs.** LADWP, SMUD and every POU are
  absent, so `Model 5` (utility FE) silently drops 100 ZIPs and `Model 8` (demand proxy)
  drops 53 of 84 LA-area ZIPs. 81 ZIPs are assigned a utility covering under 20% of
  their area; ZIP 90008 is labelled SCE on a 9.4% overlap. This needs stating in
  Methods at minimum.
- **Energy burden may be partly tautological.** It correlates −0.75 with log income and
  +0.73 with 1/income, and income alone explains R² = 0.556. If the source defines
  burden as energy cost ÷ income, regressing it on income puts the denominator on the
  right-hand side. The metrics are pulled from Tableau exports by positional column
  labels (`EB.2`, `EA.7`), so the definition is not recoverable from the code. Confirm
  with the provider before interpreting those coefficients.
- **Substantial nonlinearity.** Cross-validated R² for PV roughly doubles from linear
  (0.174) to XGBoost (0.355), and storage from 0.265 to 0.354. This does not invalidate
  the OLS ladder — it estimates interpretable conditional associations, not predictions
  — but the linear functional form is a choice worth defending explicitly.
- **Two robustness checks were not doing anything.** `Model 4` and `Model 4R` were
  byte-identical, and `Model 2C` was byte-identical to `Model 1`. Both are fixed; 4R is
  now a genuine restricted-controls test.

---

## Part 1 — Blockers (must fix before any submission)

### 1.1 ~~The reference list is empty~~ → Citation hygiene: duplicates and attribution mismatches

**Retracted:** the references are present and functional — 24 Mendeley-inserted numeric citations plus a complete IEEE-style bibliography, all living in content controls. The "stray space before a period" pattern I flagged was the space *preceding* an invisible-to-my-tooling `[4][5][6]` marker. It renders correctly in Word. Danielle's note #1 is largely done.

**What does still need attention, and it's much narrower:**

- **Entries 9 and 20 are the same paper** — Light, McIntosh & Stephenson, "Advancing Equity in Access to Distributed Energy Resources in California," *JSPG* — duplicated under two numbers. Merge in Mendeley and refresh the field.
- **Possible wrong-reference mismatch on the paper's key infrastructure claim.** §2.4 attributes socially-patterned hosting-capacity constraints to "Brockway et al. (2021)," but entry 11 is Brockway & Callaway (2022) on *community solar omission* — a different paper. The hosting-capacity result you want is Brockway, Conde & Callaway, *Nature Energy* 2021. Verify which one the marker actually points to; this claim carries real weight in §2.4 and §5.5.
- **Attribution mismatch in §2.5.** Text says "Clean Energy Group (2021) frames storage as an equity asset," but entry 17 is Tarekegne, O'Neil & Twitchell (PNNL). Same title, different authors — fix the in-text attribution.
- **Date mismatch:** Borenstein & Bushnell cited as 2016 in text, entry 19 dated 2015.
- **Incomplete metadata** on entries 8, 13, and 16 — no author or year ("Demystifying Equity in California's Energy Grid Transition"; "Distributed Energy Resources Technical Considerations for the Bulk Power System"; "Distributed Energy Resource Interconnection Roadmap"). Fill these in Mendeley before submission.
- **Genuinely uncited claims remain in §2.5:** "Flexible-DER coordination work at NREL," "Gridworks (2022)," "CPUC roadmap documents," and "SEIA/Vote Solar community-solar critiques" have no corresponding bibliography entries (entry 21 is the SEIA CPUC brief and may cover the last one). Either cite or cut — that sentence currently stacks six unsupported attributions.
- **Convert the bibliography to the target journal's style at the end.** IEEE numeric suits *Applied Energy*; ERSS and *Energy Policy* want author–date, *Nature Sustainability* wants its own numeric style. One Mendeley style switch, but do it last.

### 1.2 Section numbering is broken in three places
| Location | Current | Should be |
|---|---|---|
| §3.1 "Unit of analysis" | styled **Heading 1** | Heading 2 (it's a subsection of §3) |
| §4 Results subsections | numbered **5.1–5.9** | 4.1–4.9 |
| Discussion | numbered **"5. Discussion"** with §5.1–5.5 | 5 → 6, and its subsections collide with the Results subsections above |
| Methods | "6. Methods" | consistent renumber after Discussion |

Right now §5.1 appears twice with different content ("Baseline patterns across DER types" and "What persists and what changes"). Any reviewer will notice this in the first thirty seconds. The in-text pointer "Section 6.7" for the model ladder is also correct only under the current broken scheme.

### 1.3 Sample size contradiction between Table 2 and Table 6
- **Table 2** (summary statistics): N = **1,386** for every outcome.
- **Table 6** (cluster profiles): cluster sizes 1,218 + 279 + 323 + 488 + 252 = **2,560 ZIPs**.

**RESOLVED — it was the first branch, and worse than a caption fix.** The clustering ran
on the full unfiltered 2,552-row file with `SimpleImputer(strategy='median')`, applying
neither the ≥1,000 population filter nor the ACS-completeness filter. The largest reported
cluster (1,142 ZIPs, 45% of the sample) was **69% ZIPs with no ACS data at all** — median
imputation pushed them to the centroid of every predictor and k-means grouped them. Table 6
was reporting a missing-data artifact as a socio-technical typology. The clustering now runs
on the same N = 1,386 analysis sample as the regressions, so Tables 2 and 6 agree.

Related: §3.1 and §6.2 both promise the ≥1,000-population filter, but the paper never reports how many California ZCTAs exist (~1,760 ZCTAs statewide), how many survive each filter, or what the attrition implies. **Add a sample-construction flow (raw → merged → filtered → analysis) as a table or CONSORT-style figure.** Figure 1's caption currently hand-waves this as "Blank areas indicate missing or excluded observations," which is not enough.

### 1.4 §5.7 text does not match Table 6
The text describes **three** clusters labeled **0, 1, 2**:
> "cluster 1 is affluent with a large Asian share... cluster 2 has the highest Hispanic and combined non-white shares... cluster 0 combines comparatively strong PV, storage, and charging"

Table 6 has **five** clusters labeled Blue(1) through Purple(5). The prose is from an
earlier k=3 run.

**UPDATED — still required, and the target has moved.** After the clustering was corrected
(§1.3), the grid search selected **k = 4**, and after housing tenure was added to the feature
set it selected **k = 6**. The count has now moved three times (5 → 4 → 6) purely as the
control set changed. Nothing is wrong with the procedure, but a partition this sensitive
should not carry interpretive weight: present the clusters as descriptive texture, state
plainly that *k* is sensitive to the feature set, and avoid any claim that depends on a
specific *k*. Rewrite §5.7 against the current solution and drop the colour names.

### 1.5 Leftover internal to-do list at the top of the document
Paragraphs 2–11 are your and Danielle's working notes, sitting between the title and the abstract. Obvious, but easy to forget. Note that several are still open: expand prior work + citations, update figure, add model numbers, add energy-burden DER results, improve contributions, formalize methods prose, expand discussion, improve intro/conclusion, add cross-references.

---

## Part 2 — Substantive issues a referee will raise

### 2.1 The central identification objection: housing tenure
This is the reviewer comment I would bet on. The paper's headline is that race survives income controls. The most obvious omitted variable — **homeownership rate / renter share / single-family vs. multifamily housing structure** — is not in any specification. You cannot install rooftop PV or a home battery on a unit you don't own or a roof you don't control, and tenure is strongly correlated with race in California independent of income. You acknowledge this in §6.10 and §7 as a limitation, but that is not going to be enough at a high-impact venue.

**DONE — and the race coefficients survive.** Both B25024 (units in structure) and B25003
(tenure) are now pulled and entered, as Model 2C (structure) and Model 2D (structure +
tenure), kept separate so the incremental contribution of tenure is visible.

| Outcome | Term | M1 | 2C | 2D |
|---|---|---|---|---|
| Solar PV | % Black | −0.049\*\*\* | −0.024\*\*\* | −0.024\*\*\* |
| Solar PV | % Asian | −0.082\*\*\* | −0.050\*\*\* | −0.051\*\*\* |
| Storage | % Black | −0.106\*\*\* | −0.054\*\* | −0.057\*\* |
| Storage | % Asian | −0.252\*\*\* | −0.175\*\*\* | −0.171\*\*\* |

Race coefficients attenuate 30–50% when structure enters and then **move less than 5%**
when tenure is added — structure had already absorbed the shared variance (owner share
correlates +0.79 with single-family share). The paper's headline holds under the fuller
specification, which is the good outcome this memo hoped for.

**The unexpected payoff is a decomposition.** PV and storage turn out to be limited by
*different* barriers (Model 2D coefficients):

| Outcome | multifamily | owner-occupied |
|---|---|---|
| Solar PV | −0.142\*\*\* | −0.047 (n.s.) |
| Storage | −0.203\*\*\* | +0.204\*\* |
| EV Chargers | +0.208\*\*\* | −0.138\* |

PV is gated by **structure** — ownership is null, and the multifamily effect *strengthens*
once tenure is held constant. Storage is gated by **ownership** — the multifamily effect
halves and owner share enters at +0.204\*\*. That supports a policy claim the draft does not
currently make: third-party ownership and financing reforms address the storage barrier but
do nothing for a household with no roof, and community solar is the reverse. Two barriers,
two interventions. Figure: `outputs/standardized_figures/housing_structure_across_outcomes.png`.

**One framing caution.** Housing composition is plausibly a *mediator* of the race effect,
not a confounder — if segregation shapes who lives in multifamily housing, these variables
lie on the causal path. Model 1 gives the **total** disparity and 2C/2D the **direct**
disparity net of housing. The attenuation locates a mechanism; it does not show the
disparity is smaller than it looked. Report both and name them.

### 2.2 The Asian-share coefficient is the paper's weakest link
`pct_asian` is negative and large for PV (−0.583) and storage (−1.784) but **positive** for chargers (+0.413). The paper reports this but never interprets it. It sits awkwardly with the framing, since Asian-share ZCTAs in Table 6 are the highest-income cluster ($159.6k, 7.8% poverty) — yet show the *lowest* PV per capita (0.52/1k).

**RESOLVED — this memo's hypothesis was right, and it is now demonstrated.** The suspicion
that the positive charger coefficient reflected housing density is confirmed: once
multifamily share is controlled, `pct_asian` on chargers collapses from **+0.058\*\* to
−0.007 (n.s.)** in the standardized specification, while multifamily share itself enters at
**+0.310\*\*\***. The anomaly was a housing-composition artifact throughout.

This converts the paper's weakest link into support for the §2.7 argument: aggregate charger
counts track apartment and commercial density rather than usable residential access, which is
precisely why they mislead as an equity metric. Interpret it directly rather than folding it
into a general race narrative.

### 2.3 Model 9 has a sign you don't discuss
In Table 4 (Storage Model 9), `pct_bachelors_plus` is **−0.611 (p = 0.009)** — bachelor's attainment *negatively* associated with storage, conditional on income and PV. That's counterintuitive and unremarked. Meanwhile §5.6 reports a *positive* education LOWESS gradient for storage (+0.61) and a positive education coefficient for chargers. The sign flip between unconditional and conditional is a collinearity story worth one sentence — leave it silent and a referee will read it as instability.

### 2.4 Multicollinearity is waved off
§6.9 says "Some richer specifications show elevated VIF values" and then declines to treat that as disqualifying. That's a defensible position, but you need to **report the actual VIFs in an appendix table**, not describe them qualitatively. `log_median_household_income`, `poverty_rate`, `pct_bachelors_plus`, and `log_median_housing_value` are heavily overlapping constructs.

**UPDATED — the tables exist, and one specification was genuinely broken.** A VIF table is
already exported next to every model (`{outcome} | {model} VIF.csv`), so the appendix table
is a copy-paste job. More importantly, the audit found that the first working version of
Model 2C had VIFs of **1258 / 1077 / 199**: the three housing shares sum to 1 by
construction, so entering all three alongside an intercept was a compositional
dummy-variable trap and the coefficients were uninterpretable. Single-family is now the
omitted reference and **max VIF is 3.42 (2C) and 5.29–5.42 (2D)**. The general point stands
for the income/poverty/education/housing-value cluster, but the specific numbers are now
defensible and worth reporting rather than describing.

### 2.5 No spatial error correction
County-clustered SEs are a reasonable robustness check, but ZCTA-level DER deployment is spatially autocorrelated at a finer scale than counties (installer service territories, permitting jurisdictions, neighborhood peer effects). At a top venue expect a request for **Moran's I on the residuals**, and possibly a spatial lag or SAR/SEM specification, or Conley spatial HAC standard errors. Adding Moran's I is cheap and preempts the comment.

### 2.6 The "no APC / no causal claim" tension
The paper is repeatedly and commendably honest that this is descriptive and ecological. That honesty caps the ceiling — it is why *Nature Energy*/*Joule* are long shots (see Part 3). Two things would materially raise it without requiring a natural experiment:
- **A temporal dimension.** Tracking the Sun has install dates going back years. Even a simple two-period comparison ("did the gap widen or narrow after NEM 3.0 / SGIP equity budget?") converts this from a snapshot into a trajectory and roughly doubles the policy value.
- **A benefit-quantification step.** Translate the storage gap into forgone resilience hours or the PV gap into forgone annual bill savings. Descriptive papers with a quantified stake travel much further than coefficient tables.

Neither is required to publish. Both change which tier is realistic.

### 2.7 EV charging: the strongest finding is under-sold
§5.4/§5.8 — that aggregate charger counts are composition artifacts driven by Level 2 siting, and that poverty correlates *positively* with a metric that doesn't represent usable residential access — is the most novel and most policy-relevant result in the paper. It is currently the *fourth* thing mentioned in the abstract, in a subordinate clause. **Promote it.** "Aggregate charger counts are a misleading equity metric" is a headline; "race remains significant after controls" replicates Sunter et al. (2019) in a new technology.

### 2.8 ~~Energy-burden section is orphaned~~ → §5.5's figures exist but are invisible to the reader

**Corrected:** §5.5 contains **8 figures across three blocks** — a 6-panel composite plus two singles — which is the energy-burden DER result and coefficient robustness ladder Danielle asked for. The analysis is done. I missed it because none of the three blocks carries a caption, and my first pass counted figures by caption.

**The problem is presentation, not missing work.** As it stands:

- None of the three image blocks has a caption, so they have no figure numbers.
- Because they have no numbers, no body text refers to them. Eight figures sit between §5.5's prose and §5.6 with nothing telling the reader what they show or why they matter.
- Your own comments already flag this — "Missing figure caption," "Also missing figure caption," and "Put as one figure and add caption" (the 6-panel block).

Fix: merge the 6-panel block into one figure, caption all three, renumber the downstream figures (current Figures 10–13 shift to 13–16), and add two or three sentences in §5.5 walking the reader through them. That converts the weakest-looking section into a substantive one at low cost.

### 2.9 Seven image blocks have no captions at all
Beyond §5.5's three, the appendix has four uncaptioned image blocks (§Appendix: storage model comparison, EV charging comparison, baseline spatial maps, wind comparison). The surrounding prose describes them but no numbered captions exist, and your 12 May comment — "Ensure that we cross reference to these appendices in the main text as well" — is still open. Journals desk-check for uncaptioned and uncited display items.

### 2.10 Your own open comments
Eight unresolved comments in the file, six from today. Two are substantive and worth resolving before anyone else reads the draft:

- **"I'm not sure about this section's content"** — on §5.5. Given that the figures are there and the results are reported, my read is that the section is worth keeping and building out rather than cutting; see §2.8. It's the only place the paper connects DER access to affordability, which is what makes the storage argument land.
- **"Add the maps for storage & charging here too for completeness"** (14:06) — agreed, and it also fixes the Figure 1 gap where only PV has a representative spatial map in the appendix.

The remaining four are figure-rendering issues: Hispanic and poverty-rate colors too similar, missing colors in a plot, and the two caption notes. The color-similarity one matters more than it sounds — poverty rate and Hispanic share are the two predictors whose *divergence* carries the EV-charging argument, so a reader who can't distinguish them can't follow §5.4.

---

## Part 3 — Presentation and mechanics

- **Figure 5 and Figure 13 are never cited in the body text**; **Table 4 is never cited by number** (§5.3 says "the Model 9 table"). Journals reject at desk-check for uncited display items. This ties into your own open note about cross-references — do it last, but do it.
- **Sentence-initial "we" is now lowercase in four places.** The 14:36 save ran a `We ` → `we ` find-and-replace, which fixed the mid-sentence capitalization I originally flagged but broke sentence starts: "**we** test whether the income gradient..." (§6.7 Race-by-Income), "**we** estimate specifications with utility territory fixed effects... **we** also estimate county-clustered..." (§6.7 Utility FE), "**we** add measures of existing energy infrastructure..." (§6.7 Model 7). Fix these four by hand rather than with another global replace.
- **"the meaning of those disparities' changes by technology"** (§5.1 of Discussion) — stray apostrophe.
- **§1.2 ends with "The rest of the paper is structured as follow."** — incomplete sentence and a missing roadmap paragraph. This is where you tell the reader the unusual Results-before-Methods ordering is deliberate.
- **Results-before-Methods ordering.** Fine for *Nature Energy*/*Joule*/*PNAS*-style formats, wrong for *Energy Policy*, *ERSS*, and *Applied Energy*, which expect Methods → Results. Decide the target venue before you finalize structure, not after.
- **Abstract is ~290 words** and heavily front-loaded with motivation. *Energy Policy* caps at 100 words for the highlights-style summary plus a longer abstract; *ERSS* wants ≤ 250. Trim, and get a number into it — right now the abstract contains zero quantitative results.
- **Table 1** is placed under the §3 heading before §3.1 introduces the unit of analysis; it should follow §3.4 where the controls are actually defined.
- **`y_chargers` with a trailing space** inside Figure 8's caption.
- Consider adding **"California" and "distributed energy resources" to the title**'s keyword load — the current title is good but "Across California" buries the case selection.

---

## Part 4 — Journal shortlist

Constraint applied: **no APC**. Every venue below is hybrid or subscription, meaning the traditional publishing route costs you nothing. This rules out several otherwise-natural homes — *Environmental Research Letters* (fully OA, ~$2,300), *Nature Communications*, *iScience*, *npj Climate Action*, and *PNAS* (charges $2,575 even on the delayed-OA route).

### Tier A — best fit, realistic, submit here

**1. Energy Research & Social Science (Elsevier, IF 7.2)** — *my top recommendation.*
The natural home. ERSS is the flagship for exactly this genre: quantitative energy-justice work that is explicitly descriptive, socially framed, and policy-directed. It publishes race-and-energy papers routinely, will not demand causal identification, and actively welcomes the "race-neutral planning is insufficient" argument. Hybrid — subscription route free. Requires Methods before Results and a ≤250-word abstract. Realistic acceptance with the Part 1 fixes plus tenure controls.

**2. Energy Policy (Elsevier, IF 9.3)**
Higher IF, broader policy readership, strong fit for §5.5's stakeholder-specific recommendations (lawmakers / grid operators / utilities), which is the most *Energy Policy*-shaped part of the manuscript. Slightly less receptive to race-centered framing than ERSS and more focused on the instrument design than the disparity measurement. Hybrid, no APC. If you want maximum IF per unit of realistic risk, this is it.

### Tier B — reach, but genuinely in play

**3. Environmental Science & Technology (ACS, IF ~11.3)**
ES&T has published environmental-justice and energy-equity spatial analyses, and its "Policy Analysis" article type is a real fit. Hybrid — the subscription route carries no author charge. Higher methodological bar: expect the tenure control (§2.1), the spatial autocorrelation check (§2.5), and the VIF table (§2.4) to be non-negotiable. Word limits are tight, so the paper would need to compress substantially and push the model ladder to SI.

**4. Applied Energy (Elsevier, IF 12.2)**
Highest IF in the realistic set, but the **weakest scope fit** — Applied Energy skews toward modeling, systems engineering, and techno-economics, and reviewers there often bounce purely social-science regressions as out of scope. Note also that Applied Energy's OA route runs ~$4,140; the subscription route is free, but you should verify at submission. I'd rank this fourth despite the IF.

**5. Nature Sustainability (Springer Nature, IF 32.1, hybrid — subscription route free)**
A better fit than *Nature Energy*, and the highest-ceiling venue where the gap is rhetorical rather than empirical. Its scope explicitly spans policy, poverty, cities and urbanisation, and environmental behaviour alongside the natural-science material, so it takes social science on its own terms — where *Nature Energy* would push toward energy-systems depth this paper doesn't have. Acceptance runs ~8–12% and most attrition is **desk rejection for insufficient generality**: "California ZCTAs in 2023" reads as a case study.

The reframing that clears that bar already exists in §5.4. The charger-composition result is a **measurement critique** — aggregate charger counts correlate positively with poverty while usable residential access does not, because Level 2 siting tracks commercial corridors. Every jurisdiction running EV equity programs uses charger counts as its metric. That claim generalizes without additional data, in a way "race is significant in California" does not, and it recasts California as the proving ground rather than the subject. The multi-DER comparison then becomes evidence that the mismeasurement is technology-specific rather than a one-off.

**Send a presubmission inquiry before committing to a full submission** (see `nature_sustainability_inquiry.md`). Free, one to two weeks, and the editor will say plainly whether the framing clears the bar. Frame it around the measurement critique, not the race-after-income finding.

**6. Nature Cities (Springer Nature, hybrid — subscription route free)**
Newer and hungrier for urban-spatial-equity work; the ZCTA framing fits its remit and the generality bar is lower than *Nature Sustainability*'s. Reasonable second inquiry if Nature Sustainability declines.

### Tier C — long shots; only worth it with a substantially strengthened paper

**7. Nature Energy** (hybrid, subscription route confirmed free) and **8. Joule** (Cell Press, IF 35.4, hybrid).
Both would need this to stop being a cross-sectional descriptive snapshot. *Nature Energy* has published DER-equity work, but at the level of a national panel with a policy discontinuity, not a single-state 2023 cross-section replicating a known solar finding in two new technologies. If you add the temporal dimension **and** the benefit quantification **and** either expand beyond California or exploit a California policy change (NEM 3.0, SGIP equity budget), a presubmission inquiry to *Nature Energy* becomes defensible. Not before.

### Recommended sequence
**Send the Nature Sustainability presubmission inquiry now** — it costs nothing, runs in parallel with the Part 1 cleanup, and resolves the biggest open question about where this lands. While it's out, do the Part 1 fixes and add tenure controls (§2.1), which every venue on this list will require anyway.

- **If Nature Sustainability bites:** reframe around the measurement critique, add the temporal dimension (§2.6) if the editor signals it's needed, and submit there.
- **If not:** ERSS or Energy Policy, essentially as-is once Part 1 and §2.1 are done. The draft's honest descriptive framing is a genuinely good match for Tier A, and a clean Tier A acceptance beats a bruising Tier C rejection cycle.

Either way the cleanup work is identical, so the inquiry is free optionality.

---

## Suggested order of work

**Revised 3 August 2026 after the code audit.** Items 3 and 5 of the original list are
done; the analytical work that remained is now largely writing. Original list preserved
below for the record.

1. **Write up the structure/tenure decomposition (§2.1).** This is the strongest new
   result, it is already computed, and it gives the paper a policy claim it currently
   lacks. Highest scientific value remaining.
2. **Reinterpret the Asian-share result (§2.2)** as a housing-composition artifact and
   fold it into the charger-composition argument (§2.7) rather than the race narrative.
3. Strip internal notes; fix section numbering (§1.2, §1.5) — half a day
4. Caption §5.5's three image blocks and the four appendix blocks; renumber figures; add
   pointer sentences (§2.8, §2.9) — still the best perceived-quality-per-hour item
5. **Rewrite §5.7 against the current cluster solution (§1.4)** and state that *k* is
   sensitive to the control set. Table 2 vs Table 6 now agree at N = 1,386.
6. **Address the Part 0 items that touch reported results** — decide whether `y_wind_mw`
   and `y_level1_chargers` stay, and state the POU/LADWP coverage gap in Methods.
7. Clean citation duplicates and attribution mismatches — especially Brockway 2021 vs
   2022 (§1.1)
8. Add Moran's I (§2.5); the VIF appendix table (§2.4) is now a copy-paste from the
   exported `* VIF.csv` files
9. Reframe abstract and contributions to lead with the charger-composition finding (§2.7)
10. Resolve the four figure-rendering comments, starting with the Hispanic/poverty colour
    collision (§2.10)
11. Choose the venue, convert bibliography style, restructure Methods/Results to its
    convention, then add all cross-references last (§1.1, §3)

<details>
<summary>Original order (29 July 2026)</summary>

1. Strip internal notes; fix section numbering (§1.2, §1.5) — half a day
2. Caption §5.5's three image blocks and the four appendix blocks; renumber figures; add pointer sentences (§2.8, §2.9) — highest ratio of perceived quality to effort in this list
3. Reconcile Table 2 vs. Table 6 sample sizes; rewrite §5.7 against the current cluster table (§1.3, §1.4)
4. Clean citation duplicates and attribution mismatches — especially the Brockway 2021 vs. 2022 question (§1.1)
5. Add tenure + housing-structure controls to the ladder; rerun (§2.1) — highest scientific value
6. Add Moran's I and a VIF appendix table (§2.4, §2.5)
7. Reframe abstract and contributions to lead with the charger-composition finding (§2.7)
8. Resolve the four figure-rendering comments, starting with the Hispanic/poverty color collision (§2.10)
9. Choose the venue, convert bibliography style, restructure Methods/Results to its convention, then add all cross-references last (§1.1, §3)

</details>

---

## Sources

- [Energy Research & Social Science — open access options, Elsevier](https://www.sciencedirect.com/journal/energy-research-and-social-science/publish/open-access-options)
- [Energy Research & Social Science impact factor 2026](https://journalsearches.com/journal.php?title=energy+research+and+social+science)
- [Energy Policy — journal home, Elsevier](https://www.sciencedirect.com/journal/energy-policy)
- [Energy Policy Impact Factor 2026](https://www.journalmetrics.org/journal/energy-policy)
- [Nature Energy — our publishing models](https://www.nature.com/nenergy/our-publishing-models)
- [Article Processing Charges — Nature Support](https://support.nature.com/en/support/solutions/articles/6000211135-article-processing-charges)
- [Joule — publishing options, Cell Press](https://www.cell.com/joule/information-for-authors/publishing-options)
- [Environmental Science & Technology — ACS Publications](https://pubs.acs.org/journal/esthag)
- [ACS Open Science — OA pricing](https://acsopenscience.org/researchers/oa-pricing/)
- [Applied Energy Impact Factor 2026](https://www.journalmetrics.org/journal/applied-energy)
- [PNAS publication charges](https://www.pnas.org/author-center/publication-charges)
- [Nature Sustainability — aims & scope](https://www.nature.com/natsustain/aims)
- [Nature Sustainability Impact Factor 2026](https://www.journalmetrics.org/journal/nature-sustainability)
- [Nature Sustainability — acceptance rate](https://academic-accelerator.com/Acceptance-Rate/Nature-Sustainability)
