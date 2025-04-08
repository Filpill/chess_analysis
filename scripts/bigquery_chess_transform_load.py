import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # The Usual
    import sys
    import json
    import pyarrow
    import pandas_gbq
    import numpy as np
    import pandas as pd
    import marimo as mo
    from typing import List

    # Warning Suppression
    import warnings
    warnings.filterwarnings("ignore", message="Discarding nonzero nanoseconds in conversion.")

    # Google Libraries
    import google.cloud.logging as cloud_logging
    from google.cloud import bigquery
    from google.cloud import storage
    from google.cloud.exceptions import NotFound

    # Local Libraries
    sys.path.append(f"./inputs")
    sys.path.append(f"./functions")
    from shared_func import initialise_cloud_logger

    from general_func import extract_last_url_component
    from general_func import convert_unix_ts_to_date
    from general_func import return_missing_data_list
    from general_func import generate_games_dataframe
    from general_func import compare_sets_and_return_non_matches

    from gcs_func import list_files_in_gcs
    from gcs_func import download_content_from_gcs
    from gcs_func import delete_gcs_object

    from bq_func import check_bigquery_dataset_exists
    from bq_func import check_bigquery_table_exists
    from bq_func import create_bigquery_dataset
    from bq_func import create_bigquery_table
    from bq_func import append_df_to_bigquery_table
    from bq_func import query_bq_to_dataframe
    return (
        List,
        NotFound,
        append_df_to_bigquery_table,
        bigquery,
        check_bigquery_dataset_exists,
        check_bigquery_table_exists,
        cloud_logging,
        compare_sets_and_return_non_matches,
        convert_unix_ts_to_date,
        create_bigquery_dataset,
        create_bigquery_table,
        delete_gcs_object,
        download_content_from_gcs,
        extract_last_url_component,
        generate_games_dataframe,
        initialise_cloud_logger,
        json,
        list_files_in_gcs,
        mo,
        np,
        pandas_gbq,
        pd,
        pyarrow,
        query_bq_to_dataframe,
        return_missing_data_list,
        storage,
        sys,
        warnings,
    )


@app.cell
def _(initialise_cloud_logger):
    script_setting = "test"
    test_volume  = 15 # Max number of files to be downloaded during testing mode
    dev_endpoint_testcase = "player/hoshor/games/2024/12"
    #dev_endpoint_testcase = "player/laurent2003/games/2024/12"

    bucket_name   = "chess-api"
    project_id    = "checkmate-453316"
    dataset_name  = "chess_data"
    table_name    = "games"
    location      = "EU"
    date_endpoint = "2024/12"

    dataset_id = f"{project_id}.{dataset_name}"
    table_id = f"{project_id}.{dataset_name}.{table_name}"
    logger = initialise_cloud_logger(project_id)
    logger.log_text(f"Initialising Transform Script to Incrementally Insert data into BigQuery | Project: {project_id} | Bucket: {bucket_name} | Script Setting: {script_setting} | date_endpoint: {date_endpoint} ", severity="INFO")
    return (
        bucket_name,
        dataset_id,
        dataset_name,
        date_endpoint,
        dev_endpoint_testcase,
        location,
        logger,
        project_id,
        script_setting,
        table_id,
        table_name,
        test_volume,
    )


