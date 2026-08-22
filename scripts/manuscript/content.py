# -*- coding: utf-8 -*-
"""New manuscript content for the Nature Sustainability submission."""

TITLE = "Inequity in distributed energy adoption is technology-specific, not uniform"

AUTHORS = "Vineet Jagadeesan Nair¹*, [co-authors]\n¹Massachusetts Institute of Technology, Cambridge, MA, USA\n*Corresponding author: jvineet9@mit.edu"

ABSTRACT = (
    "Distributed energy resources are central to decarbonisation, resilience and "
    "electrification, but their benefits are not guaranteed to be shared evenly. Evidence "
    "of racial disparity in rooftop solar is usually assumed to generalise across "
    "technologies. We test that assumption across 1,390 California ZIP Code Tabulation "
    "Areas, harmonising rooftop photovoltaics, battery storage and electric-vehicle "
    "charging under one set of outcomes and controls. The technologies do not share a "
    "disparity pattern. Areas with larger Black and Asian population shares hold less "
    "solar and less storage after conditioning on income and poverty, and area-level "
    "housing type and tenure absorb 32 to 53 per cent of those gaps. Under a fully "
    "stacked specification, storage disparities persist on all three race terms, solar "
    "only for Asian share, and charging not at all. Charger counts instead rise with "
    "poverty, concentrated in faster public units. Counts measure infrastructure, not "
    "usable access, so technology-blind equity targets misread all three."
)

# ---------------------------------------------------------------- Introduction
INTRO = [
 "As electricity systems decarbonise, distributed energy resources (DERs) are becoming "
 "central to emissions reduction, local resilience and electrification. Policy debate "
 "treats them as a single category, but the benefits they deliver are heterogeneous. "
 "Rooftop photovoltaics (PV) reduce bills for the household that hosts them. Battery "
 "storage delivers backup power and outage protection, which matter most where wildfire "
 "shutoffs and grid stress are common. Charging infrastructure determines who can "
 "participate in transportation electrification, and only if it sits where people "
 "actually live and park. The clean energy transition is therefore not only a deployment "
 "problem but a distributional one: where access depends on financing, housing "
 "conditions, siting decisions, permitting, interconnection or neighbourhood "
 "infrastructure, the transition can reproduce existing inequities rather than reduce "
 "them.",

 "The evidence that it does so is almost entirely about solar. Lukanov and Krieger show "
 "that California PV deployment is patterned by neighbourhood socioeconomic conditions "
 "[1], and Sunter, Castellanos and Kammen show that racial and ethnic disparities in "
 "rooftop PV persist after accounting for income [2]. Kurdgelashvili and colleagues "
 "model county-level adoption in the same state [3], while Reames and Darghouth et al. "
 "document uneven rooftop access across communities and Sigrist et al. argue that "
 "inequitable siting reduces the carbon value of residential solar [4], [5], [6]. A "
 "parallel literature explains why race should be modelled explicitly rather than "
 "assumed away: race-linked inequities in energy burden persist net of income [7], "
 "transition planning cannot be treated as race-neutral when the underlying burdens are "
 "not [8], and structural barriers limit participation in California's DER programmes "
 "even where they are designed for low-income households [9]. Because rooftop solar "
 "measurably reduces energy burden for low- and moderate-income adopters [10], unequal "
 "access to DERs also means unequal access to bill relief and resilience.",

 "What this literature does not establish is whether inequity in DER adoption is a "
 "solar-specific phenomenon or a general feature of the transition. The distinction "
 "matters because the barriers differ. Rooftop PV depends on roof control, housing "
 "tenure, financing and installer availability. Storage overlaps with PV but adds "
 "stronger dependence on upfront capital, resilience value and programme design; it has "
 "been framed as an equity asset that can either broaden resilience or entrench "
 "advantage depending on ownership [17], [22]. Charging depends far more on siting, "
 "commercial activity and host context. Adoption is also gated by the grid itself: "
 "hosting-capacity constraints in California are socially patterned and limit deployment "
 "in disadvantaged communities [11], a problem that fairness-aware allocation schemes "
 "are only beginning to address [15], and that interconnection roadmaps identify as a "
 "national bottleneck [16]. A community adopting solar at the state average may still "
 "lack the storage that protects it during an outage, or the charging that lets its "
 "residents switch vehicles. Collapsing all three into one undifferentiated measure of "
 "“DER access” can hide exactly these offsetting patterns.",

 "Three gaps follow. First, the evidence base for racial disparity net of income is "
 "solar-only, so we do not know whether inequity is a property of solar adoption or of "
 "the transition. Second, work that looks beyond PV treats each technology in isolation, "
 "under different data, geographies and specifications, which prevents direct "
 "comparison. Third, no harmonised, race-inclusive, multi-technology dataset exists at "
 "fine spatial granularity for a single high-penetration market, because DER data is "
 "fragmented across technologies and agencies [23], [24].",

 "This paper addresses all three. We assemble a California ZIP Code Tabulation Area "
 "(ZCTA) dataset integrating rooftop PV, battery storage and EV charging with American "
 "Community Survey demographics, climate and resource data, utility territory and "
 "electricity demand, and estimate one consistent set of specifications across all "
 "three, retaining race in every model rather than assuming socioeconomic controls "
 "absorb it. California is an informative case because it combines high DER penetration, "
 "ambitious climate policy, substantial socioeconomic diversity and pronounced spatial "
 "inequality. The study is area-level and cross-sectional; we report conditional "
 "associations, not causal effects. The central finding is that the form of inequity "
 "changes by technology, and that for charging the standard metric — the count of "
 "installed units — does not measure what equity policy assumes it measures.",
]

