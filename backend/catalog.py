"""Data dictionary shared by the database loader, the API, and the frontend.

Pandas-free so the web server can import it. populate_tables.py reads these
to build metric observations and evidence text; the API serves them at
/api/definitions for the Definitions page.
"""

METRIC_COLUMNS = {
    "total_population": ("people", "demographic", "ACS 5-year"),
    "population": ("people", "demographic", "ACS 5-year"),
    "median_household_income": ("dollars", "socioeconomic", "ACS 5-year"),
    "poverty_rate": ("share", "socioeconomic", "ACS 5-year"),
    "pct_bachelors_plus": ("share", "education", "ACS 5-year"),
    "pct_black": ("share", "demographic", "ACS 5-year"),
    "pct_hispanic": ("share", "demographic", "ACS 5-year"),
    "pct_asian": ("share", "demographic", "ACS 5-year"),
    "median_housing_value": ("dollars", "housing", "ACS 5-year"),
    "pct_single_family_units": ("share", "housing", "ACS 5-year"),
    "pct_multifamily_units": ("share", "housing", "ACS 5-year"),
    "pct_mobile_home_units": ("share", "housing", "ACS 5-year"),
    "pct_other_housing_units": ("share", "housing", "ACS 5-year"),
    "owner_occupied_rate": ("share", "housing", "ACS 5-year"),
    # rebuild_processed_data.py converts the source kW values to MW before
    # aggregating them by ZCTA.
    "PV_system_size_DC": ("MW", "der_observed", "LBNL Tracking the Sun processed"),
    "storage_capacity_mw": ("MW", "der_observed", "CEC Energy Storage System Survey export"),
    "total_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "level1_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "level2_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "dc_fast_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "wind_capacity_mw": ("MW", "der_observed", "USGS USWTDB"),
    "wind_turbine_count": ("turbines", "der_observed", "USGS USWTDB"),
    "energy_burden_pct": ("share", "energy_affordability", "Energy burden Tableau export"),
    "energy_affordability_index": ("index", "energy_affordability", "Energy burden Tableau export"),
    "energy_affordability_gap": ("dollars", "energy_affordability", "Energy burden Tableau export"),
    "kwh_annual_total": ("kWh", "demand", "Utility electricity usage by ZIP export"),
    "cdd65_2023": ("degree_days", "weather", "NASA POWER gridded centroid"),
    "hdd65_2023": ("degree_days", "weather", "NASA POWER gridded centroid"),
    "ghi_mean_kwh_m2_day_2023": ("kWh/m2/day", "solar_resource", "NASA POWER gridded centroid"),
    "wind_ws10m_mean_2023": ("m/s", "wind_resource", "NASA POWER gridded centroid"),
    "wind_ws50m_mean_2023": ("m/s", "wind_resource", "NASA POWER gridded centroid"),
}

SOURCE_URLS = {
    "ACS 5-year": "https://www.census.gov/programs-surveys/acs",
    "NASA POWER gridded centroid": "https://power.larc.nasa.gov/",
    "LBNL Tracking the Sun processed": "https://emp.lbl.gov/tracking-the-sun/",
    "CEC Energy Storage System Survey export": "https://www.energy.ca.gov/data-reports/energy-almanac/california-electricity-data/california-energy-storage-system-survey",
    "CEC ZEV Infrastructure Stats export": "https://www.energy.ca.gov/data-reports/energy-almanac/zero-emission-vehicle-and-infrastructure-statistics-collection/electric",
    "USGS USWTDB": "https://energy.usgs.gov/uswtdb/data/",
    "Energy burden Tableau export": "https://www.energy.ca.gov/data-reports/data-exploration-tools/energy-equity-indicators-dashboard-collection/deep-dive-energy",
    "Utility electricity usage by ZIP export": (
        "https://www.sce.com/regulatory/regulatory-information/energy-data-reports-compliances; "
        "https://pge-energydatarequest.com/public_datasets; "
        "https://energydata.sdge.com"
    ),
    "Regression model outputs": None,
}

