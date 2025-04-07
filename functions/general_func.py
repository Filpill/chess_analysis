import re
import sys
import json
import pandas as pd
from datetime import datetime
from gcs_func import download_content_from_gcs
from gcs_func import delete_gcs_object
from bq_func  import query_bq_to_dataframe

def extract_last_url_component(url):
    return url.split("/")[-1]

def convert_unix_ts_to_date(unix_ts):
    return dt.datetime.fromtimestamp(unix_ts)

def compare_sets_and_return_non_matches(col1, col2):
    col1 = set(col1)
    col2 = set(col2)
    non_matching = list((col1 - col2))
    return non_matching

def extract_eco_url_from_pgn(pgn):
    match = re.search(r'\[ECOUrl\s+"([^"]+)"\]', pgn)
    if match:
        eco_url = match.group(1)
        print("ECO URL Extracted From PGN Data:", eco_url)
        return eco_url
    else:
        print("ECO URL not found.")

def return_missing_data_list(bq_datapoint, table_id, local_list, location, logger):
    
    # Check BQ for Unique List of Datapoints In the Database
    query = f"""
        SELECT DISTINCT {bq_datapoint} FROM `{table_id}`
    """
    
    print(f"Querying List Of Unique {bq_datapoint} Already Landing in BigQuery: {query}")
    df_bq_unique = query_bq_to_dataframe(query, location, logger)
    
    # Determine datapoints that are missing from BigQuery Table
    missing_from_bq = compare_sets_and_return_non_matches(local_list, df_bq_unique[bq_datapoint])
    print(f"Number of {bq_datapoint} from local list: {len(local_list)}")
    print(f"Number of missing {bq_datapoint} from BQ Table: {len(missing_from_bq)}")

    return missing_from_bq


def generate_games_dataframe(gcs_filename: str, bucket_name: str, logger):

    # Download Data From GCS and Store into DataFrame
    content = download_content_from_gcs(gcs_filename, bucket_name)
    data_dict = json.loads(content).get("games")
    df = pd.DataFrame(data_dict)

    # Define column order for dataframe
    columns = [
        "game_id",
        "url",
        "gcs_endpoint",
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
        #"opening"
    ]

    # Create empty column for any datapoints that don't exist
    if "accuracies" not in df.columns:
        df["accuracies" ] = dict()

    if "eco" not in df.columns:
        df["eco"] = df["pgn"].apply(lambda x: extract_eco_url_from_pgn(x))

    #if "eco" in df.columns:
        #df["opening"] = df["eco"].apply(lambda x: extract_last_url_component(x).replace("-"," "))

    # Transformations for non-zero length
    if len(df) > 0: 

        # Apply Transformations
        df["gcs_endpoint"] = gcs_filename
        df["game_id"] = df["url"].apply(lambda x: extract_last_url_component(x))
        df["game_date"] = pd.to_datetime(df["end_time"], unit="s").dt.strftime('%Y-%m-%d')
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
        df["ingested_dt"] = pd.to_datetime(datetime.now()) 

        # Fixing Types
        df["game_id"] = df["game_id"].astype(int)

    # Delete GCS data if no data found for date period
    if len(df) == 0 :
        print(f"No data in following GCS endpoint: {gcs_filename}")
        delete_gcs_object(gcs_filename, bucket_name, logger)
    
    return df[columns]
