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


def nih_exporter_table_combined(folder, pattern, start_year):
    """
    Combine the year based spreadsheets from the NIH exporter into a single DataFrame.
    """
    df_combined = None
    for year in list(range(int(start_year), 2024)):
        # The RePORTER_PUB_C_1995.csv file is giving this error:
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc in position 259615: invalid start byte
        # so I am replacing  problematic characters
        df = pd.read_csv(os.path.join(folder, pattern + str(year) + '.csv'), encoding_errors='replace')
        if df_combined is None:
            df_combined = df
        else:
            # NOTE: getting a lot of DtypeWarning: Columns (#,#) have mixed types, consider specifying the dtype for
            # each column within each folder
            df_combined = pd.concat([df_combined, df], ignore_index=True)

    return df_combined


def standardize_nih_exporter_project_names(df):
    """
    Get the names from the NIH projects data into FIRST MIDDLE LAST format and remove the '(contact)' entries
    """
    # Split the names based on the ';' delimiter
    df['name_list'] = df['PI_NAMEs'].str.split(';')
    # Expand the DataFrame so each name gets its own row
    df = df.explode('name_list')
    # Strip whitespace and '(contact)' from names
    df['name_list'] = df['name_list'].str.replace(r'\s*\(contact\)', '', regex=True).str.strip()
    # Split the name into <LAST> and <FIRST> <MIDDLE>, splitting at the first comma only
    df[['last_name', 'first_middle_name']] = df['name_list'].str.split(',', n=1, expand=True)
    # Combine <FIRST> <MIDDLE> <LAST> into the desired format
    df['project_formatted_name'] = df['first_middle_name'].str.strip() + ' ' + df['last_name'].str.strip()

    return df


def standardize_nih_exporter_publication_names(df):
    """
    Get the names from the NIH publications data into FIRST MIDDLE LAST format
    """
    # Split the names based on the ';' delimiter
    df['name_list'] = df['AUTHOR_LIST'].str.split(';')
    # Expand the DataFrame so each name gets its own row
    df = df.explode('name_list')
    # Split the name into <LAST> and <FIRST> <MIDDLE>, splitting at the first comma only
    df[['last_name', 'first_middle_name']] = df['name_list'].str.split(',', n=1, expand=True)
    # Combine <FIRST> <MIDDLE> <LAST> into the desired format
    df['publication_formatted_name'] = df['first_middle_name'].str.strip() + ' ' + df['last_name'].str.strip()

    return df


def get_nih_exporter_project_leader_names(projects_folder, start_year):
    """
    Get a list of the PIs names who were granted funding from NIH.
    """
    # Get the list of PIs from the NIH exporter
    df_projects = nih_exporter_table_combined(projects_folder, 'RePORTER_PRJ_C_FY', start_year)
    df_projects = standardize_nih_exporter_project_names(df_projects)
    df_projects = df_projects.drop_duplicates(subset='project_formatted_name')

    # Prepare a list of formatted names from df_projects
    project_formatted_names = df_projects['project_formatted_name'].str.lower().dropna().tolist()
    print(f'# project_formatted_names = {len(project_formatted_names)}')

    return project_formatted_names


def get_nih_exporter_publication_authors(publications_folder, start_year):
    """
    Get a list of the authors who have published against NIH projects.
    """
    # NOTE: have to manually rename the publication and links spreadsheets after 2021 to remove the FY in front of YYYY
    df_publications = nih_exporter_table_combined(publications_folder, 'RePORTER_PUB_C_', start_year)
    df_publications = standardize_nih_exporter_publication_names(df_publications)
    df_publications = df_publications.drop_duplicates(subset='publication_formatted_name')

    publication_formatted_names = df_publications['publication_formatted_name'].str.lower().dropna().tolist()
    print(f'# publication_formatted_names = {len(publication_formatted_names)}')

    return publication_formatted_names


def best_jaro_winkler_match(user_name, nih_names):
    """
    Compute the best Jaro-Winkler match score and the corresponding project name.
    """
    best_score = 0
    best_match_name = None
    for nih_name in nih_names:
        score = JaroWinkler.similarity(user_name, nih_name)
        if score > best_score:
            best_score = score
            best_match_name = nih_name

    return best_score, best_match_name


def check_nih_exporter_hits(df_pn_users, projects_folder, publications_folder, start_year):
    """
    Search for matches between the PhysioNet user names and the names in the projects and publications data from the NIH
    exporter.
    """
    # Get the list of PhysioNet users
    # df_pn_users = df_pn_users.iloc[1:11].copy() # For looping through fewer users during debug
    user_names = df_pn_users['full_name'].str.lower().dropna().tolist()
    print(f'# user names = {len(user_names)}')

    # Get the list of project lead names from NIH exporter
    project_formatted_names = get_nih_exporter_project_leader_names(projects_folder, start_year)

    # Get the list of authors from publications associated with the NIH exporter projects
    publication_formatted_names = get_nih_exporter_publication_authors(publications_folder, start_year)

    # Time how long the fuzzy matching takes
    t0 = time.time()

    # Matching against the project DataFrame list
    print('Searching for PhysioNet users who are PIs that were awarded grants in NIH Exporter...')
    project_results = Parallel(n_jobs=-1)(
        delayed(best_jaro_winkler_match)(user_name, project_formatted_names) for user_name in tqdm(user_names))
    project_best_scores, project_best_match_names = zip(*project_results)
    df_pn_users.loc[:, 'nih_project_best_score'] = project_best_scores
    df_pn_users.loc[:, 'nih_project_best_match_name'] = project_best_match_names

    # Matching against the publication DataFrame list
    print('Searching for PhysioNet users who are published authors from NIH Exporter...')
    publication_results = Parallel(n_jobs=-1)(
        delayed(best_jaro_winkler_match)(user_name, publication_formatted_names) for user_name in tqdm(user_names))
    publication_best_scores, publication_best_match_names = zip(*publication_results)
    df_pn_users.loc[:, 'nih_publication_best_score'] = publication_best_scores
    df_pn_users.loc[:, 'nih_publication_best_match_name'] = publication_best_match_names

    t1 = time.time()
    print(f'Finished in {t1 - t0} seconds')

    return df_pn_users

