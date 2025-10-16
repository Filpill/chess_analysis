"""
Chess Game Data Transformation Functions

Functions for transforming and loading chess game data from GCS to BigQuery.
"""

import re
import json
import numpy as np
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from gcp_common import (
    download_content_from_gcs,
    delete_gcs_object,
    query_bq_to_dataframe,
    log_printer,
)


def script_date_endpoint_selection(bq_load_settings):
    """
    Select date endpoint for BigQuery load based on script settings.

    Args:
        bq_load_settings: Dictionary with script_setting and optional manual_date_endpoint

    Returns:
        String in format "YYYY/MM"
    """
    if bq_load_settings.get("script_setting") in 'prod':
        date_last_month = date.today() - relativedelta(months=1)
        return datetime.strftime(date_last_month, "%Y/%m")

    if bq_load_settings.get("script_setting") in ['backfill','test', 'dev']:
         return bq_load_settings.get("manual_date_endpoint")


def extract_last_url_component(url):
    """
    Extract the last component of a URL path.

    Args:
        url: URL string

    Returns:
        Last component of URL path
    """
    return url.split("/")[-1]


def convert_unix_ts_to_date(unix_ts):
    """
    Convert Unix timestamp to datetime.

    Args:
        unix_ts: Unix timestamp (integer)

    Returns:
        Datetime object
    """
    return datetime.fromtimestamp(unix_ts)


def compare_sets_and_return_non_matches(col1, col2):
    """
    Compare two sets and return items in col1 that are not in col2.

    Args:
        col1: First collection
        col2: Second collection

    Returns:
        List of non-matching items from col1
    """
    col1 = set(col1)
    col2 = set(col2)
    non_matching = list((col1 - col2))
    return non_matching


def extract_eco_url_from_pgn(pgn, logger):
    """
    Extract ECO URL from PGN string.

    Args:
        pgn: PGN string
        logger: Cloud logging logger instance

    Returns:
        ECO URL string or "ECO Not Found"
    """
    match = re.search(r'\[ECOUrl\s+"([^"]+)"\]', pgn)
    if match:
        eco_url = match.group(1)
        return eco_url
    else:
        return "ECO Not Found"
        log_printer("ECO URL not found.", logger)


def return_missing_data_list(bq_datapoint, table_id, local_list, location, logger):
    """
    Query BigQuery to find missing datapoints not yet in the table.

    Args:
        bq_datapoint: Column name to query
        table_id: Full BigQuery table ID
        local_list: List of local datapoints
        location: BigQuery location (e.g., 'EU', 'US')
        logger: Cloud logging logger instance

    Returns:
        List of missing datapoints
    """
    # Check BQ for Unique List of Datapoints In the Database
    query = f"""
        SELECT DISTINCT {bq_datapoint} FROM `{table_id}`
    """

    log_printer(f"Querying List Of Unique {bq_datapoint} Already Landing in BigQuery: {query}", logger)
    df_bq_unique = query_bq_to_dataframe(query, location, logger)

    # Determine datapoints that are missing from BigQuery Table
    missing_from_bq = compare_sets_and_return_non_matches(local_list, df_bq_unique[bq_datapoint])
    log_printer(f"Number of {bq_datapoint} from local list: {len(local_list)}", logger)
    log_printer(f"Number of missing {bq_datapoint} from BQ Table: {len(missing_from_bq)}", logger)

    return missing_from_bq


def gcs_action_taken_dict(gcs_filename, action_taken, logger):
    """
    Create dictionary tracking action taken on GCS object.

    Args:
        gcs_filename: GCS filename path
        action_taken: Action taken (e.g., "Loaded", "Deleted")
        logger: Cloud logging logger instance

    Returns:
        Dictionary with GCS interaction metadata
    """
    # Dictionary to determine what action was taken when handling the GCS data
    # To load into BQ table later
    _, _, _, year, month = gcs_filename.split("/")

    interaction_dict = {
        "gcs_endpoint" :  gcs_filename,
        "gcs_game_month" : datetime(int(year), int(month), 1),
        "gcs_object_interaction_dt" : datetime.now(),
        "action_taken" : action_taken
    }

    return interaction_dict


def generate_games_dataframe(gcs_filename: str, bucket_name: str, logger):
    """
    Download and transform chess game data from GCS into DataFrame.

    Args:
        gcs_filename: GCS filename path
        bucket_name: GCS bucket name
        logger: Cloud logging logger instance

    Returns:
        Tuple of (DataFrame, interaction_dict) or (None, interaction_dict) if empty
    """
    # Download Data From GCS and Store into DataFrame
    content = download_content_from_gcs(gcs_filename, bucket_name ,logger)
    data_dict = json.loads(content).get("games")
    df = pd.DataFrame(data_dict)

    # Define column order for dataframe
    columns = [
        "game_id",
        "url",
        "game_date",
        "ingested_dt",
        "time_control",
        "end_time",
        "rated",
        "time_class",
        "rules",
        "white",
        "black",
        "accuracies",
        "eco",
        "opening"
    ]

    # Create empty column for any datapoints that don't exist
    if "accuracies" not in df.columns:
        df["accuracies"] = dict()

    if "eco" not in df.columns:
        df["eco"] = np.nan

    if "pgn" not in df.columns:
        df["pgn"] = np.nan

    # Transformations for non-zero length
    if len(df) > 0:

        # Apply Transformations
        df["eco"] = df.apply(
            lambda row: row["eco"] if pd.notna(row["eco"]) else (
                extract_eco_url_from_pgn(row["pgn"], logger) if pd.notna(row["pgn"]) else "ECO Not Found"
            ),
            axis=1
        )

        df["opening"] = df["eco"].apply(
            lambda x: extract_last_url_component(x).replace("-", " ") if pd.notna(x) else "ECO Not Found"
        )

        df["game_id"] = df["url"].apply(lambda x: extract_last_url_component(x))
        df["game_date"] = pd.to_datetime(df["end_time"], unit="s").dt.strftime('%Y-%m-%d')
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
        df["ingested_dt"] = pd.to_datetime(datetime.now())

        # Fixing Types
        df["game_id"] = df["game_id"].astype(int)

        # Generate interaction dict
        interaction_dict = gcs_action_taken_dict(gcs_filename, "Loaded", logger)

        return df[columns], interaction_dict

    # Ammend action to take for GCS data that is empty (prepping for deletion)
    if len(df) == 0 :

        # Generate interaction dict
        interaction_dict = gcs_action_taken_dict(gcs_filename, "Deleted", logger)

        return None, interaction_dict


def deletion_interaction_list_handler(df, bucket_name, logger):
    """
    Delete GCS objects marked for deletion.

    Args:
        df: DataFrame with action_taken column
        bucket_name: GCS bucket name
        logger: Cloud logging logger instance
    """
    df_to_banish_to_shadow_realm = df[df['action_taken']=="Deleted"]

    for gcs_filename in df_to_banish_to_shadow_realm["gcs_endpoint"]:
         log_printer(f"No data in following GCS endpoint: {gcs_filename}", logger)
         delete_gcs_object(gcs_filename, bucket_name, logger)