# ---------------------------------------------------------------- Results
RESULTS = [
 ("H2", "Disparities differ by technology"),
 ("", "Racial and socioeconomic disparities are not uniform across technologies. In the "
  "baseline specification (Table 1), rooftop PV and battery storage both carry clear "
  "negative associations with ZCTA shares of Black and Asian residents after "
  "conditioning on income and poverty. EV charging departs from that pattern: charger "
  "deployment is negatively associated with Hispanic share and positively associated "
  "with poverty rate. Figure 2 places the three outcomes on a common standardised scale. "
  "All coefficients reported in the main text are standardised, so a coefficient is the "
  "change in outcome standard deviations associated with a one-standard-deviation change "
  "in the predictor; one standard deviation is 6.6 percentage points for Black share, "
  "23.8 for Hispanic share and 14.1 for Asian share (Supplementary Table S3)."),
 ("", "Baseline explanatory power is low by construction — R² runs from 0.07 to 0.24 "
  "across the three outcomes. The objective here is coefficient stability under "
  "conditioning rather than prediction, and area-level cross-sections of this kind carry "
  "substantial local heterogeneity that no set of ZCTA-level covariates absorbs. As "
  "controls accumulate, R² rises to 0.49 for PV and 0.42 for storage."),
 ("", "Housing is tested directly rather than left as a proposed mechanism. Adding the "
  "exhaustive ACS B25024 structure composition, with single-family units as the "
  "reference, and B25003 owner occupancy, with renters as the reference, moves the "
  "standardised Black-share coefficient for PV from −0.049 to −0.023 and the Asian-share "
  "coefficient from −0.082 to −0.051. For storage the corresponding movements are "
  "−0.106 to −0.059 and −0.252 to −0.171 (Figure 4). Area-level housing composition "
  "therefore absorbs between 32 and 53 per cent of these coefficients. What remains is "
  "not explained by the housing stock, but these models do not identify household-level "
  "tenure or roof access."),

 ("H2", "Rooftop solar and storage"),
 ("", "For rooftop PV, ZCTAs with higher median household income show higher adoption "
  "intensity, while those with larger Black and Asian population shares show "
  "substantially lower intensity. Solar resource potential behaves as expected: mean "
  "global horizontal irradiance is positive and highly significant, so the racial "
  "gradient is not an artefact of lower-income areas having worse solar resource. The "
  "negative Black- and Asian-share coefficients persist as education, county clustering, "
  "infrastructure context and electricity demand enter the specification "
  "(Supplementary Fig. S1)."),
 ("", "Battery storage shows the strongest and most stable disparity pattern of the three. "
  "Income is strongly positive, and Black, Hispanic and Asian shares are all negative, "
  "with coefficients larger in magnitude than the corresponding PV estimates and "
  "negative across nearly every specification examined (Supplementary Fig. S2). Adding "
  "local PV deployment to the most controlled storage specification leaves the race "
  "coefficients negative and significant, so the storage gap is not simply the solar gap "
  "restated further down the same adoption pathway. That model conditions on a parallel "
  "outcome of the same predictors and is therefore not a better-identified estimate of "
  "the storage gap; it answers only that narrower question (Supplementary Table S6)."),
 ("", "The substantive point is that storage inequity is deeper than solar inequity, and "
  "storage is the technology whose benefit — backup power during outages and wildfire "
  "shutoffs — is most concentrated in exactly the communities that show the lowest "
  "deployment. Reported standard errors are heteroskedasticity-robust; spatially robust "
  "alternatives that allow residuals to covary with distance are reported in "
  "Supplementary Table S8, and residual spatial dependence is documented in "
  "Supplementary Table S7."),
 ("", "The Asian-share coefficients deserve separate comment, because they point in "
  "different directions across technologies and because housing composition explains "
  "most of that difference. In the baseline the standardised coefficient is −0.082 for "
  "PV and −0.252 for storage, and positive for aggregate charging at 0.058. Once housing "
  "structure and tenure enter, the charging coefficient falls to −0.008 and is no longer "
  "distinguishable from zero, while the PV and storage coefficients attenuate but remain "
  "negative at p < 0.001. The apparent sign reversal is not a stable feature of the "
  "data. High-Asian-share ZCTAs are also the highest-income profiles in the sample, "
  "which is hard to square with an income-based reading of their low PV and storage "
  "deployment; they concentrate in dense metropolitan submarkets where multifamily "
  "housing and lower owner-occupancy limit roof control, and the same density supports "
  "commercial charging siting."),

 ("H2", "Charging measures infrastructure, not access"),
 ("", "The charging results are more complex. The aggregate baseline has a positive but "
  "not conventionally significant income coefficient, a near-zero Black-share "
  "coefficient, a negative Hispanic-share coefficient and a positive Asian-share "
  "coefficient, while poverty rate is strongly positive. The positive Asian-share "
  "coefficient is not stable: under Conley spatially robust standard errors it remains "
  "significant at 50 km and 200 km but not at 100 km, and it reverses sign once housing "
  "structure and tenure enter, so we build no interpretation on it."),
 ("", "The charger-type decomposition clarifies what the aggregate is measuring. The "
  "positive association with poverty is driven by Level 2 units; for DC fast chargers "
  "the coefficient is positive but imprecisely estimated (Figure 3b, Supplementary "
  "Table S4). Level 1 units cannot be tested at all: 97.8 per cent of ZCTAs report zero, "
  "against a statewide total of 256 Level 1 ports compared with 40,078 Level 2 and "
  "13,852 DC fast. We therefore report the Level 1 zero share rather than a coefficient, "
  "and the aggregate-versus-Level 2 contrast carries the argument."),
  ("", "Two features of the charger data govern how these counts should be read. The "
  "inventory records public and shared-use stations only — every station row is flagged "
  "public access — so residential charging is unobserved, and no measure in this study "
  "speaks to whether a household can charge where it parks overnight. And because the "
  "association concentrates in Level 2 units rather than the slowest ports, the pattern "
  "is consistent with siting driven by commercial and industrial activity rather than by "
  "household-serving provision. We treat that siting interpretation as a hypothesis: the "
  "dataset carries no charger-host or facility-type field, so it is not directly tested "
  "here. What the data do establish is narrower and still consequential — a higher "
  "charger count in a higher-poverty ZCTA is not evidence of better household charging "
  "access, because the counts do not include the charging that households actually use."),

 ("H2", "Disparities under a fully stacked specification"),
 ("", "The specifications above vary one control block at a time against a fixed core. "
  "That design isolates which block moves which coefficient, but it is a model series "
  "rather than a nested sequence, and it cannot show whether the controls jointly absorb "
  "the race coefficients. We therefore also estimate a genuinely nested cumulative "
  "ladder: C1 (income, race, poverty, climate), C2 (adding education and housing value), "
  "C3 (adding housing structure and tenure), C4 (adding utility fixed effects) and C5 "
  "(adding county fixed effects with county-clustered standard errors). All five rungs "
  "are fitted on one frozen common sample of 1,160 ZCTAs across 42 county clusters, "
  "identical at every rung, so movement reflects added controls rather than sample "
  "drift. A further model adds electricity demand and infrastructure capacity; these sit "
  "on the causal path from income and race to adoption, so it is reported only as a "
  "conservative lower bound (Supplementary Table S5)."),
 ("", "Figure 2 traces the result, and it is weaker than the baseline models imply. "
  "Coefficients attenuate by roughly two-thirds to three-quarters between C1 and C5, and "
  "what survives differs by technology. For storage, all three race terms remain "
  "negative and significant at C5: Black share −0.034 (p = 0.009), Hispanic share "
  "−0.113 (p = 0.016) and Asian share −0.116 (p < 0.001). For PV, only Asian share "
  "survives, at −0.114 (p = 0.010); the Black-share coefficient falls to −0.017 and is "
  "no longer distinguishable from zero (p = 0.472). For aggregate charging, no race term "
  "survives. Storage is thus the one technology whose racial disparities hold under the "
  "full confounder set."),
 ("", "Two further checks agree with that ranking. Across all 48 valid combinations of the "
  "six confounder blocks, the storage Asian-share coefficient is significant and "
  "same-signed in 48 of 48 specifications, Hispanic share in 44 and Black share in 36; "
  "the corresponding PV counts are 34, 31 and 28; and for aggregate charging the "
  "Black-share coefficient is significant in 0 of 48, despite appearing significant in "
  "some single specifications (Supplementary Fig. S3). Oster bounds tell the same story: "
  "storage Hispanic share (δ = 1.99), PV Asian share (1.57) and storage Asian share "
  "(1.29) exceed the conventional threshold of one, meaning selection on unobservables "
  "would have to be stronger than selection on the observed confounders to explain them "
  "away. We do not report δ for the PV income term or for aggregate charging: adding "
  "the full confounder set increases rather than shrinks those coefficients, so the "
  "assumption underlying the bound does not hold."),
 ("", "A spatial error model reaches the same conclusion by a different route. Fitting the "
  "core specification with an eight-nearest-neighbour spatial error term (λ = 0.85 for "
  "PV, 0.65 for storage, 0.45 for charging) leaves all three storage race coefficients "
  "negative and significant, leaves PV significant for Asian share only (−0.070, "
  "p = 0.012) and not for Black share (p = 0.259), and leaves charging significant for "
  "Hispanic share alone (Supplementary Table S9). Two methods that treat spatial "
  "structure very differently therefore produce the same ordering. Functional form does "
  "not drive the result either: Poisson pseudo-maximum-likelihood models on raw counts "
  "with a population offset, which handle the zeros directly rather than through a "
  "log(1 + x) transformation, reproduce the sign and significance of every headline "
  "coefficient (Supplementary Table S10), as do population-weighted estimates "
  "(Supplementary Table S11)."),
 ("", "The fully stacked estimates are the conservative reading. The model series shows "
  "which controls do the absorbing, and housing composition does most of it."),

 ("H2", "Affordability context"),
 ("", "The energy-burden outcomes provide affordability context rather than orthogonal "
  "controls: burden is strongly negatively correlated with income (−0.75) and "
  "positively with poverty (0.55). Income is strongly negative for both burden measures "
  "and Hispanic share positive, consistent with affordability stress being itself "
  "demographically structured. The per-capita affordability gap is severely skewed — "
  "the median ZCTA reports about $75 while the maximum exceeds $236,000, and the top 100 "
  "ZCTAs account for 92 per cent of the statewide total — which we attribute to error in "
  "the source series rather than to real variation. Main-text estimates therefore "
  "exclude the 134 ZCTAs above $1,000 per capita; the full-sample results are in "
  "Supplementary Table S12. The exclusion matters: the positive Asian-share association "
  "with the affordability gap in the full sample (0.090, p = 0.010) disappears once the "
  "outliers are removed (−0.019, p = 0.477), and we do not report it as a finding."),
]

