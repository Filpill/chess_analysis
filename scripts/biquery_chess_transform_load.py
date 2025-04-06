import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # The usual
    import sys
    import json
    import pyarrow
    import pandas_gbq
    import numpy as np
    import pandas as pd
    import datetime as dt
    import marimo as mo
    from typing import List

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
    from general_func import generate_games_dataframe
    from general_func import compare_sets_and_return_non_matches
    from gcs_func import list_files_in_gcs
    from gcs_func import download_content_from_gcs
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
        download_content_from_gcs,
        dt,
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
        storage,
        sys,
    )


@app.cell
def _(initialise_cloud_logger):
    bucket_name = "chess-api"
    project_id = "checkmate-453316"
    dataset_name = "chess_data"
    table_name = "games"
    location = "EU"

    dataset_id = f"{project_id}.{dataset_name}"
    table_id = f"{project_id}.{dataset_name}.{table_name}"
    logger = initialise_cloud_logger(project_id)
    return (
        bucket_name,
        dataset_id,
        dataset_name,
        location,
        logger,
        project_id,
        table_id,
        table_name,
    )


@app.cell
def _(
    check_bigquery_dataset_exists,
    check_bigquery_table_exists,
    create_bigquery_dataset,
    create_bigquery_table,
    dataset_id,
    location,
    schema,
    table_id,
    time_partitioning_field,
):
    if check_bigquery_dataset_exists(dataset_id) == False:
        create_bigquery_dataset(dataset_id, location)

    if check_bigquery_table_exists(table_id) == False:
        create_bigquery_table(table_id, schema, time_partitioning_field)
    return


@app.cell
def _(bucket_name, list_files_in_gcs, logger):
    files_in_gcs = list_files_in_gcs(bucket_name, logger)
    player_data_in_gcs = sorted([obj for obj in files_in_gcs if obj.startswith("player/")])
    return files_in_gcs, player_data_in_gcs


@app.cell
def _(bucket_name, download_content_from_gcs, json, player_data_in_gcs):
    # Sampling data
    gcs_filename = player_data_in_gcs[0]
    gcs_data_endpoint = download_content_from_gcs(gcs_filename, bucket_name)
    gcs_data_endpoint = json.loads(gcs_data_endpoint).get("games")
    return gcs_data_endpoint, gcs_filename


@app.cell
def _(gcs_data_endpoint, generate_games_dataframe):
    df = generate_games_dataframe(gcs_data_endpoint)
    df
    return (df,)


@app.cell
def _(location, logger, query_bq_to_dataframe, table_id):
    # Check BQ for Unique List of Games In the Database
    query = f"""
        SELECT DISTINCT game_id FROM `{table_id}`
    """
    df_unique_games = query_bq_to_dataframe(query, location, logger)
    return df_unique_games, query


@app.cell
def _(compare_sets_and_return_non_matches, df, df_unique_games):
    # Determine games that are missing
    gcs_games = df["game_id"]
    unique_games_currently_in_bq = df_unique_games["game_id"]
    games_missing_from_bq = compare_sets_and_return_non_matches(gcs_games, unique_games_currently_in_bq)
    number_of_missing_games  = len(games_missing_from_bq)
    print(f"Number of missing games from BQ Table {number_of_missing_games}")

    # Filter data to Missing Games Exclusively
    df_filtered = df[df["game_id"].isin(games_missing_from_bq)]
    return (
        df_filtered,
        games_missing_from_bq,
        gcs_games,
        number_of_missing_games,
        unique_games_currently_in_bq,
    )


@app.cell
def _(bigquery):
    # Definining Schema of BigQuery Table
    schema = [
        bigquery.SchemaField(name="game_id",       field_type="INT64",     mode="REQUIRED", description="The ID of the chess game played"),
        bigquery.SchemaField(name="url",           field_type="STRING",    mode="REQUIRED", description="The URL of the chess game played"),
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

        bigquery.SchemaField(name="eco",     field_type="STRING",          mode="REQUIRED", description="The ECO code of the chess opening played"),
        bigquery.SchemaField(name="opening", field_type="STRING",          mode="REQUIRED", description="The name of the chess opening played"),
    ]
    time_partitioning_field ="game_date"


    return schema, time_partitioning_field


@app.cell
def _(append_df_to_bigquery_table, df_filtered, table_id):
    append_df_to_bigquery_table(df_filtered, table_id)
    return


if __name__ == "__main__":
    app.run()
