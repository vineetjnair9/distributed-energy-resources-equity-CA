# Stage 4 — bibliography work (Mendeley)

The bibliography is a `MENDELEY_BIBLIOGRAPHY` content control. Editing it in the XML would
be overwritten the next time Mendeley refreshes, so everything below has to be done in
Mendeley and re-inserted with the Word plugin.

Four prose fixes that sit *outside* the Mendeley fields are already applied to
`index.docx` as tracked changes under "Claude (citation fixes)" — see the last section.

---

## 1. Add — Conley (comment 77)

Cited eight times in the text, no bibliography entry.

> T. G. Conley, "GMM estimation with cross sectional dependence," *Journal of
> Econometrics*, vol. 92, no. 1, pp. 1–45, Sep. 1999, doi: 10.1016/S0304-4076(98)00084-0.

---

## 2. Add — data sources (comment 50)

None of these are currently cited. Retrieval URLs for all of them are in
[`data/raw/SOURCES.md`](../data/raw/SOURCES.md).

| Source | Used for | Note |
|---|---|---|
| LBNL *Tracking the Sun* (Barbose et al.) | rooftop PV capacity | confirm which edition/year you pulled |
| California Distributed Generation Statistics (CaliforniaDGStats) | interconnection records, `2023-12-31` snapshot | not named in the manuscript text |
| USGS US Wind Turbine Database (Hoen et al.), doi: 10.5066/F7TX3DN0 | wind turbines | confirm the version you used |
| NASA POWER | GHI, wind speed, HDD/CDD | |
| U.S. Census Bureau, ACS 2023 5-year estimates | demographics, B25024, B25003 | |
| U.S. Census Bureau, TIGER/Line 2023 shapefiles | ZCTA and county boundaries | not named in the manuscript text |
| California Electric Utility Service Territory (SCOUT, ArcGIS) | ZIP-to-utility crosswalk | not named in the manuscript text |

Three of these are not named anywhere in the Methods text, so this needs a sentence naming
the source as well as the citation.

---

## 3. Fix metadata on existing entries

**[8]** — currently `"Demystifying Equity in California's Energy Grid Transition BLOG ENERGY EQUITY."`
with no author or year. It is:

> The Greenlining Institute, "Demystifying Equity in California's Energy Grid Transition,"
> Jul. 25, 2024. https://greenlining.org/2024/demystifying-equity-in-californias-energy-grid-transition/

**[13]** — currently `"Distributed Energy Resources Technical Considerations for the Bulk Power System," 2018`
with no author. It is:

> Federal Energy Regulatory Commission Staff, "Distributed Energy Resources: Technical
> Considerations for the Bulk Power System," Docket No. AD18-10-000, Feb. 2018.

**[16]** — currently `"Distributed Energy Resource Interconnection Roadmap."` with no author
or year. **Needs your decision.** The title matches the DOE i2X *Distributed Energy Resource
Interconnection Roadmap* (January 2025), but §2.5 refers to "CA Public Utilities Commission
(CPUC) roadmap documents." Those are different publications. Confirm which one you cited.

**[19]** — the DOI is malformed: `10.1146/annureveconomics-080614-115630` should be
`10.1146/annurev-economics-080614-115630`.

**[7], [14], [21]** — titles were scraped from PDF cover pages and carry stray capitals and
fragments ("...SEPTEMBER 2020 How High Are Household Energy Burdens?",
"WESTERN INTERSTATE ENERGY BOARD ... Acknowledgements Disclaimer",
"BEFORE THE PUBLIC UTILITIES COMMISSION..."). Clean these in Mendeley before the style
conversion, or they will render as-is.

---

## 4. Merge the duplicate

**[9] and [20] are the same paper** — Light, McIntosh & Stephenson, "Advancing Equity in
Access to Distributed Energy Resources in California," *Journal of Science Policy &
Governance*, 2022, doi: 10.38126/jspg200106. Merge them in Mendeley and re-insert.

---

## 5. Claims with no bibliography entry

- **"Gridworks (2022)"** (§2.5) — no entry exists.
- **"Flexible-DER coordination work at NREL and related DOE planning studies"** (§2.5) — no
  entry exists. Either cite the specific study or drop the sentence.
- **"CA Public Utilities Commission (CPUC) roadmap documents"** (§2.5) — may be entry [16];
  see above.
- "SEIA/Vote Solar community-solar critiques" is covered by entry [21] (Churchill &
  Armstrong). No action.

---

## 6. Already applied to index.docx (tracked)

| Was | Now | Why |
|---|---|---|
| Clean Energy Group (2021) | Tarekegne et al. (2021) | the cited work [17] is Tarekegne, O'Neil & Twitchell |
| Clean Energy Group 2021 | Tarekegne et al. 2021 | same, second mention |
| Borenstein and Bushnell (2016) | Borenstein and Bushnell (2015) | entry [19] is 2015, *Annu. Rev. Econ.* vol. 7 |
| Stokes and Warshaw (2022) | Stokes and Warshaw (2017) | entry [18] is 2017, *Nat. Energy* vol. 2 |

If you meant to cite Clean Energy Group's own storage-equity work rather than the Tarekegne
article, reject that pair of changes and add a Clean Energy Group entry instead.

---

## Note on the Brockway attribution

`AUDIT.md` and `audit_v3.md` flag §2.4 as misattributing hosting-capacity constraints to
"Brockway et al. (2021)" when entry [11] was said to be Brockway & Callaway (2022) on
community solar. **That is not true of the current file.** Entry [11] is Brockway, Conde &
Callaway, "Inequitable access to distributed energy resources due to grid infrastructure
limits in California," *Nat. Energy* 6(9), 2021 — the hosting-capacity paper, correctly
cited. No action needed.
