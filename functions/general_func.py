import pandas as pd
import datetime as dt

def extract_last_url_component(url):
    return url.split("/")[-1]

def convert_unix_ts_to_date(unix_ts):
    return dt.datetime.fromtimestamp(unix_ts)

def generate_games_dataframe(gcs_data_endpoint: dict):
    df = pd.json_normalize(gcs_data_endpoint)
    df["game_id"] = df["url"].apply(lambda x: extract_last_url_component(x))
    df["opening"] = df["eco"].apply(lambda x: extract_last_url_component(x).replace("-"," "))
    df["game_date"] = pd.to_datetime(df['end_time'], unit="s").dt.strftime('%Y-%m-%d')   
    
    columns = [
        "game_id",
        "url",
        "game_date",
        "time_control",
        "end_time",
        "rated",
        "time_class",
        "rules",
        "white.uuid",
        "white.username",
        "white.rating",
        "white.result",
        "accuracies.white",
        "black.uuid",
        "black.username",
        "black.rating",
        "black.result",
        "accuracies.black",
        "eco",
        "opening"
    ]
    
    return df[columns]
