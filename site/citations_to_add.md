# Bibliography worklist

The document half is done. What remains has to happen in the Mendeley library itself,
because that is what a Refresh in Mendeley Cite reads from.

**Why the library matters even though the document already looks right.** Mendeley Cite
v3 stores each citation's CSL JSON inside the document, and I patched three entries there
(commit `533b0c4`). Those edits render correctly today. But Refresh re-fetches every item
by ID from your library, so anything still wrong in the library comes back. Fix the library
once and the document stays fixed.

---

## 1. Import the new references — one step

[`mendeley_import.ris`](mendeley_import.ris) holds all eight new references. In Mendeley:
**File → Import → RIS**, or drag the file into the library.

| Reference | For |
|---|---|
| Conley (1999), *J. Econometrics* 92(1), 1–45 | the spatial HAC standard errors, cited 8× with no entry |
| USGS US Wind Turbine Database, doi 10.5066/F7TX3DN0 | wind turbines |
| LBNL *Tracking the Sun* public data file | rooftop PV capacity |
| CaliforniaDGStats interconnection report | PV and storage interconnections |
| Census ACS 2023 5-year | demographics, B25024, B25003 |
| Census TIGER/Line 2023 | ZCTA and county boundaries |
| NASA POWER | irradiance, wind speed, degree days |
| California Electric Utility Service Territories (SCOUT) | ZIP-to-utility crosswalk |

Two need a look before you cite them:

- **Tracking the Sun** is entered with LBNL as institutional author. The report series is
  authored by Barbose, Darghouth et al.; confirm the 2024 edition's author list if you want
  a person-level citation.
- **USWTDB** is continuously versioned. Record the version you actually downloaded.

---

## 2. Fix four items in the library

The first three I already corrected inside the document, so these edits make the library
agree rather than changing what you see.

**"Demystifying Equity in California's Energy Grid Transition BLOG ENERGY EQUITY"**
- Author: The Greenlining Institute
- Year: 2024 (25 July)
- Title: drop the trailing `BLOG ENERGY EQUITY`
- URL: https://greenlining.org/2024/demystifying-equity-in-californias-energy-grid-transition/

**"Distributed Energy Resources Technical Considerations for the Bulk Power System"**
- Author: Federal Energy Regulatory Commission Staff
- Year: 2018 (February)
- Title: add the colon — `Distributed Energy Resources: Technical Considerations…`
- Number: Docket No. AD18-10-000

**Borenstein & Bushnell, "The U.S. Electricity Industry after 20 Years of Restructuring"**
- DOI: `10.1146/annurev-economics-080614-115630` (currently `annureveconomics`, missing a hyphen)

**"Distributed Energy Resource Interconnection Roadmap" — needs you to identify it.**
I could not resolve this one. The title matches the DOE i2X *Distributed Energy Resource
Interconnection Roadmap* (January 2025), but §2.5 of the manuscript refers to "CA Public
Utilities Commission (CPUC) roadmap documents." Those are different publications. Open the
entry in Mendeley and check its URL or attached PDF — that will settle it — then fill in the
author and year to match.

---

## 3. Merge the duplicate

**Light, McIntosh & Stephenson (2022)**, "Advancing Equity in Access to Distributed Energy
Resources in California," *J. Science Policy & Governance*, doi 10.38126/jspg200106, exists
twice in the library with different IDs, which is why it appears as both **[9]** and **[20]**.

Select both and merge them in Mendeley. This is the one change that renumbers the
bibliography: after merging, everything from [20] onward shifts down by one, in the entry
list and in every in-text number. Mendeley handles that on Refresh — do not renumber by hand.

---

## 4. Then refresh once

After the import, the four fixes and the merge, hit **Refresh** in Mendeley Cite. That
rewrites the bibliography and every citation number from the library in one pass, and
supersedes the patches I made inside the document.

---

## 5. Still to write into the manuscript

Adding references to the library does not cite them. Three data sources are never named in
the Methods text at all — **CaliforniaDGStats**, **TIGER/Line**, and the **SCOUT utility
territories layer** — so they need a sentence as well as a citation. Conley is already
named in the text eight times and only needs its citation inserted.

Two claims in §2.5 still have no entry behind them:

- **"Gridworks (2022)"**
- **"Flexible-DER coordination work at NREL and related DOE planning studies"**

Either cite something specific or cut the sentence.

---

## Already done in the document

| Change | Commit |
|---|---|
| Clean Energy Group (2021) → Tarekegne et al. (2021), matching citation [17] | `533b0c4` |
| Borenstein and Bushnell (2016) → (2015) in prose | `533b0c4` |
| Stokes and Warshaw (2022) → (2017) in prose | `533b0c4` |
| Entries [8], [13], [19] repaired in both the CSL JSON and the rendered text | `533b0c4` |

**On the Brockway attribution:** `AUDIT.md` and `audit_v3.md` flag §2.4 as misattributing
hosting-capacity constraints. That is not true of the current file — entry [11] is Brockway,
Conde & Callaway, *Nat. Energy* 6(9), 2021, the hosting-capacity paper, correctly cited.
No action.
