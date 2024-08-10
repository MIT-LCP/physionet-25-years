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


def standardize_pi_names(df):
    """
    Get the names from the NIH projects data into FIRST MIDDLE LAST format
    and remove the '(contact)' entries
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
    Get the names from the NIH publications data into FIRST MIDDLE LAST format
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


def get_pi_names(projects):
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