# ---------------------------------------------------------------- Discussion
DISCUSSION = [
 ("H2", "What persists and what changes across technologies"),
 ("", "The clean energy transition does not reproduce inequality in the same way across "
  "technologies. Rooftop PV shows racial and socioeconomic patterning that is "
  "substantially, though not entirely, explained by housing composition. Storage is more "
  "unequal and more stable, and is the only technology whose disparities survive a fully "
  "stacked specification, a specification curve and a spatial error model alike. "
  "Aggregate charging does not fit an underserved-versus-served story at all; the "
  "measure mixes infrastructure types that serve different users under different siting "
  "logics. A community that appears relatively well served on one aggregate metric may "
  "still be underserved in the specific benefit that matters — bill savings from PV, "
  "resilience from storage, or charging it can actually use."),

 ("H2", "Plausible mechanisms"),
 ("", "For rooftop PV, the persistence of negative coefficients after income controls is "
  "consistent with barriers beyond household income: roof access, housing tenure, "
  "installer market penetration, credit constraints, and permitting and interconnection "
  "frictions. For storage, larger and more stable disparities are consistent with higher "
  "upfront capital requirements, dependence on bundled solar-plus-storage pathways and "
  "programmatic complexity that advantages already well-positioned households."),
 ("", "One result runs against the expected direction and deserves its own explanation. "
  "Adding the full confounder set does not shrink the PV income coefficient; it "
  "increases it. Education, housing value, structure, tenure and geography together "
  "leave the income gradient in rooftop solar larger than the core specification "
  "implies, which is the opposite of what omitted-variable reasoning predicts and why "
  "the Oster bound is not interpretable for that term. The most plausible reading is "
  "that these controls are absorbing variation that suppresses the income gradient — "
  "dense, high-value, high-income submarkets with low owner-occupancy — and that once "
  "housing is held fixed, the remaining income effect reflects financing and adoption "
  "capacity more directly. If so, the barrier is not price alone but access to capital "
  "and to installers, which points at third-party ownership and inclusive financing "
  "rather than at incentive levels."),
 ("", "For charging, the positive poverty association appears in Level 2 units and not in "
  "the aggregate's slowest ports, which is consistent with siting driven by commercial "
  "and industrial activity rather than household-serving provision. Because the "
  "inventory covers only public and shared-use stations, the counts cannot speak to "
  "residential charging at all. Aggregate charger counts are therefore not neutral "
  "measures of equitable access: they can record infrastructure abundance in places "
  "where practical charging access for residents, particularly renters and multifamily "
  "residents, remains limited."),

 ("H2", "Implications for how equity is measured"),
 ("", "If equity is measured too coarsely, policy can mistake infrastructure counts for "
  "access, or progress in one technology for progress in another. The charging result is "
  "the sharpest case: a deployment target expressed in chargers per capita can be met "
  "entirely through commercial siting while household-serving access does not move. The "
  "storage result is the sharpest equity case: the communities most exposed to outages "
  "and wildfire shutoffs show the lowest deployment of the technology that buffers them, "
  "and that gap does not follow solar access. If PV, storage and residentially usable "
  "charging remain concentrated in already advantaged communities, lower-income and more "
  "heavily non-white communities face a double burden — higher exposure to outage risk "
  "and cost burden alongside lower access to the technologies that reduce both."),
 ("", "That racial disparities persist after income controls, for storage under every "
  "specification we examined, is the reason these results bear on race-neutral planning. "
  "Eligibility rules keyed only to income or to generic disadvantaged-community "
  "designations will miss communities that are underserved on race-correlated "
  "dimensions. This is an area-level finding and does not describe individual household "
  "behaviour, but eligibility rules are themselves written at area level."),

 ("H2", "Policy levers differ by technology"),
 ("", "The implication is not that disadvantaged places need more DERs in the aggregate, "
  "but that the three technologies require different instruments. For rooftop solar, the "
  "persistence of disparities after observed controls supports targeted incentives, "
  "community-solar expansion, financing support and outreach that reduce adoption "
  "frictions; the income result above suggests financing access and installer presence "
  "matter more than headline incentive levels. For storage, which warrants the sharpest "
  "targeting, resilience rebates, backup-power provisioning and community-storage "
  "programmes should weight toward communities exposed to outages and wildfire shutoffs, "
  "since the storage gap does not follow PV access. For charging, procurement targets "
  "should measure usable residential access through multifamily, curbside and "
  "renter-serving deployment rather than aggregate counts, which the subtype results "
  "show can overstate access."),
 ("", "Two further levers sit outside consumer programmes. Adoption is partly gated by "
  "hosting-capacity and interconnection frictions that are themselves socially patterned "
  "[11], [15]; operators can publish hosting-capacity and interconnection-queue outcomes "
  "disaggregated by community demographics and pilot fairness-aware allocation so that "
  "grid upgrades do not concentrate where adoption is already high. And persistent PV "
  "and storage gaps after income controls point at non-price barriers — installer "
  "market penetration, financing access, split incentives for renters — that "
  "third-party ownership, on-bill and inclusive financing, and community "
  "solar-plus-storage can address where subsidies alone do not."),
 ("", "California is both an empirical case and an early warning. As decarbonisation "
  "expands, the question is not only how quickly DERs diffuse but whether the benefits "
  "of that diffusion reduce inequality or reproduce it in new forms. Answering it "
  "requires a multi-technology equity lens rather than a single-technology one, and "
  "measurement that distinguishes infrastructure presence from usable benefit. "
  "Income-keyed eligibility rules, undifferentiated deployment targets and race-neutral "
  "planning defaults each need revisiting if the transition is to narrow existing gaps "
  "rather than widen them."),
]
