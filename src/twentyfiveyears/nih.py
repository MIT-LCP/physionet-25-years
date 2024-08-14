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

    if string.lower() in [suffix.lower() for suffix in name_suffixes]:
        return True
    else:
        return False


def standardize_physionet_names(df_names, first_name_as_initial=False):
    """
    Split the PhysioNet user names into FIRST LAST format. Remove suffixes.
    """
    df = pd.DataFrame()
    # Split the first_names strings, remove suffixes, and take only the first part
    df['first_name'] = df_names['first_names'].apply(
    lambda x: next((part for part in x.split() if not is_suffix(part)), x.split()[0]) if pd.notna(x) and x else None)

    # Split the last_name strings, remove suffixes
    df['last_name'] = df_names['last_name'].apply(
        lambda x: ' '.join([part for part in x.split() if not is_suffix(part)]) if pd.notna(x) and x else None)

    if first_name_as_initial:
        df['first_initial'] = df['first_name'].apply(lambda x: x[0] if x else '')
        df['physionet_name'] = df["first_initial"].str.strip() + " " + df["last_name"].str.strip()
    else:
        df['physionet_name'] = df["first_name"].str.strip() + " " + df["last_name"].str.strip()

    return df['physionet_name']


def standardize_pi_names(df, first_name_as_initial=False):
    """
    Get the names from the NIH projects data into FIRST LAST format
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

    # Split into LAST and FIRST names
    df["last_name"] = df["name_list"].str.split(",", n=1).str[0].str.strip()
    df["first_name"] = df["name_list"].str.split(",", n=1).str[1].str.strip().str.split().str[0]

    # Remove suffixes
    df["last_name_no_suffix"] = df['last_name'].apply(
        lambda x: ' '.join([part for part in x.split() if not is_suffix(part)]) if pd.notna(x) and x else None)
    df["first_name_no_suffix"] = df['first_name'].apply(
    lambda x: next((part for part in x.split() if not is_suffix(part)), x.split()[0]) if pd.notna(x) and x else None)

    if first_name_as_initial:
        df['first_initial'] = df['first_name_no_suffix'].apply(lambda x: x[0] if x else '')
        df['project_formatted_name'] = df["first_initial"].str.strip() + " " + df["last_name_no_suffix"].str.strip()
    else:
        df['project_formatted_name'] = df["first_name_no_suffix"].str.strip() + " " + df[
            "last_name_no_suffix"].str.strip()

    return df


def standardize_author_names(df, first_name_as_initial=False):
    """
    Get the names from the NIH publications data into FIRST LAST format and remove suffixes.
    """
    # Split the names based on the ';' delimiter
    df["name_list"] = df["AUTHOR_LIST"].str.split(";")

    # Expand the DataFrame so each name gets its own row
    df = df.explode("name_list")

    # Split into LAST and FIRST names
    df["last_name"] = df["name_list"].str.split(",", n=1).str[0].str.strip()
    df["first_name"] = df["name_list"].str.split(",", n=1).str[1].str.strip().str.split().str[0]

    # Remove suffixes
    df["last_name_no_suffix"] = df['last_name'].apply(
        lambda x: ' '.join([part for part in x.split() if not is_suffix(part)]) if pd.notna(x) and x else None)
    df["first_name_no_suffix"] = df['first_name'].apply(
    lambda x: next((part for part in x.split() if not is_suffix(part)), x.split()[0]) if pd.notna(x) and x else None)

    if first_name_as_initial:
        df['first_initial'] = df['first_name_no_suffix'].apply(lambda x: x[0] if x else '')
        df['publication_formatted_name'] = df["first_initial"].str.strip() + " " + df["last_name_no_suffix"].str.strip()
    else:
        df['publication_formatted_name'] = df["first_name_no_suffix"].str.strip() + " " + df[
            "last_name_no_suffix"].str.strip()

    return df


def get_physionet_users(path, person_map, first_name_as_initial):
    """
    Get a DataFrame of the PhysioNet users
    """
    # Read in the PhysioNet users data
    df = pd.read_csv(path, low_memory=False)
    # Add person_id column to the users table
    df_physionet_users = pd.merge(df, person_map, left_on='user_id', right_on='physionet_id')
    # Standardize the PhysioNet name into FIRST LAST
    df_physionet_names = df_physionet_users[['first_names', 'last_name']].copy()
    standardized_names = standardize_physionet_names(df_physionet_names, first_name_as_initial)
    df_physionet_users['physionet_name'] = standardized_names.str.lower()
    # Only keep the columns we need from the users table
    df_physionet_users = df_physionet_users[['person_id', 'physionet_name']].copy()

    return df_physionet_users


def get_investigators(df_projects, first_name_as_initial):
    """
    Get a list of the PIs names who were granted funding from NIH.
    """
    df_investigators = standardize_pi_names(df_projects, first_name_as_initial)
    df_investigators = df_investigators.drop_duplicates(subset="project_formatted_name")

    # Prepare a list of formatted names from projects
    project_formatted_names = (
        df_investigators["project_formatted_name"].str.lower().dropna().tolist()
    )

    return project_formatted_names


def get_authors(df_publications, first_name_as_initial):
    """
    Get a list of the authors who have published against NIH projects.

    # NOTE: have to manually rename the publication and links spreadsheets
    # after 2021 to remove the FY in front of YYYY
    """
    df_authors = standardize_author_names(df_publications, first_name_as_initial)
    df_authors = df_authors.drop_duplicates(
        subset="publication_formatted_name"
    )

    publication_formatted_names = (
        df_authors["publication_formatted_name"].str.lower().dropna().tolist()
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
