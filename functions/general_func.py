import pandas as pd
from datetime import datetime

def extract_last_url_component(url):
    return url.split("/")[-1]

def convert_unix_ts_to_date(unix_ts):
    return dt.datetime.fromtimestamp(unix_ts)

def compare_sets_and_return_non_matches(col1, col2):
    col1 = set(col1)
    col2 = set(col2)
    non_matching = list((col1 - col2))
    return non_matching

def generate_games_dataframe(gcs_data_endpoint: dict):
    df = pd.DataFrame(gcs_data_endpoint)
    df["game_id"] = df["url"].apply(lambda x: extract_last_url_component(x))
    df["opening"] = df["eco"].apply(lambda x: extract_last_url_component(x).replace("-"," "))
    df["game_date"] = pd.to_datetime(df["end_time"], unit="s").dt.strftime('%Y-%m-%d')   
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
    df["ingested_dt"] = pd.to_datetime(datetime.now()) 

    # Fixing Types
    df["game_id"] = df["game_id"].astype(int)
    
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
    
    return df[columns]
