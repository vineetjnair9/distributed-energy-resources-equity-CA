#%% Combining Data
## Making Database with counties to zip-codes and zip_codes to counties
import geopandas as gpd
import pandas as pd
import re
import spacy
from rapidfuzz import fuzz, process

# Load the Excel files (no header as we’ll rename columns explicitly)
county_fips = pd.read_excel('New County and State FIPS.xlsx')

# Explicitly set column names for clarity
county_fips.columns = ["FIPS CODE", "COUNTY"]

# Initialize dictionaries
us_dict = {}
name_to_fips = {}

# Process county data
current_state = None
for index, row in county_fips.iterrows():
    fips_code = str(row["FIPS CODE"]).strip().lower() if pd.notna(row["FIPS CODE"]) else None
    county_name = str(row["COUNTY"]).strip().lower() if pd.notna(row["COUNTY"]) else None

    name_to_fips[county_name] = fips_code
    # Display the first row for verification
    if index == 0:
        print(f"First row - FIPS Code: {fips_code}, County: {county_name}")

    # Check if the FIPS code represents a state (ends in '000')
    if fips_code and fips_code[-3:] == "000":
        current_state = fips_code  # Update the current state FIPS
        if current_state not in us_dict:
            us_dict[current_state] = []  # Initialize county set for the state
    else:
        # Only add if current_state is valid and county_name is not 'nan'
        if current_state and county_name != 'nan':
            us_dict[current_state].append(fips_code)  # Add county FIPS code to the current state in the US dictionary
        else:
            print(f"Warning: County '{county_name}' with FIPS '{fips_code}' is missing or has no valid current state assigned.")

# Output the results for verification
print("FIPS to County:", name_to_fips)
print("US Dictionary:", us_dict)

#%%
## Creating functions to unpack CSV and XLSX files
def read_csv_or_excel(filename, csv = True):
    # a function to return a dataframe of a csv or xlsx file
    if csv:
        data_frame = pd.read_csv(filename)
    else:
        data_frame = pd.read_excel(filename)
    data_frame.columns = data_frame.columns.str.strip().str.lower()

    return data_frame

# OPTION 1
def filter_columns(keywords):
    # filters the columns based on keyword
    filter = "|".join([re.escape(keyword) for keyword in keywords])
    # Select columns containing either "power" or "capacity"
    df_filtered = df.filter(regex=filter)

    return df_filtered

# Load the spaCy model
nlp = spacy.load("en_core_web_md")

# OPTION 2
# Function to find similar columns
def find_similar_columns(dataframe, keywords, fuzzy_threshold=0, semantic_threshold=0.1):
    # Dictionary to store matching columns for each keyword
    matches = {}
    for keyword in keywords:
        # Step 1: Fuzzy matching to find potential column matches
        fuzzy_matches = process.extract(keyword, dataframe.columns, scorer=fuzz.token_sort_ratio, limit=None)
        # Step 2: Filter fuzzy matches by threshold
        potential_matches = [col for col, score, _ in fuzzy_matches if score >= fuzzy_threshold]
        # Step 3: Use spaCy to filter potential matches by semantic similarity
        keyword_doc = nlp(keyword)
        max_match = 0
        final_match = None
        for col in potential_matches:
            similarity_mat = nlp(col).similarity(keyword_doc)
            if similarity_mat >= semantic_threshold and similarity_mat > max_match:
                max_match = nlp(col).similarity(keyword_doc)
                final_match = col

        matches[keyword] = final_match

    return matches

# Adding data to big data frame
solar_xlsx = "Solar_Footprints.xlsx"
solar_dataframe = read_csv_or_excel(solar_xlsx, False)
power_plant_csv = "Power_Plant.csv"
power_plant_dataframe = read_csv_or_excel(power_plant_csv)
dataframes = [solar_dataframe, power_plant_dataframe]

# intializes columns of data frame
columns = ["DER_type", "capacity_KW", "power_KW", "county", "status"]
df = pd.DataFrame(columns=columns)


