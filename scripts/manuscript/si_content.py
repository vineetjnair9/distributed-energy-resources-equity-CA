# -*- coding: utf-8 -*-
"""Supplementary Information text.

Structured as numbered Notes, each written to be read as prose with its figures and
tables rather than as a caption list. Much of this is the original appendix and Results
text from the draft, restored and lightly edited: variable names replaced with their
prose names, cross-references renumbered, and development-log phrasing removed.

Item numbering is shared with the main text. ``build_manuscript.py`` writes the main
text's references; anything renumbered here must be renumbered there too.
"""

INTRO = (
    "This Supplementary Information reports the material that does not fit within the "
    "main text's display-item limit, together with the robustness analyses the main text "
    "summarises. It is organised as thirteen Notes. Notes S1 to S5 document the "
    "specifications and the robustness evidence behind the main results. Notes S6 to S10 "
    "carry the descriptive and secondary analyses. Notes S11 to S13 report predictive "
    "model comparisons, statistical diagnostics, and the data-construction decisions that "
    "govern how the outcomes should be read. Every item here is cited at least once in "
    "the main text."
)

NOTES = [

# ---------------------------------------------------------------- S1
("Supplementary Note S1 | The model series", [
 "The main results are estimated as a model series: each specification varies exactly one "
 "control block against a fixed core of log median household income, Black, Hispanic and "
 "Asian population shares, poverty rate, and the resource control appropriate to the "
 "outcome. The specifications are siblings rather than nested rungs — some substitute a "
 "control rather than adding one — so the series answers which single block moves which "
 "coefficient. It does not, on its own, establish whether the blocks jointly absorb an "
 "effect; that is what the cumulative ladder in Note S2 is for.",

 "Model 1 is the baseline: income, race and ethnicity shares, poverty rate, and a limited "
 "set of climate controls. It provides a first-pass estimate of area-level disparities "
 "after accounting for basic socioeconomic status and broad geographic conditions.",

 "Model 2 has four variants. Models 2A and 2B add bachelor's attainment and median housing "
 "value respectively. Model 2C adds exhaustive housing structure composition — "
 "multifamily, mobile-home and boat/RV/van/other shares, with single-family units omitted "
 "as the reference. Model 2D further adds owner occupancy, with renters as the omitted "
 "tenure reference. Because the four ACS B25024 structure shares sum to one, omitting "
 "single-family makes every reported structure coefficient an interpretable contrast with "
 "a true single-family base; tenure is kept as its own block so Model 2D shows what tenure "
 "adds beyond building type.",

 "Model 3 tests whether the results depend on how geographic context is captured. For "
 "solar we substitute global horizontal irradiance alone (Model 3C); elsewhere we compare "
 "heating and cooling degree days (Model 3A) against mean temperature alone (Model 3B). "
 "For wind outcomes we use wind resource measures. Because Model 3 substitutes rather than "
 "adds, it is a sensitivity check on the resource control and not a more demanding "
 "specification.",

 "Model 4 tests whether the income gradient differs across communities by adding "
 "interactions between income and race and ethnicity shares. These are mean-centred before "
 "interaction so the main effects stay interpretable; a reduced variant, Model 4R, omits "
 "the poverty control to confirm the interaction is not absorbing it.",

 "Model 5 adds utility territory fixed effects to absorb institutional differences across "
 "service areas — rates, interconnection processes, incentive administration and "
 "historical investment all differ by territory. Model 5C re-estimates the baseline with "
 "county-clustered standard errors as a robustness check on inference rather than on the "
 "conditional mean.",

 "Model 6 introduces broader geographic controls: latitude and longitude (Model 6A) or "
 "county fixed effects (Model 6B), testing whether the main patterns simply reflect "
 "regional gradients within California rather than more local disparities.",

 "Model 7 adds measures of existing energy infrastructure, with a variant scaling those "
 "measures by population (Model 7PC), to examine whether local deployment patterns are "
 "partly explained by the surrounding energy-system context. Model 8 adds a demand proxy "
 "based on annual electricity consumption, which is particularly relevant for charging, "
 "where deployment may track commercial activity and underlying load as much as "
 "residential adoption potential. The demand proxy enters positively where it is "
 "significant — 0.018 (p < 0.001) for solar and 0.061 (p < 0.001) for storage — "
 "and is not distinguishable from zero for aggregate charging (0.007, p = 0.327). It is "
 "available for 1,196 of the 1,390 analysis ZCTAs, of which 1,159 report positive "
 "consumption; most remaining gaps fall outside the three investor-owned utility "
 "territories for which ZIP-level usage is published.",

 "Model 9 adds local solar deployment to the storage model, testing whether storage "
 "disparities persist after conditioning on upstream solar deployment. Model 9A instead "
 "adds DER deployment terms to the energy-burden outcomes. These are two distinct "
 "specifications with different outcomes and different control sets, and both condition on "
 "variables that are themselves outcomes of the same predictors, so each answers a narrow "
 "question rather than providing a better-identified estimate.",

 "The specifications above are stated formally below. Equation (4), the baseline estimating equation, is given in the Methods; the remaining specifications follow the same notation, in which y_z is the outcome in ZCTA z, RaceSES_z collects income, the race and ethnicity shares and poverty rate, X_z is the vector of contextual controls, and \u03b5_z is the error term.",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3 Climate_z + \u03b5_z                                      (5)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b8 SESextra_z + \u03b3 Climate_z + \u03b5_z                       (6)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b8 ResourceClimateAlt_z + \u03b5_z                            (7)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b4(Income_z \u00d7 Race_z) + \u03b3X_z + \u03b5_z                       (8)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03b4 Utility_z + \u03b5_z                                (9)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03b8 Geo_z + \u03b5_z                                  (10)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03b4 County_z + \u03b5_z                               (11)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03bb Infrastructure_z + \u03b5_z                       (12)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03bb Infrastructure_z + \u03d5 Demand_z + \u03b5_z          (13)",

 "y_z = \u03b2\u2080 + \u03b2 RaceSES_z + \u03b3X_z + \u03bb Infrastructure_z + \u03d5 Demand_z + \u03c8 DER_z + \u03b5_z (14)",

 "Supplementary Figures S1 to S3 trace every coefficient across this series for the three "
 "headline outcomes, one panel per coefficient, with 95 per cent confidence bands. Read "
 "against Figure 2 in the main text, which compresses the same information into one panel "
 "per outcome, they show which specific control block is responsible for each movement.",
]),

# ---------------------------------------------------------------- S2
("Supplementary Note S2 | The nested cumulative ladder", [
 "Because the model series is not nested, it cannot answer whether the control blocks "
 "jointly absorb the race coefficients. We therefore fit a second structure in which each "
 "rung is a strict superset of the last. Model C1 is the core specification. C2 adds "
 "educational attainment and median housing value. C3 adds housing structure and tenure. "
 "C4 adds utility fixed effects. C5 adds county fixed effects with county-clustered "
 "standard errors, dropping the ZCTA-level climate control that county fixed effects very "
 "nearly absorb; county and utility fixed effects are not stacked with climate in a single "
 "design matrix.",

 "Two design decisions matter for how the ladder should be read. First, the cumulative "
 "rungs use only pre-treatment confounders. Electricity demand and installed infrastructure "
 "capacity sit on the causal path from income and race to adoption, so conditioning on "
 "them estimates a direct rather than a total effect; they enter only a separate model, "
 "reported as a conservative lower bound and never as the headline estimate. Second, all "
 "rungs are fitted on one intersected, listwise-deleted sample — rows non-missing on "
 "every variable used anywhere in the ladder, plus the minimum cluster-size filter — so "
 "N and cluster count are identical at every rung and coefficient movement reflects "
 "controls alone. Interactions stay out of the cumulative ladder and remain their own arm "
 "in the model series.",

 "The frozen sample is 1,160 ZCTAs across 42 county clusters, and 1,150 for the two "
 "affordability outcomes. R² climbs monotonically as controls accumulate, from 0.11 to "
 "0.49 for solar, 0.24 to 0.42 for storage and 0.07 to 0.27 for aggregate charging; the "
 "largest single jump is always the addition of county fixed effects. Supplementary "
 "Figure S4 traces the coefficient paths and Supplementary Table S5 reports every "
 "coefficient.",

 "The result is weaker than the baseline models imply and is reported that way in the main "
 "text. Coefficients attenuate by roughly two-thirds to three-quarters between C1 and C5. "
 "For storage all three race terms survive; for solar only Asian share survives; for "
 "aggregate charging none does. This ordering is the same one the model series, the "
 "specification curve, the Oster bounds and the spatial error model all produce.",
]),

# ---------------------------------------------------------------- S3
("Supplementary Note S3 | Specification curve", [
 "A specification curve asks how much a reported coefficient depends on which controls "
 "happened to be included. We enumerate every subset of the six confounder blocks and fit "
 "each on the frozen sample, recording the four focal terms. Of the 64 possible "
 "combinations, 16 stack county and utility fixed effects together — near-collinear, "
 "near-exhaustive partitions of the same ZCTAs — and are excluded, leaving 48 valid "
 "specifications per outcome.",

 "Supplementary Figure S5 plots the sorted coefficient with its confidence interval for "
 "each outcome, with the block-membership matrix below. The summary counts appear in "
 "Table 2 of the main text: the number of specifications, out of 48, in which a "
 "coefficient is both significant at the 5 per cent level and same-signed as the median "
 "across all 48.",

 "Three readings are worth drawing out. Storage is the most reproducible result in the "
 "study: Asian share is significant and same-signed in 48 of 48, Hispanic share in 44, "
 "Black share in 36. Solar is intermediate, at 34, 31 and 28. Aggregate charging is "
 "fragile on race terms, and the Black-share coefficient is significant in 0 of 48 despite "
 "appearing significant in individual specifications — which is precisely the failure "
 "mode a specification curve exists to expose. Wind is weakest of all, at 0 of 48 on every "
 "term, consistent with its treatment as contextual rather than headline material.",
]),

# ---------------------------------------------------------------- S4
("Supplementary Note S4 | Oster bounds on omitted-variable bias", [
 "Oster's δ asks how strong selection on unobservables would have to be, relative to "
 "selection on the observed confounders, to drive a coefficient to zero. We compare the "
 "core specification with the saturated confounder model, setting R²max to 1.3 times "
 "the saturated R² and capping it at one. A value of δ ≥ 1 is the conventional "
 "robustness threshold: the omitted-variable bias would have to exceed the observed "
 "selection.",

 "Three coefficients clear that threshold and can be cited directly: storage Hispanic "
 "share at 1.99, solar Asian share at 1.57 and storage Asian share at 1.29. Storage income "
 "sits just below at 0.96, meaning selection on unobservables a little under the scale of "
 "the observed confounders would zero it out.",

 "δ is not interpretable everywhere, and that is itself informative. The formula "
 "assumes that adding controls moves a coefficient toward zero. For the solar income term "
 "and for aggregate charging the full confounder set increases the coefficient instead "
 "— solar income moves from 0.43 to 0.47 on the raw scale — so the returned values "
 "(−32.6 and +26.0) do not mean what δ normally means. We report δ only where "
 "the sign behaves as the method assumes, and treat the non-attenuation as a separate "
 "qualitative finding, discussed in the main text. Supplementary Table S7 reports every "
 "cell with the underlying β and R² values.",
]),

# ---------------------------------------------------------------- S5
("Supplementary Note S5 | Functional form, weighting and spatial models", [
 "Three features of the design invite objections that can be tested directly rather than "
 "argued about.",

 "Functional form. The outcomes are population-normalised rates entered as log(1 + rate), "
 "which keeps ZCTAs with zero deployment in the sample but handles the zeros only "
 "implicitly. Supplementary Table S8 reports Poisson pseudo-maximum-likelihood models "
 "fitted to the raw counts with log population as an offset, which handle the zeros "
 "directly. Every headline sign and significance is reproduced: solar Black share "
 "−2.13 and Asian share −1.99, storage Black share −1.53, Hispanic share "
 "−0.82 and Asian share −1.76, all at p ≤ 0.001, with aggregate charging Black "
 "share indistinguishable from zero and Hispanic share negative. Negative binomial fits "
 "agree.",

 "Weighting. The population floor is 1,000 residents, so unweighted regressions give a "
 "1,100-person ZCTA the same leverage as a 90,000-person one. Supplementary Table S9 "
 "reports population-weighted estimates. The solar and storage race coefficients hold, "
 "attenuating modestly. Two charging coefficients move: Black share becomes negative and "
 "significant under weighting, and Asian share becomes indistinguishable from zero, which "
 "is further reason not to build an interpretation on the aggregate charging race terms.",

 "Spatial structure. Conley standard errors correct inference for spatial dependence but "
 "leave the conditional mean untouched, so spatially structured omitted variables — "
 "installer density, permitting regimes, local programme administration — can still "
 "bias the coefficients. Supplementary Table S10 reports maximum-likelihood spatial error "
 "models on eight-nearest-neighbour weights. The spatial autoregressive parameter is large "
 "(λ = 0.85 for solar, 0.65 for storage, 0.45 for charging), confirming that a great "
 "deal of the structure is spatial. All three storage race coefficients remain negative "
 "and significant; solar survives for Asian share (−0.070, p = 0.012) but not Black "
 "share (p = 0.259); charging survives for Hispanic share alone. Two methods that treat "
 "spatial structure very differently therefore produce the same ordering.",
]),

# ---------------------------------------------------------------- S6
("Supplementary Note S6 | Housing structure and tenure", [
 "Housing is tested directly rather than left as a proposed mechanism. Model 2C adds the "
 "exhaustive ACS B25024 structure composition and Model 2D adds B25003 owner occupancy. "
 "Structure coefficients use single-family housing as the omitted reference, and tenure "
 "uses renters as the omitted reference.",

 "Supplementary Table S2 reports the coefficient pairs behind the attenuation figure in "
 "the main text. Area-level housing composition absorbs 53 per cent of the solar "
 "Black-share coefficient, 38 per cent of the solar Asian-share coefficient, 44 per cent "
 "of the storage Black-share coefficient and 32 per cent of the storage Asian-share "
 "coefficient. For aggregate charging the Asian-share coefficient collapses from positive "
 "to indistinguishable from zero.",

 "Movement toward zero is attenuation associated with area-level housing composition. "
 "These models observe the housing stock of an area, not the tenure or roof access of any "
 "household, so they cannot identify the household-level mechanism; what they establish is "
 "that a substantial share of what reads as a racial gap tracks the housing stock, and "
 "that a substantial share does not.",
]),

# ---------------------------------------------------------------- S7
("Supplementary Note S7 | Descriptive gradients", [
 "The regression tables summarise conditional associations, but the raw outcome gradients "
 "are also informative. Supplementary Figure S6 plots a combined non-white racial share "
 "against the three headline outcomes using deterministic LOWESS smoothing with seeded 95 "
 "per cent bootstrap confidence intervals. The fitted gradients are negative for all three "
 "technologies, with the largest descriptive decline for storage. Over the middle 90 per "
 "cent of the observed predictor range, the fitted endpoint change is about −0.20 for "
 "solar, −1.58 for storage and −0.02 for aggregate charging. These are descriptive "
 "summaries rather than causal effects, but they reinforce the regression finding that "
 "more heavily non-white ZCTAs tend to be less served across multiple outcomes.",

 "Supplementary Figure S7 provides the corresponding education view. The LOWESS fits show "
 "a mildly negative unconditional gradient for solar (−0.06) but positive gradients for "
 "storage (0.61) and charging (1.17). The corresponding standardised Model 2 charging "
 "regression also estimates a positive education coefficient (0.432, p < 0.001), "
 "indicating that bachelor's attainment is positively associated with aggregate charger "
 "deployment. Education is treated throughout as a control rather than as a headline "
 "predictor: it captures information, housing-market position and adoption capacity that "
 "overlap with income, and the central question is whether race remains associated with "
 "deployment once those proxies are included.",

 "Supplementary Figure S8 shows the underlying distributions. The three outcomes are "
 "strongly right-skewed and the socioeconomic context variables span materially different "
 "neighbourhood conditions, which is the reason for both the log(1 + rate) transformation "
 "and the standardised reporting scale.",
]),

# ---------------------------------------------------------------- S8
("Supplementary Note S8 | Exploratory neighbourhood typology", [
 "In addition to the regression work we use principal component analysis and K-means "
 "clustering to summarise ZCTA contexts in the statewide sample. This is descriptive "
 "rather than causal, and no result in the main text depends on it. The cluster map in "
 "Supplementary Figure S9 shows that the resulting profiles are spatially coherent rather "
 "than randomly scattered. Cluster identifiers are ordered by mean household income for "
 "stable interpretation.",

 "Supplementary Table S16 shows that clusters 1 and 2 are the lowest-income and most "
 "heavily Hispanic profiles; cluster 5 combines high income, the largest Asian share and "
 "the strongest charging outcome; and cluster 6 is the highest-income profile and has the "
 "strongest storage outcome. Two features are worth noting against the main results. The "
 "highest-Asian-share clusters are also the highest-income clusters, which is what makes "
 "an income-based reading of their low solar and storage deployment hard to sustain. And "
 "the cluster with the strongest charging outcome is not the cluster with the strongest "
 "storage outcome, which is the typology-level version of the paper's central point: "
 "technology access is shaped by bundles of demographic, economic, housing and "
 "infrastructural conditions rather than by one variable in isolation.",
]),

# ---------------------------------------------------------------- S9
("Supplementary Note S9 | Energy burden and affordability", [
 "The energy-burden outcomes provide affordability context for the DER results rather than "
 "cleanly orthogonal controls. In the matched sample, mean energy burden is about 2.2 per "
 "cent with an interquartile range from roughly 1.5 to 2.8 per cent, and burden is "
 "strongly negatively correlated with log median household income (−0.746) and "
 "positively correlated with poverty rate (0.545). The level sits below commonly cited "
 "household energy-burden estimates because the California Energy Commission series covers "
 "electricity costs rather than total household energy expenditure; it should be read as a "
 "relative affordability-stress index rather than a total-burden measure. Supplementary "
 "Figure S10 shows the descriptive gradients linking neighbourhood characteristics to both "
 "affordability outcomes.",

 "In the baseline model with energy burden as the outcome, income is strongly negative "
 "(−0.0096, p < 0.001), Hispanic share is positive (0.0036, p < 0.001) and Asian share "
 "is negative (−0.0077, p < 0.001), while Black share and poverty rate are not "
 "distinguishable from zero after the included controls. Supplementary Figure S12 traces "
 "these coefficients across the model series.",

 "The per-capita affordability gap requires care. Its distribution is severely skewed: the "
 "median ZCTA reports about $75 while the maximum exceeds $236,000, and the top 100 ZCTAs "
 "account for 92 per cent of the statewide total. We attribute this to error in the source "
 "series rather than to real variation. Main-text estimates therefore exclude the 134 "
 "ZCTAs whose per-capita gap exceeds $1,000, a threshold roughly thirteen times the "
 "median; Supplementary Table S11 reports both samples. The exclusion is not cosmetic. In "
 "the full sample, Asian share is positively associated with the affordability gap (0.090, "
 "p = 0.010); with the outliers removed the association disappears entirely (−0.019, "
 "p = 0.477), and R² rises from 0.32 to 0.45. We therefore do not report that "
 "association as a finding.",

 "Model 9A reverses the direction of the question and adds the DER outcomes as predictors "
 "of affordability. Only aggregate charging is distinguishable from zero: negatively "
 "associated with energy burden (−0.0011, p < 0.001) and positively with the logged "
 "affordability gap (1.002, p < 0.001). Solar, storage and the demand proxy are not "
 "significant for either outcome. Because the DER terms are themselves outcomes of the "
 "same demographic predictors, these coefficients describe associations and should not be "
 "read causally. Supplementary Figure S11 reports them.",

 "Taken together these results reinforce the main text's interpretation: affordability "
 "stress is itself spatially and demographically structured, but it does not make the DER "
 "outcomes interchangeable. Solar and storage remain tied to different race and income "
 "patterns than aggregate charging, and the charging result still appears to reflect a mix "
 "of infrastructure siting and household-serving access rather than a single uniform "
 "affordability channel.",
]),

# ---------------------------------------------------------------- S10
("Supplementary Note S10 | Wind as contextual comparison", [
 "The wind-capacity outcome is useful as contextual comparison but is not part of the "
 "paper's equity argument. For wind capacity the most consistent predictor is mean "
 "hub-height wind speed, which is positive and statistically significant across all "
 "examined models (Supplementary Figure S13). The social variables are weaker and less "
 "stable, and in the specification curve wind returns 0 of 48 significant same-signed "
 "specifications on every focal term — the weakest result in the study.",

 "This suggests that wind siting is far more tightly tied to physical resource conditions "
 "than the consumer-facing outcomes. Wind capacity is also zero in 97.5 per cent of ZCTAs, "
 "so a linear model on the logged rate is effectively a rare-event fit; the binary "
 "turbine-presence outcome is estimated as a linear probability model and is likewise not "
 "foregrounded. Because wind is not a behind-the-meter or consumer-facing resource, it is "
 "not directly comparable to the three headline technologies and is reported here as "
 "context only. Its cross-validated model comparison is in Supplementary Figure S16.",
]),

# ---------------------------------------------------------------- S11
("Supplementary Note S11 | Predictive model comparison and spatial output", [
 "In exploratory analysis we compare the linear specifications against more flexible "
 "predictive models — polynomial regression, random forest and gradient-boosted trees "
 "— using cross-validation. These are not the basis for any claim in the paper. They "
 "serve as a diagnostic on whether the linear models are missing strong nonlinear "
 "structure; the substantive conclusions remain grounded in the interpretable OLS results. "
 "Supplementary Figures S14 and S15 report the storage and aggregate charging comparisons, "
 "with error bars of ±1 standard deviation across five cross-validation folds, and "
 "Supplementary Figure S16 reports wind.",

 "Supplementary Figure S17 shows representative baseline spatial output for rooftop solar: "
 "observed adoption and the baseline standardised residuals by ZCTA, side by side. The "
 "residual map is the visual counterpart to the Moran's I statistics in Note S12 — what "
 "the model fails to explain is visibly clustered rather than scattered, which is what "
 "motivates the spatially robust standard errors and the spatial error model. The "
 "statewide observed geography for all three outcomes is Figure 1 in the main text.",

]),

# ---------------------------------------------------------------- S12
("Supplementary Note S12 | Statistical diagnostics", [
 "This Note reports diagnostic checks on the estimating equations. They do not alter any "
 "point estimate; they characterise how much confidence the standard errors deserve and "
 "where the specification is strained.",

 "Multicollinearity. Variance inflation factors for the solar models (Supplementary "
 "Table S17) show both a well-conditioned specification and a cautionary case. VIF is "
 "computed with the intercept retained in the auxiliary regressions, so raw and "
 "standardised diagnostics agree. The housing structure and tenure controls in Model 2D "
 "have a maximum VIF of 5.30, despite owner occupancy correlating −0.72 with "
 "multifamily share. In the per-capita infrastructure specification, wind MW per 100k and "
 "turbines per 100k reach 27.40 and 27.38; their individual coefficients should not be "
 "read separately. Across the cumulative ladder no focal term exceeds a VIF of 8.15 at any "
 "rung, so collinearity is not a threat to the coefficients the paper reports. VIF tables "
 "for every model and outcome are exported alongside the coefficient tables.",

 "Spatial autocorrelation. Moran's I measures whether what a model fails to explain is "
 "clustered in space. It runs from roughly −1 to 1, where 0 means residuals are "
 "scattered independently of location and positive values mean neighbouring ZCTAs carry "
 "similar residuals. Positive residual autocorrelation matters because it breaks the "
 "independence assumption behind heteroskedasticity-robust standard errors, which are then "
 "too small and overstate precision. We compute it on the OLS residuals using "
 "row-standardised eight-nearest-neighbour weights over ZCTA centroids, with pseudo "
 "p-values from 999 permutations (Supplementary Table S18). All 72 tests — six "
 "outcomes by four specifications by three neighbour counts — return p ≤ 0.001, so "
 "residual spatial dependence is present throughout rather than marginal.",

 "Two patterns are worth noting. Including latitude and longitude linearly absorbs almost "
 "none of the dependence, and for energy burden it is slightly worse than the baseline, so "
 "that specification should not be read as a geographic robustness check. County fixed "
 "effects remove roughly two-thirds of the dependence for solar and storage but leave it "
 "clearly present, which indicates clustering at a finer scale than counties. "
 "County-clustered standard errors therefore address the right concern at too coarse a "
 "resolution. Results are stable across four, eight and sixteen neighbours.",

 "Spatially robust standard errors. Given that dependence, we recompute the baseline "
 "standard errors following Conley (1999), allowing residuals to covary with great-circle "
 "distance under a Bartlett kernel (Supplementary Table S19). Point estimates are "
 "unchanged by construction; only the standard errors move. Because there is no consensus "
 "rule for the distance cutoff, several are reported. Standard errors rise by up to a "
 "factor of three relative to HC1 and plateau between 100 and 200 kilometres, consistent "
 "with clustering at utility-territory and metropolitan scale.",

 "The substantive conclusions hold but their relative strength changes, and this is where "
 "the ordering used in the main text comes from. The Asian-share coefficients for solar "
 "and storage remain significant at the 0.1 per cent level at every cutoff and are the "
 "most robust results in the paper. The Black-share coefficients remain negative and "
 "significant at the 5 per cent level but are less precisely estimated than the HC1 errors "
 "imply. The positive poverty coefficient for aggregate charging, which underpins the "
 "charger-composition argument, survives at the 1 per cent level. The positive Asian-share "
 "coefficient for aggregate charging is significant at 50 and 200 kilometres but not at "
 "100, which is why no interpretation is built on it.",
]),

# ---------------------------------------------------------------- S13
("Supplementary Note S13 | Data construction and measurement", [
 "Three properties of the source data govern how the outcomes should be read, and each is "
 "reported here rather than left implicit.",

 "The charging inventory is public and shared-use only. Every station record in the "
 "California Energy Commission charging file carries a public access flag, and the "
 "statewide Level 1 total is 256 ports against 40,078 Level 2 and 13,852 DC fast. "
 "Residential charging is therefore unobserved: no charging measure in this study speaks "
 "to whether a household can charge where it parks overnight. This is the reason the main "
 "text reads charger counts as a measure of infrastructure rather than of usable access. "
 "Charger records without a valid source ZIP are excluded from ZCTA outcomes rather than "
 "reassigned from coordinates, so the charging outcomes should be interpreted as "
 "valid-source-ZIP records.",

 "The storage series is overwhelmingly customer-sited. The California Energy Commission "
 "storage system survey covers utility-scale alongside behind-the-meter systems, and the "
 "distinction matters because the resilience interpretation in the main text holds only "
 "for customer-sited capacity. The underlying records are 193,070 residential, 3,211 "
 "commercial and 291 utility — 98.2 per cent residential. Supplementary Table S12 "
 "re-fits the storage baseline on capacity aggregated from all sectors and from "
 "residential records only; every sign and significance is reproduced in the "
 "residential-only specification, and the behind-the-meter reading of the storage results "
 "is supported by the source.",

 "Deployment is zero in a non-trivial share of ZCTAs, and the share differs sharply by "
 "technology: 5.3 per cent for solar, 6.6 for storage, 19.0 for aggregate charging, 22.3 "
 "for Level 2 and 44.2 for DC fast, but 97.8 per cent for Level 1 and 97.5 per cent for "
 "wind capacity (Supplementary Table S13). Level 1 charging and wind are therefore too "
 "sparse to support a coefficient at this geography, and are reported descriptively rather "
 "than modelled in the main text. The zero shares are also why the Poisson specifications "
 "in Note S5 matter: they fit the counts directly rather than through a transformation.",

 "Supplementary Table S14 gives variable definitions for every outcome, predictor and "
 "control, and Supplementary Table S15 gives summary statistics for the analysis sample. "
 "Supplementary Table S3 reports the predictor standard deviations used to convert "
 "standardised coefficients into percentage-point changes.",
]),
]
