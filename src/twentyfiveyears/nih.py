"""
nih.py

This module contains functions used to prepare and process data
extracted from NIH Exporter: https://reporter.nih.gov/exporter
"""
import os
import time

import pandas as pd
from tqdm import tqdm
from joblib import Parallel, delayed
from rapidfuzz.distance import JaroWinkler


def combine_exporter_tables(folder, pattern, start_year):
    """
    Combine the year based spreadsheets from the NIH exporter into a
    single DataFrame.
    """
    df_combined = None

    for year in list(range(int(start_year), 2024)):
        # The RePORTER_PUB_C_1995.csv file is giving this error:
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc in position
        # 259615: invalid start byte
        # so I am replacing  problematic characters
        df = pd.read_csv(
            os.path.join(folder, pattern + str(year) + ".csv"),
            dtype=str, encoding_errors="replace",
        )
        if df_combined is None:
            df_combined = df
        else:
            df_combined = pd.concat([df_combined, df], ignore_index=True)

    return df_combined


def is_suffix(string):
    """
    Check to see if a given string is a common name suffix
    """
    name_suffixes = [
        "Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV", "V",
        "Esq.", "Esq", "Ph.D.", "PhD", "M.D.", "MD", "D.D.S.", "DDS", "J.D.", "JD",
        "M.B.A.", "MBA", "D.O.", "DO", "R.N.", "RN", "CPA", "LL.M.", "LLM",
        "DVM", "DVM", "DDS", "DDS", "PE", "PE", "FACS", "FACS", "MPH", "MPH",
        "D.Min.", "DMin", "M.Div.", "MDiv", "Ed.D.", "EdD", "Psy.D.", "PsyD",
        "B.Sc.", "BSc", "M.Sc.", "MSc",
        "D.Litt.", "DLitt", "O.D.", "OD", "MSW", "MSW", "MSN", "MSN",
        "DC", "DC", "PA-C", "PAC", "RN-BSN", "RNBSN", "CFA", "CFA"
    ]
    # Removed these since they are often names and aren't common for researchers "B.A.", "BA", "M.A.", "MA",

    if string in name_suffixes:
        return True
    else:
        return False


def standardize_physionet_names(df):
    """
    Split the PhysioNet user names into FIRST MIDDLE LAST format, keeping last name together if it contains a connector
    word. Remove suffixes.
    """
    # Common connectors
    connectors = ["de", "da", "y", "del", "di", "van", "von", "la", "le"]
    # Vectorized splitting of names
    split_names = df['full_name'].str.split()
    # Extract FIRST names
    df['first_name'] = split_names.str[0]

    # Extract LAST names considering connectors
    last_names = []
    filtered_names = []
    for names in split_names:
        # Remove suffixes from the last parts
        filtered_parts = [name for name in names if not is_suffix(name)]

        # Build last name considering connectors
        found_connector = False
        for part in filtered_parts:
            if part.lower() in connectors and filtered_parts and len(filtered_parts) > 3:  # If the part is a connector
                found_connector = True

        # The last name will be the last element in last_name_parts
        last_names.append(' '.join(filtered_parts[-3:]) if found_connector else filtered_parts[-1])
        # Build a list of filtered names to be used below
        filtered_names.append(filtered_parts)

    df['last_name'] = last_names

    # Extract MIDDLE names by removing FIRST and LAST from the filtered parts
    df['middle_name'] = [
        ' '.join(
            part for part in parts if part not in (first, *last.split())
        )
        for parts, first, last in zip(filtered_names, df['first_name'], df['last_name'])
    ]

    # Replace hyphens with spaces in middle_name
    df['middle_name_split'] = df['middle_name'].str.replace('-', ' ', regex=False)
    # Convert middle names to first initials without punctuation, and ensure no NaN values
    df['middle_initials'] = df['middle_name_split'].str.split().str.join(' ').str.extractall(r'(\b\w)')[0].groupby(
        level=0).agg(' '.join).fillna('')

    # Concatenate the processed columns back into a single column without extra spaces
    df['physionet_name'] = df[['first_name', 'middle_initials', 'last_name']].fillna('').agg(
        ' '.join, axis=1).str.replace(' +', ' ', regex=True).str.strip()

    return df