METRIC_INTERPRETATIONS = {
    "pct_black": "This is the non-Hispanic Black share of the population.",
    "pct_hispanic": "This is the Hispanic or Latino share of the population, of any race.",
    "pct_asian": "This is the non-Hispanic Asian share of the population.",
    "poverty_rate": (
        "This is the share of the population for whom poverty status was determined "
        "that is below the poverty line."
    ),
    "pct_bachelors_plus": (
        "This is the share of residents age 25 or older with a bachelor's degree "
        "or higher."
    ),
    "pct_single_family_units": (
        "This is the share of all housing units that are single-family."
    ),
    "pct_multifamily_units": (
        "This is the share of all housing units that are multifamily."
    ),
    "pct_mobile_home_units": (
        "This is the share of all housing units that are mobile homes."
    ),
    "pct_other_housing_units": (
        "This is the share of all housing units in other structures."
    ),
    "owner_occupied_rate": (
        "This is the share of occupied housing units that are owner-occupied."
    ),
    "PV_system_size_DC": (
        "This is aggregate reported PV capacity in the processed Tracking the Sun data."
    ),
    "kwh_annual_total": (
        "This is the electricity usage reported for this ZIP in the utility export. "
        "Coverage is uneven across ZIPs and utilities, so treat it as reported usage "
        "for the accounts present in that export, not as total ZCTA consumption."
    ),
    "energy_burden_pct": (
        "This is the percentage of income spent on energy annually. It is a "
        "ZCTA-level figure and is not a household burden, so it cannot be compared "
        "against the 7% household affordability threshold."
    ),
    "energy_affordability_gap": (
        "The CEC defines this as a population-weighted measure of the gap between "
        "affordable and unaffordable energy burdens; burdens above 7% are treated "
        "as unaffordable in this analysis."
    ),
    "energy_affordability_index": (
        "The CEC index combines the percentile of financial energy burden with the "
        "percentile of disposable income per person to represent household burden "
        "and ability to respond to energy-price changes."
    ),
}

DER_PRIORITY_OUTCOMES = {
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_level1_chargers",
    "y_level2_chargers",
    "y_dc_fast_chargers",
    "y_wind_mw",
}
BURDEN_PRIORITY_OUTCOMES = {
    "energy_burden_pct",
    "energy_affordability_index",
    "log_energy_gap_per_capita",
}


# --- Definitions page ---------------------------------------------------------
# Written from how scripts/rebuild_processed_data.py and notebooks/regression.ipynb
# actually compute each value. "population" in METRIC_COLUMNS is never produced
# by the pipeline, so it has no entry here and never reaches the database.

TERMS = [
    ("ZCTA", "ZIP Code Tabulation Area: the Census Bureau's polygon approximation "
     "of a ZIP code. Every value in the atlas is attached to one five-digit ZCTA."),
    ("Priority", "A screening flag from one regression specification. For adoption "
     "outcomes (solar, storage, chargers, wind capacity) a ZCTA is flagged when its "
     "residual is at or below the 25th percentile of that model's residuals: it has "
     "less than places with similar demographics, housing and climate. For energy "
     "burden and the affordability gap it is flagged at or above the 75th "
     "percentile: burden higher than predicted. For turbine presence it is flagged "
     "when the absolute residual is in the top quarter, in either direction. About "
     "one in four fitted ZCTAs is flagged by each specification by construction."),
    ("Residual", "Observed value minus the value the model predicts, on the "
     "outcome's modeled scale (see Outcomes). Negative means less than predicted."),
    ("Residual rank", "Where a ZCTA's residual falls among all ZCTAs in the same "
     "model's fitted sample, from 0 to 100. The 9th means 91% of places had a larger "
     "residual. Ranks from models with different samples are not directly comparable."),
    ("Specification", "One regression model: a particular outcome, set of control "
     "variables, fixed effects and standard errors. Each outcome is fit with about "
     "25 specifications; agreement across them is the robustness signal."),
    ("Fitted sample", "The ZCTAs a model is estimated on: those with ACS data, at "
     "least 1,000 residents, and reported median income and race shares (about "
     "1,390 of 2,549), minus any rows missing that model's own variables. ZCTAs "
     "outside it have indicators but no model results."),
    ("Screening signal", "A prompt to look closer, not a causal estimate. A residual "
     "says a place differs from statistically similar places, not why."),
]