@app.cell
def _(
    bigquery,
    check_bigquery_dataset_exists,
    check_bigquery_table_exists,
    create_bigquery_dataset,
    create_bigquery_table,
    dataset_id,
    location,
    table_id,
):
    # Definining Schema of BigQuery Table
    schema = [
        bigquery.SchemaField(name="game_id",       field_type="INT64",     mode="REQUIRED", description="The ID of the chess game played"),
        bigquery.SchemaField(name="url",           field_type="STRING",    mode="REQUIRED", description="The URL of the chess game played"),
        bigquery.SchemaField(name="gcs_endpoint",  field_type="STRING",    mode="REQUIRED", description="The path to data endpoint inside GCS bucket"),
        bigquery.SchemaField(name="game_date",     field_type="DATE",      mode="REQUIRED", description="The date of the chess game played"),
        bigquery.SchemaField(name="ingested_dt",   field_type="TIMESTAMP", mode="REQUIRED", description="The timestamp of the ingested data"),
        bigquery.SchemaField(name="time_control",  field_type="STRING",    mode="REQUIRED", description="The time control of the chess game played"),
        bigquery.SchemaField(name="end_time",      field_type="INTEGER",   mode="REQUIRED", description="The timestamp at which the game ended"),
        bigquery.SchemaField(name="rated",         field_type="BOOL",      mode="REQUIRED", description="Flag for identifying if the game was rated"),
        bigquery.SchemaField(name="time_class",    field_type="STRING",    mode="REQUIRED", description="The time classification for the game"),
        bigquery.SchemaField(name="rules",         field_type="STRING",    mode="REQUIRED", description="The chess ruleset of the respective chess game"),

        bigquery.SchemaField(name="white", field_type="RECORD", mode="REQUIRED", description="White player details", fields=[
                bigquery.SchemaField(name="uuid",     field_type="STRING",     mode="REQUIRED", description="The unique identifier of a player's username"),
                bigquery.SchemaField(name="username", field_type="STRING",     mode="REQUIRED", description="The username of the chess player"),
                bigquery.SchemaField(name="rating",   field_type="INT64",      mode="REQUIRED", description="The rating of the chess player at the time of the game"),
                bigquery.SchemaField(name="result",   field_type="STRING",     mode="REQUIRED", description="The result of the respective chess game"),
        ]),

        bigquery.SchemaField(name="black", field_type="RECORD", mode="REQUIRED", description="Black player details", fields=[
                bigquery.SchemaField(name="uuid",     field_type="STRING",     mode="REQUIRED", description="The unique identifier of a player's username"),
                bigquery.SchemaField(name="username", field_type="STRING",     mode="REQUIRED", description="The username of the chess player"),
                bigquery.SchemaField(name="rating",   field_type="INT64",      mode="REQUIRED", description="The rating of the chess player at the time of the game"),
                bigquery.SchemaField(name="result",   field_type="STRING",     mode="REQUIRED", description="The result of the respective chess game"),
        ]),

        bigquery.SchemaField(name="accuracies", field_type="RECORD", mode="NULLABLE", description="Player accuracies", fields=[
                bigquery.SchemaField(name="white", field_type="FLOAT64",       mode="NULLABLE", description="White - The accuracy of the respective chess game"),
                bigquery.SchemaField(name="black", field_type="FLOAT64",       mode="NULLABLE", description="Black - The accuracy of the respective chess game"),
        ]),

        bigquery.SchemaField(name="eco",     field_type="STRING",          mode="REQUIRED", description="The Encyclopedia of Chess Openings URL for the chess opening played"),
        bigquery.SchemaField(name="opening", field_type="STRING",          mode="REQUIRED", description="The name of the chess opening played"),
    ]
    time_partitioning_field ="game_date"

    if check_bigquery_dataset_exists(dataset_id) == False:
        create_bigquery_dataset(dataset_id, location)

    if check_bigquery_table_exists(table_id) == False:
        create_bigquery_table(table_id, schema, time_partitioning_field)
    return schema, time_partitioning_field


@app.cell
def _(bucket_name, date_endpoint, list_files_in_gcs, logger):
    # List player objects from GCS
    files_in_gcs = list_files_in_gcs(bucket_name, logger)
    list_player_endpoints = sorted([obj for obj in files_in_gcs if obj.startswith("player/")])
    list_filtered_game_endpoints = sorted([obj for obj in list_player_endpoints if obj.endswith(f"{date_endpoint}")])
    return files_in_gcs, list_filtered_game_endpoints, list_player_endpoints


@app.cell
def _(
    list_filtered_game_endpoints,
    location,
    logger,
    return_missing_data_list,
    table_id,
):
    # Determine which endpoints are missing from BQ and q
    endpoints_missing_from_bq = return_missing_data_list("gcs_endpoint", table_id, list_filtered_game_endpoints, location, logger)
    return (endpoints_missing_from_bq,)


@app.cell
def _(
    bucket_name,
    dev_endpoint_testcase,
    endpoints_missing_from_bq,
    generate_games_dataframe,
    logger,
    pd,
    script_setting,
    test_volume,
):
    if script_setting == "dev":
        df_combined = generate_games_dataframe(dev_endpoint_testcase, bucket_name, logger)
        print("Downloaded test case to dataframe")

    # Download game data from each endpoint in GCS and store dataframes into list
    if script_setting in ("prod", "test"):
        list_of_game_dfs = []
        for i, gcs_filename in enumerate(endpoints_missing_from_bq):

            # When in test setting, this will apply a limiter to the volume of data being
            if script_setting == "test" and i == test_volume:
                break

            df = generate_games_dataframe(gcs_filename, bucket_name, logger)
            if df is not None:
                list_of_game_dfs.append(df)

        df_combined = pd.concat(list_of_game_dfs)
        print("Transformed all downloads into list of dataframes and concatenated together")
    return df, df_combined, gcs_filename, i, list_of_game_dfs


@app.cell
def _(df_combined, location, logger, return_missing_data_list, table_id):
    # Determine missing game_id's from BigQuery and filter list accordingly
    games_missing_from_bq = return_missing_data_list("game_id", table_id, df_combined["game_id"], location, logger)
    df_filtered = df_combined[df_combined["game_id"].isin(games_missing_from_bq)]
    games_filtered_away = len(df_combined) - len(df_filtered)
    print(f"\nNumber of game_id's filtered away from combined dataframe: {games_filtered_away}")

    # De-duplication process for game_id's in scenarios where where players inside batch play each other
    df_deduplicated = df_filtered.drop_duplicates(subset="game_id", keep="first")
    duplicates_removed = len(df_filtered) - len(df_deduplicated)
    print(f"Number of duplicate game_id's removed from combined dataframe: {duplicates_removed}")
    return (
        df_deduplicated,
        df_filtered,
        duplicates_removed,
        games_filtered_away,
        games_missing_from_bq,
    )


@app.cell
def _(df_deduplicated):
    df_deduplicated
    return


@app.cell
def _(append_df_to_bigquery_table, df_deduplicated, table_id):
    append_df_to_bigquery_table(df_deduplicated, table_id)
    return


if __name__ == "__main__":
    app.run()