for dataframe in dataframes:
    dataframe['county'] = dataframe['county'].str.replace(r'\bcounty\b', '', case=False, regex=True)
    # Find similar columns
    similar_columns = find_similar_columns(dataframe, columns)
    # Remove duplicates from similar_columns to avoid duplicate labels
    unique_similar_columns = {k: v for k, v in similar_columns.items() if list(similar_columns.values()).count(v) == 1}

    # Skip if no columns matched uniquely
    if not unique_similar_columns:
        print("No unique matching columns found for this dataframe, skipping.")
        continue

    # filter and rename and reindex columns
    temp_df = dataframe.rename(columns=unique_similar_columns)[list(unique_similar_columns.values())]
    temp_df = temp_df.rename(columns={v: k for k, v in unique_similar_columns.items()}).reindex(columns=columns)

    # fills any missing columns in temp_df with None
    temp_df = temp_df.fillna({col: None for col in columns if col not in temp_df.columns})
    temp_df.dropna(axis=1, how='all', inplace=True)

    # reset inidices and concatenate
    temp_df.reset_index(drop=True, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df = pd.concat([df, temp_df], ignore_index=True)

    # name_to_fips = {k: v for k, v in name_to_fips.items()}
    df["county"] = df["county"].str.lower()

    df['county_fips'] = df['county'].map(name_to_fips)


# Display the empty DataFrame
print(df)

#%%
"""
New Idea:
- make separate databases mapping to different county fips
  with different databases representing different data files
  all having their own dataframe
- putting dataframe in dictionaries pointing to
  their corresponding der type
"""
"""
// Define data structure for FIPS codes
"""
# just a reminder of what maps name to fips
name_to_fips = name_to_fips
# maps states to fips codes in state
us_dict = us_dict

# Initialize empty dictionary for county dataframes
county_dataframes = {}


"""
1.  Define the FIPS data structure:
  - Create a dictionary with state FIPS codes as keys
  - For each state, create a nested dictionary with 'counties' as the key
  - For each county, store its FIPS code, list of DER types, and an empty list for data frames
"""
for state, counties in us_dict.items():
    county_dataframes[state] = {}
    for county in counties:
        county_dataframes[state][county] = {
            "Batteries": [], "Electric Vehicles": [], "Solar": [], "Wind": [], "Power Plants": []
            }
# print(county_dataframes)

type_to_data = {
    "Batteries": [],
    "Electric Vehicles": [],
    "Solar": [solar_dataframe],
    "Wind": [],
    "Power Plants": [power_plant_dataframe]
    }

for dataframe in dataframes:

    for index, row in df.iterrows():
        for col_name, value in row.items():
            if "county" in col_name.lower() or "fips" in col_name.lower():
                pass

"""
2.  Initialize the final mapping structure:
  - Create an empty dictionary to store the final mapping

3.  Populate the data frames:
  - For each state in the FIPS data structure:
    - For each county in the state:
      - For each DER type in the county:
        - Create a new data frame with placeholder data and the DER type
        - Add this data frame to the county's list of data frames
4.  Construct the final mapping:
  - For each state FIPS code in the FIPS data structure:
    - Create a new dictionary in the final mapping for this state
    - For each county FIPS code in the state:
        - Create a new dictionary in the state's dictionary for this county
        - For each DER type in the county:
            - Create a new list in the county's dictionary for this DER type
            - Add all data frames from the county that match this DER type to the list
5. Function to access data:
 - Define a function that takes state FIPS, county FIPS, and DER type as input
 - Return the list of data frames for the specified state, county, and DER type

6. Error handling:
 - Add checks to ensure the requested state, county, and DER type exist in the structure
 - Return appropriate error messages if any part of the request is invalid

7. (Optional) Add functions for data manipulation:
Create a function to add new DER types to a county
Create a function to add new data frames to a specific DER type in a county
Create a function to remove DER types or data frames

8. (Optional) Data summary function:
Create a function that provides a summary of the data structure
Include counts of states, counties, DER types, and data frames

9. (Optional) Data export function:
Create a function to export the data structure to a file format (e.g., JSON, CSV)

10. (Optional) Data import function:
Create a function to import data from external sources and populate the structure

11. Main program flow:
Initialize the FIPS data structure
Populate the data frames
Construct the final mapping
Provide examples of accessing and manipulating the data using the created functions
"""

#%%
# Initialize a dictionary to store data by county FIPS
county_data = {}

# Process each dataframe
for der_type, dataframes in type_to_data.items():
    for dataframe in dataframes:
        # Find the column that contains county or FIPS information
        county_col = next((col for col in dataframe.columns if 'county' in col.lower() or 'fips' in col.lower()), None)

        if county_col is None:
            print(f"No county or FIPS column found in dataframe for {der_type}")
            continue

        # Process each row in the dataframe
        for _, row in dataframe.iterrows():
            county_identifier = row[county_col]
            print(county_identifier, county_col)

            # If the identifier is a county name, convert it to FIPS
            if 'county' in county_col.lower() and type(county_identifier) == str:
                county_identifier = county_identifier.lower().strip()
                fips = name_to_fips.get(county_identifier)
            else:
                fips = county_identifier

            if fips is None:
                print(f"No FIPS code found for {county_identifier}")
                continue

            # Initialize the county data if it doesn't exist
            if fips not in county_data:
                county_data[fips] = {}

            # Initialize the DER type data if it doesn't exist
            if der_type not in county_data[fips]:
                county_data[fips][der_type] = []

            # Add the row data to the county's DER type list
            county_data[fips][der_type].append(row.to_dict())




# Now, populate the county_dataframes structure with the collected data
for state, counties in us_dict.items():
    for county in counties:
        if county in county_data:
            for der_type in ["Batteries", "Electric Vehicles", "Solar", "Wind", "Power Plants"]:
                if der_type in county_data[county]:
                    print("poop", county_data[county][der_type])
                    county_dataframes[state][county][der_type] = pd.DataFrame(county_data[county][der_type])
print(county_dataframes)
print(county_data)
