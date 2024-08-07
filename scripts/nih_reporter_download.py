import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

# Define the base URLs for the NIH RePORTER APIs
PROJECTS_URL = "https://api.reporter.nih.gov/v2/projects/search"
PUBLICATIONS_URL = "https://api.reporter.nih.gov/v2/publications/search"

# Function to fetch data with pagination
def fetch_data(url, params):
    all_data = []
    while True:
        response = requests.post(url, json=params)
        if response.status_code == 200:
            data = response.json()
            results = data['results']
            all_data.extend(results)

            if len(results) < params['limit'] or params['offset'] >= 9999:
                break

            params['offset'] += params['limit']
        else:
            print("Failed to fetch data:", response.status_code, response.text)
            break
        time.sleep(1)  # Wait for 1 second after each request
    return all_data

# Function to fetch data for multiple years, states, and quarterly ranges
def fetch_data_by_years_states_quarters(base_url, base_params, years, states):
    all_data = []
    for year in years:
        print(f'Processing year {year}')
        for state in states:
            start_date = datetime(year, 1, 1)
            while start_date.year == year:
                from_date = start_date.strftime("%Y-%m-%d")
                end_date = (start_date + relativedelta(months=3) - timedelta(days=1)).strftime("%Y-%m-%d")
                # print(f"Fetching data for fiscal year: {year}, state: {state}, date range: {from_date} to {end_date}")
                params = base_params.copy()
                params['criteria']['fiscal_years'] = [year]
                params['criteria']['org_state'] = [state]
                params['criteria']['project_start_date'] = {
                    "from_date": from_date,
                    "to_date": end_date
                }
                params['offset'] = 0
                data = fetch_data(base_url, params)
                all_data.extend(data)
                start_date += relativedelta(months=3)

    return all_data


# Function to fetch publication data for multiple project numbers
def fetch_publications_for_projects(project_numbers):
    publications = []
    print(f"Number of projects: {len(project_numbers)}")
    print("Collecting publications associated with projects...")
    for i in tqdm(range(0, len(project_numbers), 500)):
        batch = project_numbers[i:i+500]
        publications_params = {
            "criteria": {
                "core_project_nums": batch
            },
            "offset": 0,
            "limit": 500  # Adjust the limit based on your needs
        }
        batch_publications = fetch_data(PUBLICATIONS_URL, publications_params)
        publications.extend(batch_publications)
        # print(f"Batch start = {i}")
        time.sleep(1)

    return publications


# Define the parameters for the projects API request
projects_params = {
    "criteria": {
        "fiscal_years": [],  # Will be set in the fetch_data_by_years_states_quarters function
        "org_state": [],  # Will be set in the fetch_data_by_years_states_quarters function
        "project_start_date": {},  # Will be set in the fetch_data_by_years_states_quarters function
        "include_active_projects": True  # Include active projects
    },
    "include_fields": [
        "CoreProjectNum",
        "ProjectTitle",
        "PrincipalInvestigators",
        "Organization",
        "ProjectStartDate",
        "ProjectEndDate"
    ],
    "offset": 0,
    "limit": 500  # Adjust the limit based on your needs
}

t0 = time.time()
# Define the fiscal years to fetch
fiscal_years = list(range(1985, 2025))

# Define the states to fetch
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
          "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
          "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# Fetch project data for multiple fiscal years, states, and quarterly ranges
projects = fetch_data_by_years_states_quarters(PROJECTS_URL, projects_params, fiscal_years, states)

# Create a DataFrame from the project data
projects_df = pd.DataFrame(projects)

# Flatten the nested JSON for the Organization column
organization_df = pd.json_normalize(projects_df['organization'])
projects_df = projects_df.drop(columns=['organization']).join(organization_df)

# Flatten the nested JSON for the PrincipalInvestigators column
pi_df = pd.json_normalize(projects_df['principal_investigators'].explode()).groupby(level=0).agg(lambda x: list(x))
pi_df.columns = [f'pi_{col}' for col in pi_df.columns]
projects_df = projects_df.drop(columns=['principal_investigators']).join(pi_df)

# Remove the brackets from principal investigators columns
for col in pi_df.columns:
    projects_df[col] = projects_df[col].apply(lambda x: x[0] if isinstance(x, list) and x else None)

# Reorder columns to have core_project_num as the first column
projects_df = projects_df[['core_project_num'] + [col for col in projects_df.columns if col != 'core_project_num']]

# Save the project data to a CSV file
projects_df.to_csv('nih_projects.csv', index=False)
print("Flattened project data saved to nih_projects.csv")

# Extract project numbers
project_numbers = projects_df['core_project_num'].tolist()

# Fetch publication data associated with the projects
publications = fetch_publications_for_projects(project_numbers)

# Create a DataFrame from the publication data
publications_df = pd.DataFrame(publications)
publications_df.rename(columns={'coreproject': 'core_project_num'}, inplace=True)

# Save the publication data to a CSV file
publications_df.to_csv('nih_publications.csv', index=False)
print("Publication data saved to nih_publications.csv")

t1 = time.time()
total_time = t1 - t0
print("Total time taken:", total_time)
