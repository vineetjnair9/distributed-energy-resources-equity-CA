# Nature Sustainability — Presubmission Inquiry

**Submit via:** the "Presubmission enquiry" option in the Nature Sustainability online submission system (nature.com/natsustain → Submit manuscript). Editors typically respond in 1–2 weeks.

**Placeholders to fill before sending:** `[Danielle SURNAME]`, `[co-author list]`, `[affiliation]`. Verify the current Chief Editor's name on the journal masthead rather than using a generic salutation if you can.

---

## Draft inquiry

**Subject:** Presubmission enquiry — aggregate infrastructure counts misstate equity in distributed energy deployment

Dear Editors,

I am writing to ask whether the work described below would be of interest to *Nature Sustainability* as a full submission.

**The problem.** Governments and utilities increasingly measure clean-energy equity by counting deployed infrastructure — chargers per capita, rooftop solar per capita, storage per capita — and target programs accordingly. We show that for at least one major technology this metric does not measure what planners believe it measures, and that the direction of the error is the opposite of what equity targeting assumes.

**What we find.** Using a harmonized ZIP-code-level dataset covering all of California — the largest and most policy-active distributed energy market in the United States — we estimate deployment disparities for rooftop solar, battery storage, and EV charging under a single common set of outcomes, controls, and specifications. Three results:

First, aggregate EV charger counts are *positively* associated with neighborhood poverty rate (2.00, p < 0.001). Read naively, this says poorer communities enjoy better charging access. Decomposing by charger type shows the association is entirely composition-driven: it is absent for Level 1 charging (0.002, p = 0.58) and concentrated in Level 2 infrastructure (2.23, p < 0.001), which is sited along commercial and workplace corridors rather than where residents park. The aggregate count measures infrastructure presence in a way that is uncorrelated — and possibly inversely correlated — with usable residential access. Any program evaluated on charger counts can report progress while the access gap widens.

Second, the mismeasurement is technology-specific rather than general. For rooftop solar and battery storage, deployment intensity is *negatively* associated with Black, Hispanic, and Asian population shares, and these associations persist through a ladder of increasingly demanding specifications — additional socioeconomic controls, utility territory fixed effects, county-clustered inference, existing-infrastructure controls, and an electricity demand proxy. Storage shows the deepest and most stable disparities of the three technologies, and they survive conditioning on local solar deployment (Black −1.30, Hispanic −1.00, Asian −1.14, all p < 0.001), meaning the storage gap is not simply downstream of unequal solar access. Because storage is the technology that delivers outage resilience, the communities most exposed to wildfire-related shutoffs are the least likely to hold the asset that buffers them.

Third, the disparities do not reduce to income. Racial and ethnic composition remains statistically associated with deployment after socioeconomic controls, which bears directly on the race-neutral eligibility rules that structure most current DER programs.

**Why we think this fits *Nature Sustainability*.** The core claim is a measurement critique with reach beyond its setting. Charger counts are the standard equity indicator across jurisdictions, and the composition problem we document is a property of how charging infrastructure is sited, not of California specifically. The finding implies that a widely used sustainability metric is systematically misleading, and that equity policy calibrated to one technology will misdiagnose the others — a concrete correction to how distributional progress in the energy transition is tracked. California serves as the proving ground because its data density permits the technology-by-technology comparison, not because the argument is California-specific.

We are explicit that the analysis is area-level and cross-sectional, and we frame the results as conditional associations rather than causal effects. The measurement claim, however, does not depend on causal identification: it rests on the divergence between the aggregate indicator and its disaggregated components.

**Format.** We anticipate roughly [X] words with [N] main-text display items, with the full model ladder, robustness checks, and dataset documentation in Supplementary Information. The harmonized ZIP-level dataset would be released publicly on acceptance; to our knowledge no comparable multi-technology, race-inclusive DER dataset exists at this granularity.

I would be glad to send the full manuscript if this sounds appropriate, and equally glad to hear if it would be better placed elsewhere.

With thanks for your time,

Vineet Nair
[affiliation]
jvineet9@mit.edu

on behalf of [co-author list]

---

## Notes on the draft

**What this version does differently from the manuscript.** The paper currently leads with "race remains significant after income controls" and treats the charger-composition result as the fourth finding. This inquiry inverts that. The race result replicates Sunter et al. (2019) in new technologies — real, but incremental, and a Nature-family editor will read it as such. The charger finding says a metric in active policy use is wrong, which is the kind of claim that survives a generality screen.

**The storage result is doing important work here too** and I've kept it prominent — it's the one place where the paper connects a disparity to a concrete, differentiated benefit (outage resilience), which is what makes it feel consequential rather than descriptive.

**What I deliberately left out:** the wind outcome, the PCA/k-means clustering, and the energy-burden section. All three are supplementary in the paper and would dilute a one-page pitch.

**Be ready for the obvious editor pushback**, which will be some version of "is this California-specific?" Two things strengthen the answer if you can get them before a full submission:

1. **Housing tenure controls** (§2.1 of the review memo). If the race coefficients survive tenure, the finding is much harder to dismiss as a housing-stock artifact — and a Nature Sustainability referee will ask.
2. **Any out-of-state replication of the charger-composition result**, even a rough one. The [AFDC Alternative Fuel Stations database](https://afdc.energy.gov/data_download) is national, free, and includes charger level and location. Reproducing the Level 1 / Level 2 / DC-fast split against ACS poverty in two or three other states would take a few days and would convert the generality claim from an argument into evidence. If the editor bites, this is what I'd do first.

**One honest caveat:** even reframed, this is a competitive ask at ~8–12% acceptance. The inquiry is worth sending because it's free and fast, not because it's likely. Keep the ERSS and Energy Policy paths warm.