ACS = "ACS 2023 5-year estimates"
METRIC_DEFINITIONS = {
    "total_population": ("Population", f"Resident population (table B01003). {ACS}."),
    "median_household_income": ("Median household income",
        f"Median household income in dollars (B19013). Suppressed values are left missing. {ACS}."),
    "poverty_rate": ("Poverty rate",
        "Share of people whose poverty status was determined who are below the poverty line (B17001)."),
    "pct_bachelors_plus": ("Bachelor's degree or higher (25+)",
        "Share of residents age 25 or older with a bachelor's, master's, professional or doctoral degree (B15003)."),
    "pct_black": ("Black (non-Hispanic)", "Non-Hispanic Black share of the population (B03002)."),
    "pct_hispanic": ("Hispanic or Latino", "Hispanic or Latino share of the population, of any race (B03002)."),
    "pct_asian": ("Asian (non-Hispanic)", "Non-Hispanic Asian share of the population (B03002)."),
    "median_housing_value": ("Median housing value", "Median value of owner-occupied homes in dollars (B25077)."),
    "pct_single_family_units": ("Single-family units", "Share of all housing units that are detached or attached single-family homes (B25024)."),
    "pct_multifamily_units": ("Multifamily units", "Share of housing units in buildings with two or more units (B25024)."),
    "pct_mobile_home_units": ("Mobile home units", "Share of housing units that are mobile homes (B25024)."),
    "pct_other_housing_units": ("Other housing units", "Share of housing units that are boats, RVs, vans or similar (B25024)."),
    "owner_occupied_rate": ("Owner-occupied", "Share of occupied housing units that are owner-occupied (B25003)."),
    "PV_system_size_DC": ("Rooftop PV capacity (DC)",
        "Total installed solar capacity in MW (DC) from LBNL Tracking the Sun, for California systems "
        "installed by the end of 2023, summed by the ZIP code recorded for each system. All sectors are included."),
    "storage_capacity_mw": ("Storage capacity",
        "Total residential and commercial battery storage in MW (AC) from the CEC Energy Storage System Survey, "
        "for systems of 5 MW or smaller."),
    "total_chargers": ("EV chargers (all)",
        "Public EV charging ports from the CEC ZEV Infrastructure Statistics, assigned to the ZCTA that contains each station's location."),
    "level1_chargers": ("Level 1 chargers", "Public Level 1 (120 V) charging ports, assigned as for all chargers."),
    "level2_chargers": ("Level 2 chargers", "Public Level 2 (240 V) charging ports, assigned as for all chargers."),
    "dc_fast_chargers": ("DC fast chargers", "Public DC fast charging ports, assigned as for all chargers."),
    "wind_capacity_mw": ("Wind capacity", "Total turbine capacity in MW from the USGS Wind Turbine Database, for California turbines in the ZCTA."),
    "wind_turbine_count": ("Wind turbines", "Number of turbines in the USGS Wind Turbine Database within the ZCTA."),
    "energy_burden_pct": ("Energy burden (% of income)",
        "Share of income spent on energy, from the CEC Energy Equity Indicators. A ZCTA-level figure, not a "
        "household burden, so it can't be compared with the 7% household affordability threshold."),
    "energy_affordability_index": ("Affordability index",
        "CEC index from 0 to 100 combining the percentile of energy burden with the percentile of disposable "
        "income per person. Higher means less able to absorb energy-price changes."),
    "energy_affordability_gap": ("Affordability gap",
        "CEC population-weighted gap between affordable and unaffordable energy spending (burdens above 7% "
        "count as unaffordable), as a ZCTA total."),
    "kwh_annual_total": ("Reported electricity use",
        "2023 electricity use in kWh reported by PG&E, SCE and SDG&E, across all customer classes. Missing for "
        "ZCTAs served only by other utilities; some small areas are suppressed for privacy."),
    "cdd65_2023": ("Cooling degree days", "2023 cooling degree days (base 65°F) from NASA POWER daily temperature at the ZCTA's center."),
    "hdd65_2023": ("Heating degree days", "2023 heating degree days (base 65°F) from NASA POWER daily temperature at the ZCTA's center."),
    "ghi_mean_kwh_m2_day_2023": ("Solar irradiance (GHI)", "Mean daily sunlight reaching the ground (global horizontal irradiance) in 2023, from NASA POWER at the ZCTA's center."),
    "wind_ws10m_mean_2023": ("Wind speed at 10 m", "Mean 2023 wind speed at 10 meters from NASA POWER at the ZCTA's center."),
    "wind_ws50m_mean_2023": ("Wind speed at 50 m", "Mean 2023 wind speed at 50 meters from NASA POWER at the ZCTA's center."),
}

