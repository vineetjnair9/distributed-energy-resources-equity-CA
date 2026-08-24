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
# Ordered by evidential strength rather than by technology convention: storage is the
# strongest result in the study on every robustness measure, charging is the most
# distinctive, and solar is the case where housing composition does most of the work.
RESULTS = [
 ("H2", "Disparities differ by technology"),
 ("", "Racial and socioeconomic disparities are not uniform across technologies. In the "
  "baseline specification (Table 1), rooftop photovoltaics and battery storage both carry "
  "clear negative associations with ZCTA shares of Black and Asian residents after "
  "conditioning on income and poverty. EV charging departs from that pattern: charger "
  "deployment is negatively associated with Hispanic share and positively associated with "
  "poverty rate. Coefficients reported throughout use standardised predictors, so a "
  "coefficient is the change in the log(1 + rate) outcome associated with a "
  "one-standard-deviation change in the predictor; one standard deviation is 6.6 "
  "percentage points for Black share, 23.8 for Hispanic share and 14.1 for Asian share, "
  "and a coefficient near \u22120.10 corresponds to roughly a 10 per cent lower deployment "
  "rate (Supplementary Table S3)."),
 ("", "Figure 2 traces the five focal coefficients across the model series, in which each "
  "specification adds or substitutes one control block against a fixed core. Reading the "
  "three panels together is the paper's central comparison. The storage coefficients are "
  "the largest and the flattest: race and ethnicity shares stay negative and separated "
  "from zero across every specification. The solar coefficients are smaller and move more, "
  "particularly where housing enters. The charging coefficients behave differently again, "
  "with poverty rate the only consistently signed predictor and the race terms crossing "
  "zero. Whatever is producing inequity is not one mechanism operating at three "
  "intensities."),
 ("", "Baseline explanatory power is low by construction, from 0.07 to 0.19 across the "
  "three outcomes. The objective is coefficient stability under conditioning rather than "
  "prediction, and area-level cross-sections of this kind carry substantial local "
  "heterogeneity that no set of ZCTA-level covariates absorbs. As controls accumulate, "
  "R\u00b2 rises to 0.49 for solar and 0.42 for storage (Supplementary Table S5)."),

 ("H2", "Battery storage: the deepest and most persistent disparities"),
 ("", "Storage carries the strongest disparity pattern in the study. In the baseline, "
  "income is strongly positive while Black, Hispanic and Asian shares are all negative and "
  "precisely estimated, with coefficients larger in magnitude than the corresponding solar "
  "estimates. Unlike the other two outcomes, the pattern does not depend on any single "
  "control block: it survives educational attainment, housing value, housing structure and "
  "tenure, utility fixed effects, county clustering, infrastructure context and the "
  "electricity-demand proxy, and the confidence bands in Figure 2b stay clear of zero "
  "throughout (Supplementary Fig. S2)."),
 ("", "It also survives every robustness check we ran. Under Conley spatially robust "
  "standard errors the Asian- and Hispanic-share coefficients hold at every distance "
  "cutoff. Across all 48 valid combinations of the six confounder blocks, the Asian-share "
  "coefficient is significant and same-signed in 48 of 48, Hispanic share in 44 and Black "
  "share in 36 \u2014 the highest counts for any outcome. Oster bounds put storage Hispanic "
  "share at \u03b4 = 1.99 and Asian share at 1.29, both above the conventional threshold of "
  "one, meaning selection on unobservables would have to be stronger than selection on the "
  "observed confounders to explain them away (Table 2). A Poisson model fitted to raw "
  "capacity with a population offset, and a spatial error model, reproduce all three signs "
  "and significances (Supplementary Tables S8 and S10)."),
 ("", "Adding local solar deployment to the most controlled storage specification leaves "
  "the race coefficients negative and significant, so the storage gap is not the solar gap "
  "restated further down a shared adoption pathway. That model conditions on a parallel "
  "outcome of the same predictors and is therefore not a better-identified estimate of the "
  "storage gap; it answers only that narrower question (Supplementary Table S6)."),
 ("", "The substantive point is that storage inequity is deeper than solar inequity and "
  "more robust than either of the other two results, and storage is the technology whose "
  "benefit \u2014 backup power during outages and wildfire shutoffs \u2014 is most "
  "concentrated in exactly the communities showing the lowest deployment."),

 ("H2", "Rooftop solar: disparities that housing composition partly explains"),
 ("", "For rooftop solar, ZCTAs with higher median household income show higher adoption "
  "intensity, while those with larger Black and Asian population shares show substantially "
  "lower intensity. Solar resource potential behaves as expected: mean global horizontal "
  "irradiance is positive and highly significant, so the racial gradient is not an "
  "artefact of lower-income areas having worse solar resource. Hispanic share runs the "
  "other way for solar alone, positive and significant, and does not follow the Black and "
  "Asian pattern in any specification; we therefore treat the solar racial gradient as a "
  "Black- and Asian-share result rather than a general non-white one."),
 ("", "Housing is tested directly rather than left as a proposed mechanism. Adding the "
  "exhaustive ACS B25024 structure composition, with single-family units as the reference, "
  "and B25003 owner occupancy, with renters as the reference, moves every race coefficient "
  "for solar and storage toward zero without eliminating it (Figure 3). Area-level housing "
  "composition absorbs between 32 and 53 per cent of these coefficients across the four "
  "technology-by-race combinations, most for the solar Black share and least for the "
  "storage Asian share (Supplementary Table S2). Movement toward zero is attenuation "
  "associated with area-level housing composition; these models do not identify "
  "household-level tenure or roof access."),
 ("", "The two solar race coefficients are not equally solid, and the paper should not "
  "treat them as though they were. The Asian-share coefficient is robust: significant at "
  "the 0.1 per cent level at every Conley distance cutoff, same-signed and significant in "
  "34 of 48 specification-curve combinations, and clearing the Oster threshold at \u03b4 = "
  "1.57. The Black-share coefficient is weaker on all three measures \u2014 28 of 48, "
  "\u03b4 = 0.32, and less precisely estimated than the heteroskedasticity-robust errors "
  "imply once residuals are allowed to covary with distance. We report both, and rest the "
  "solar conclusion on the Asian-share result."),
 ("", "High-Asian-share ZCTAs are also the highest-income profiles in the sample, which is "
  "hard to square with an income-based reading of their low solar and storage deployment. "
  "They concentrate in dense metropolitan submarkets where multifamily housing and lower "
  "owner-occupancy limit roof control, and the same density supports commercial charging "
  "siting \u2014 which is why the sign flips for charging in the baseline and collapses "
  "toward zero once housing enters."),

 ("H2", "Charging measures infrastructure, not usable access"),
 ("", "The charging results are the most distinctive in the study and the least like a "
  "conventional access gradient. The aggregate baseline has a positive but not "
  "conventionally significant income coefficient, a near-zero Black-share coefficient, a "
  "negative Hispanic-share coefficient and a positive Asian-share coefficient, while "
  "poverty rate is strongly positive. The positive Asian-share coefficient is not stable: "
  "under Conley standard errors it remains significant at 50 km and 200 km but not at 100 "
  "km, and it reverses sign once housing structure and tenure enter, so we build no "
  "interpretation on it. The Black-share coefficient is significant in 0 of 48 "
  "specification-curve combinations despite appearing significant in individual "
  "specifications \u2014 the clearest case in the study of a coefficient that should not be "
  "reported from one model alone."),
 ("", "The charger-type decomposition clarifies what the aggregate is measuring. The "
  "positive association with poverty is driven by Level 2 units; for DC fast chargers the "
  "coefficient is positive but imprecisely estimated (Figure 4, Supplementary Table S4). "
  "Level 1 units cannot be tested at all: 97.8 per cent of ZCTAs report zero, against a "
  "statewide total of 256 Level 1 ports compared with 40,078 Level 2 and 13,852 DC fast. "
  "We therefore report the Level 1 zero share rather than a coefficient, and the "
  "aggregate-versus-Level 2 contrast carries the argument."),
 ("", "Two features of the charger data govern how these counts should be read. The "
  "inventory records public and shared-use stations only \u2014 every station row is "
  "flagged public access \u2014 so residential charging is unobserved, and no measure in "
  "this study speaks to whether a household can charge where it parks overnight. And "
  "because the association concentrates in Level 2 units rather than the slowest ports, "
  "the pattern is consistent with siting driven by commercial and industrial activity "
  "rather than by household-serving provision. We treat that siting interpretation as a "
  "hypothesis: the dataset carries no charger-host or facility-type field, so it is not "
  "directly tested here. What the data do establish is narrower and still consequential "
  "\u2014 a higher charger count in a higher-poverty ZCTA is not evidence of better "
  "household charging access, because the counts do not include the charging that "
  "households actually use."),

 ("H2", "Disparities under a fully stacked specification"),
 ("", "The model series varies one control block at a time, which isolates what each block "
  "absorbs but cannot show whether the blocks jointly account for the race coefficients. "
  "We therefore also fit a nested cumulative ladder in which each rung is a strict "
  "superset of the last, from a core specification through education and housing value, "
  "housing structure and tenure, utility fixed effects, and finally county fixed effects "
  "with county-clustered standard errors. All rungs are fitted on one frozen sample of "
  "1,160 ZCTAs across 42 county clusters, identical at every rung, so movement reflects "
  "controls rather than sample drift (Supplementary Table S5 and Supplementary Fig. S4)."),
 ("", "Coefficients attenuate by roughly two-thirds to three-quarters, and what survives "
  "tracks the ordering above. For storage, all three race terms remain negative and "
  "significant: Black share \u22120.034 (p = 0.009), Hispanic share \u22120.113 (p = "
  "0.016) and Asian share \u22120.116 (p < 0.001). For solar, only Asian share survives, "
  "at \u22120.114 (p = 0.010); the Black-share coefficient falls to \u22120.017 and is no "
  "longer distinguishable from zero (p = 0.472). For aggregate charging, no race term "
  "survives. The fully stacked estimates are the conservative reading of the same pattern "
  "the model series shows, and they place storage, solar and charging in the same order "
  "(Table 2)."),

 ("H2", "Affordability context"),
 ("", "The energy-burden outcomes provide affordability context rather than orthogonal "
  "controls: burden is strongly negatively correlated with income (\u22120.75) and "
  "positively with poverty (0.55). Income is strongly negative for both burden measures "
  "and Hispanic share positive, consistent with affordability stress being itself "
  "demographically structured. The per-capita affordability gap is severely skewed, and "
  "main-text estimates exclude the 134 ZCTAs whose gap exceeds $1,000 per capita; the "
  "exclusion removes a previously apparent positive Asian-share association that we "
  "therefore do not report as a finding (Supplementary Table S11 and Supplementary "
  "Note S9)."),
]

# ---------------------------------------------------------------- Discussion
DISCUSSION = [
 ("H2", "What persists and what changes across technologies"),
 ("", "The clean energy transition does not reproduce inequality in the same way across "
  "technologies. Storage is the clearest case: the deepest disparities in the study, "
  "stable across every specification in the model series, and the only outcome whose race "
  "coefficients survive a fully stacked specification, a specification curve and a spatial "
  "error model alike. Rooftop solar shows racial and socioeconomic patterning that housing "
  "composition substantially, though not entirely, explains, and whose surviving component "
  "is carried by Asian share rather than by Black share. "
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