def standardize_pi_names(df):
    """
    Get the names from the NIH projects data into FIRST MIDDLE LAST format
    and remove suffixes and the '(contact)' entries
    """
    # Split the names based on the ';' delimiter
    df["name_list"] = df["PI_NAMEs"].str.split(";")

    # Expand the DataFrame so each name gets its own row
    df = df.explode("name_list")

    # Strip whitespace and '(contact)' from names
    df["name_list"] = (
        df["name_list"].str.replace(r"\s*\(contact\)", "", regex=True).str.strip()
    )

    # Split the name into <LAST> and <FIRST> <MIDDLE>, splitting at the first comma only
    df[["last_name", "first_middle_name"]] = df["name_list"].str.split(
        ",", n=1, expand=True
    )
    # Combine <FIRST> <MIDDLE> <LAST> into the desired format
    df["project_formatted_name"] = (
        df["first_middle_name"].str.strip() + " " + df["last_name"].str.strip()
    )

    return df


def standardize_author_names(df):
    """
    Get the names from the NIH publications data into FIRST MIDDLE LAST format and remove suffixes.
    """
    # Split the names based on the ';' delimiter
    df["name_list"] = df["AUTHOR_LIST"].str.split(";")

    # Expand the DataFrame so each name gets its own row
    df = df.explode("name_list")

    # Split the name into <LAST> and <FIRST> <MIDDLE>, splitting at the first
    # comma only
    df[["last_name", "first_middle_name"]] = df["name_list"].str.split(
        ",", n=1, expand=True
    )

    # Combine <FIRST> <MIDDLE> <LAST> into the desired format
    df["publication_formatted_name"] = (
        df["first_middle_name"].str.strip() + " " + df["last_name"].str.strip()
    )

    return df


def get_physionet_users(path, person_map):
    """
    Get a DataFrame of the PhysioNet users
    """

    # Read in the PhysioNet users data
    physionet_users = pd.read_csv(path, low_memory=False)
    # Add person_id column to the users table
    physionet_users = pd.merge(physionet_users, person_map, left_on='user_id', right_on='physionet_id')
    # Standardize the PhysioNet name into FIRST MIDDLE LAST
    physionet_users = standardize_physionet_names(physionet_users)
    # Only keep the columns we need from the users table
    physionet_users = physionet_users[['person_id', 'physionet_name']].copy()
    # Use lower case for the users name
    physionet_users['physionet_name'] = physionet_users['physionet_name'].str.lower()

    return physionet_users


def get_investigators(projects):
    """
    Get a list of the PIs names who were granted funding from NIH.
    """
    projects = standardize_pi_names(projects)
    projects = projects.drop_duplicates(subset="project_formatted_name")

    # Prepare a list of formatted names from projects
    project_formatted_names = (
        projects["project_formatted_name"].str.lower().dropna().tolist()
    )

    return project_formatted_names


def get_authors(publications):
    """
    Get a list of the authors who have published against NIH projects.

    # NOTE: have to manually rename the publication and links spreadsheets
    # after 2021 to remove the FY in front of YYYY
    """
    publications = standardize_author_names(publications)
    publications = publications.drop_duplicates(
        subset="publication_formatted_name"
    )

    publication_formatted_names = (
        publications["publication_formatted_name"].str.lower().dropna().tolist()
    )

    return publication_formatted_names


def best_jaro_winkler_match(user_name, nih_names):
    """
    Compute the best Jaro-Winkler match score and the corresponding
    project name.
    """
    best_score = 0
    best_match_name = None

    for nih_name in nih_names:
        score = JaroWinkler.similarity(user_name, nih_name)
        if score > best_score:
            best_score = score
            best_match_name = nih_name

    return best_score, best_match_name


def link_users(physionet_users, nih_users, match_group, limit=None):
    """
    Search for matches between the PhysioNet user names and the names in
    the projects and publications data from the NIH exporter.
    """
    t0 = time.time()
    user_names = physionet_users["physionet_name"].str.lower().dropna().tolist()

    # Set limit when testing
    if limit:
        physionet_users = physionet_users[:limit]
        nih_users = nih_users[:limit]
        user_names = user_names[:limit]

    if match_group == "investigators":

        results = Parallel(n_jobs=-1)(
            delayed(best_jaro_winkler_match)(user_name, nih_users)
            for user_name in tqdm(user_names)
        )
        best_scores, best_match_names = zip(*results)
        physionet_users.loc[:, "matched_investigator_score"] = best_scores
        physionet_users.loc[:, "matched_investigator_name"] = best_match_names

    elif match_group == "authors":

        results = Parallel(n_jobs=-1)(
            delayed(best_jaro_winkler_match)(user_name, nih_users)
            for user_name in tqdm(user_names)
        )
        best_scores, best_match_names = zip(*results)
        physionet_users.loc[:, "matched_author_score"] = best_scores
        physionet_users.loc[:, "matched_author_name"] = best_match_names

    t1 = time.time()
    print(f"Finished in {t1 - t0} seconds")

    return physionet_users