# What the model tables' Actual and Predicted columns are measured in.
OUTCOME_DEFINITIONS = {
    "y_pv": ("Rooftop PV", "log(1 + kW of solar per 1,000 residents)"),
    "y_storage": ("Storage", "log(1 + MW of storage per 100,000 residents)"),
    "y_chargers": ("EV chargers", "log(1 + public charging ports per 1,000 residents)"),
    "y_level1_chargers": ("Level 1 chargers", "log(1 + Level 1 ports per 1,000 residents)"),
    "y_level2_chargers": ("Level 2 chargers", "log(1 + Level 2 ports per 1,000 residents)"),
    "y_dc_fast_chargers": ("DC fast chargers", "log(1 + DC fast ports per 1,000 residents)"),
    "y_wind_mw": ("Wind capacity", "log(1 + MW of wind per 100,000 residents)"),
    "any_turbines": ("Turbine presence", "1 if the ZCTA has any wind turbine, else 0 (linear probability model)"),
    "energy_burden_pct": ("Energy burden", "Share of income spent on energy (0 to 1), untransformed"),
    "log_energy_gap_per_capita": ("Affordability gap", "log(1 + affordability gap per resident)"),
}

CORE_TERMS = "log median income, Black, Hispanic and Asian shares, and poverty rate"
# Every specification adds to the core terms unless it says otherwise.
SPECIFICATIONS = [
    ("Model 1 baseline (climate controls)", f"Core terms ({CORE_TERMS}) plus the outcome's climate control: solar irradiance for PV; heating and cooling degree days for storage and chargers; 50 m wind speed for wind; all three for burden."),
    ("Model 2A (add bachelors)", "Model 1 plus the bachelor's-degree share."),
    ("Model 2B (add housing value)", "Model 1 plus log median housing value."),
    ("Model 2C (add housing structure)", "Model 1 plus multifamily, mobile-home and other housing shares (single-family is the reference)."),
    ("Model 2D (add housing structure and tenure)", "Model 2C plus the owner-occupied share."),
    ("Model 3A (HDD + CDD)", "Core terms with heating and cooling degree days as the climate control."),
    ("Model 3B (temp only)", "Core terms with mean 2023 temperature as the climate control."),
    ("Model 3C (GHI only)", "Core terms with solar irradiance as the climate control (identical to Model 1 for PV)."),
    ("Model 4 interactions (centered)", "Model 1 with mean-centered income and race terms plus income × race interactions."),
    ("Model 4R interactions (centered, no poverty control)", "Model 4 without the poverty rate."),
    ("Model 5 utility FE", "Model 1 plus a fixed effect for the serving utility."),
    ("Model 5C clustered SEs by county", "Model 5 with standard errors clustered by county."),
    ("Model 6A lat and lon", "Core terms plus latitude and longitude, without climate controls."),
    ("Model 6B county fe", "Core terms plus county fixed effects, without climate controls."),
    ("No County FE + clustered SEs (county)", "Model 1 with standard errors clustered by county."),
    ("Model 7 (infrastructure controls, outcome-safe)", "Model 1 plus existing energy infrastructure (power plant, storage and wind capacity, turbine count), leaving out the outcome itself."),
    ("Model 7 (per-capita infrastructure controls)", "Model 7 with the infrastructure controls per 100,000 residents."),
    ("Model 8 add demand proxy", "Model 1 plus log reported electricity use."),
    ("Model 9 + pv control (most controlled)", "Storage only: core terms, degree days, electricity use, bachelor's share, plant and wind capacity per capita, and rooftop PV."),
    ("Model 9A (predicting burden)", "Burden outcomes only: race shares, electricity use, all climate controls, and PV, storage and charger adoption; income and poverty are left out on purpose."),
    ("Model C1 (core, common sample)", "Model 1 on a common sample shared by models C1–C5, S and O, so the ladder compares like with like."),
    ("Model C2 (+ education, housing value)", "C1 plus bachelor's share and log housing value."),
    ("Model C3 (+ housing structure, tenure)", "C2 plus housing-structure shares and owner-occupied share."),
    ("Model C4 (+ utility FE)", "C3 plus utility fixed effects."),
    ("Model C5 (+ county FE, county-clustered SEs)", "C4 plus county fixed effects with county-clustered errors; climate controls dropped."),
    ("Model S (saturated confounders)", "The same model as C5, kept under a second label."),
    ("Model O (over-controlled: + demand and infrastructure)", "C5 plus electricity use and the Model 7 infrastructure controls; deliberately over-controlled as a bound."),
]

STANDARD_ERRORS = "Heteroskedasticity-robust (HC1) unless a specification says clustered by county."
