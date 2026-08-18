A harmonized, ZIP-code-level panel of distributed energy resources across California,
built so that deployment can be compared across technologies rather than one at a time.

Distributed energy data is scattered across agencies, geographies and vintages: rooftop
solar sits with one program, storage with another, EV charging in a dashboard export,
and none of them share a common set of controls. This record assembles them into a
single 2023 panel keyed to Census ZIP Code Tabulation Areas, so questions that require
comparing technologies — who has storage but not solar, where charging is dense but
residential access is not — can be asked directly.

Coverage. 2,549 California ZCTAs by 50 columns. Rooftop solar PV capacity, battery
storage capacity, EV charging counts split by Level 1, Level 2 and DC fast, EV
registrations, wind capacity and turbine counts, and power-plant capacity. Each is joined
to American Community Survey 2023 five-year demographics and socioeconomics, exhaustive
housing structure and tenure, NASA POWER climate and solar resource, utility service
territory, annual electricity demand from all three investor-owned utilities, and
California Energy Commission energy burden and affordability measures.

Using it. Geography is the 2023 ZCTA, keyed by `zip_code` as a five-digit string —
read it as text, not as an integer. Coverage is not universal on every column: housing
structure and tenure are complete for 1,717 ZCTAs and energy burden for 1,669, so expect
missingness rather than assuming a balanced panel. The four housing-structure shares are
exhaustive and sum to one, with single-family the natural omitted reference.

Beyond the panel. The record also carries the 347 coefficient tables behind every
figure in the accompanying paper, so results can be redrawn without refitting; the raw
inputs that have no stable public download URL, including LBNL's Tracking the Sun file;
the exact Census API response and its query manifest, preserved because the Census serves
current vintages rather than historical snapshots; and the pinned environment the pipeline
runs under. `CHECKSUMS.sha256` covers every file.

Underlying sources retain their own citation requirements, in particular LBNL Tracking the
Sun, the USGS US Wind Turbine Database, CaliforniaDGStats, NASA POWER, the California
Energy Commission and the US Census Bureau. `SOURCES.md` documents each with its origin.
