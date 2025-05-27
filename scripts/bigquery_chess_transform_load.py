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
    from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging

    # Importing Local Functions
    for rel_path in (".", ".."):
        sys.path.append(f"{rel_path}/functions")
        sys.path.append(f"{rel_path}/inputs")

    from shared_func import log_printer
    from shared_func import initialise_cloud_logger

    from transform_func import script_date_endpoint_selection
    from transform_func import extract_last_url_component
    from transform_func import convert_unix_ts_to_date
    from transform_func import return_missing_data_list
    from transform_func import generate_games_dataframe
    from transform_func import compare_sets_and_return_non_matches
    from transform_func import deletion_interaction_list_handler

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
        CloudLoggingHandler,
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
        deletion_interaction_list_handler,
        download_content_from_gcs,
        extract_last_url_component,
        generate_games_dataframe,
        initialise_cloud_logger,
        json,
        list_files_in_gcs,
        log_printer,
        mo,
        np,
        pandas_gbq,
        pd,
        pyarrow,
        query_bq_to_dataframe,
        rel_path,
        return_missing_data_list,
        script_date_endpoint_selection,
        setup_logging,
        storage,
        sys,
        warnings,
    )


@app.cell
def _(
    initialise_cloud_logger,
    json,
    log_printer,
    script_date_endpoint_selection,
):
    # Reading Script Input Variables
    try:
        with open("./inputs/bq_load_settings.json") as f:
            bq_load_settings = json.load(f)
    except FileNotFoundError:
        with open("../inputs/bq_load_settings.json") as f:
            bq_load_settings = json.load(f)

    date_endpoint   = script_date_endpoint_selection(bq_load_settings) # type: ignore
    script_setting  = bq_load_settings.get("script_setting")           # prod/test/dev
    test_volume     = bq_load_settings.get("test_volume")              # For "test" setting Max number of files to be downloaded during testing mode
    dev_testcase    = bq_load_settings.get("dev_testcase")             # Singular endpoint testing
    project_id      = bq_load_settings.get("project_id")
    bucket_name     = bq_load_settings.get("bucket_name")
    dataset_name    = bq_load_settings.get("dataset_name")
    location        = bq_load_settings.get("location")

    dataset_id = f"{project_id}.{dataset_name}"
    logger = initialise_cloud_logger(project_id)

    log_printer(f"Initialising Transform Script to Incrementally Insert data into BigQuery | Project: {project_id} | Bucket: {bucket_name} | Script Setting: {script_setting} | date_endpoint: {date_endpoint}", logger)
    return (
        bq_load_settings,
        bucket_name,
        dataset_id,
        dataset_name,
        date_endpoint,
        dev_testcase,
        f,
        location,
        logger,
        project_id,
        script_setting,
        test_volume,
    )


@app.cell
def _(
    check_bigquery_dataset_exists,
    create_bigquery_dataset,
    dataset_id,
    location,
    logger,
):
    if check_bigquery_dataset_exists(dataset_id, logger) == False:
        create_bigquery_dataset(dataset_id, location)
    return


@app.cell
def _(
    bigquery,
    check_bigquery_table_exists,
    create_bigquery_table,
    dataset_name,
    logger,
    project_id,
):
    # Definining Schema of Loading Completed BigQuery Table
    table_id_loading_completed = f"{project_id}.{dataset_name}.loading_completed"

    schema_loading_completed = [
        bigquery.SchemaField(name="gcs_endpoint",              field_type="STRING",    mode="REQUIRED", description="The path to data endpoint inside GCS bucket"),
        bigquery.SchemaField(name="gcs_game_month",            field_type="DATE",      mode="REQUIRED", description="The month relating to GCS object that was involved in data loading"),
        bigquery.SchemaField(name="gcs_object_interaction_dt", field_type="TIMESTAMP", mode="REQUIRED", description="The timestamp of the interaction of the GCS object that was involved in data loading"),
        bigquery.SchemaField(name="acton_taken",               field_type="STRING",    mode="NULLABLE", description="Action taken when interacting with GCS object"),
    ]
    loading_time_partitioning_field ="gcs_game_month"

    if check_bigquery_table_exists(table_id_loading_completed, logger) == False:
        create_bigquery_table(table_id_loading_completed, schema_loading_completed, logger, loading_time_partitioning_field)
    return (
        loading_time_partitioning_field,
        schema_loading_completed,
        table_id_loading_completed,
    )


@app.cell
def _(
    bigquery,
    check_bigquery_table_exists,
    create_bigquery_table,
    dataset_name,
    logger,
    project_id,
):
    # Definining Schema of Games BigQuery Table
    table_id_games = f"{project_id}.{dataset_name}.games"

    schema_games = [
        bigquery.SchemaField(name="game_id",       field_type="INT64",     mode="REQUIRED", description="The ID of the chess game played"),
        bigquery.SchemaField(name="url",           field_type="STRING",    mode="REQUIRED", description="The URL of the chess game played"),
        bigquery.SchemaField(name="game_date",     field_type="DATE",      mode="REQUIRED", description="The date of the chess game played"),
        bigquery.SchemaField(name="ingested_dt",   field_type="TIMESTAMP", mode="REQUIRED", description="The timestamp of the ingested data"),
        bigquery.SchemaField(name="time_control",  field_type="STRING",    mode="REQUIRED", description="The time control of the chess game played"),
        bigquery.SchemaField(name="end_time",      field_type="INTEGER",   mode="REQUIRED", description="The timestamp at which the game ended"),
        bigquery.SchemaField(name="rated",         field_type="BOOL",      mode="REQUIRED", description="Flag for identifying if the game was rated"),
        bigquery.SchemaField(name="time_class",    field_type="STRING",    mode="REQUIRED", description="The time classification for the game"),
        bigquery.SchemaField(name="rules",         field_type="STRING",    mode="REQUIRED", description="The chess ruleset of the respective chess game"),

        bigquery.SchemaField(name="white",         field_type="RECORD",    mode="REQUIRED", description="White player details", fields=[
                bigquery.SchemaField(name="uuid",       field_type="STRING",     mode="REQUIRED", description="The unique identifier of a player's username"),
                bigquery.SchemaField(name="username",   field_type="STRING",     mode="REQUIRED", description="The username of the chess player"),
                bigquery.SchemaField(name="rating",     field_type="INT64",      mode="REQUIRED", description="The rating of the chess player at the time of the game"),
                bigquery.SchemaField(name="result",     field_type="STRING",     mode="REQUIRED", description="The result of the respective chess game"),
        ]),

        bigquery.SchemaField(name="black",          field_type="RECORD",    mode="REQUIRED", description="Black player details", fields=[
                bigquery.SchemaField(name="uuid",       field_type="STRING",     mode="REQUIRED", description="The unique identifier of a player's username"),
                bigquery.SchemaField(name="username",   field_type="STRING",     mode="REQUIRED", description="The username of the chess player"),
                bigquery.SchemaField(name="rating",     field_type="INT64",      mode="REQUIRED", description="The rating of the chess player at the time of the game"),
                bigquery.SchemaField(name="result",     field_type="STRING",     mode="REQUIRED", description="The result of the respective chess game"),
        ]),

        bigquery.SchemaField(name="accuracies",     field_type="RECORD",    mode="NULLABLE", description="Player accuracies", fields=[
                bigquery.SchemaField(name="white",      field_type="FLOAT64",    mode="NULLABLE", description="White - The accuracy of the respective chess game"),
                bigquery.SchemaField(name="black",      field_type="FLOAT64",    mode="NULLABLE", description="Black - The accuracy of the respective chess game"),
        ]),

        bigquery.SchemaField(name="eco",     field_type="STRING",          mode="REQUIRED", description="The Encyclopedia of Chess Openings URL for the chess opening played"),
        bigquery.SchemaField(name="opening", field_type="STRING",          mode="REQUIRED", description="The name of the chess opening played"),
    ]
    games_time_partitioning_field ="game_date"

    if check_bigquery_table_exists(table_id_games, logger) == False:
        create_bigquery_table(table_id_games, schema_games, logger, games_time_partitioning_field)
    return games_time_partitioning_field, schema_games, table_id_games


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
    table_id_loading_completed,
):
    # Determine which endpoints that have not been processed from GCS to BQ destination
    endpoints_missing_from_bq = sorted(return_missing_data_list("gcs_endpoint", table_id_loading_completed, list_filtered_game_endpoints, location, logger))
    # endpoints_missing_from_bq
    return (endpoints_missing_from_bq,)


@app.cell
def _(
    bucket_name,
    dev_testcase,
    endpoints_missing_from_bq,
    generate_games_dataframe,
    log_printer,
    logger,
    pd,
    script_setting,
    test_volume,
):
    if script_setting == "dev":
        df_combined, interaction_dict = generate_games_dataframe(dev_testcase, bucket_name, logger)
        df_interaction_list = pd.DataFrame([interaction_dict])
        print("Downloaded test case to dataframe")

    # Download game data from each endpoint in GCS and store dataframes into list
    if script_setting in ("prod", "test"):
        list_of_game_dfs = []
        list_of_interaction_dicts = []
        for i, gcs_filename in enumerate(endpoints_missing_from_bq):

            # When in test setting, this will apply a limiter to the volume of data being
            if script_setting == "test" and i == test_volume:
                break

            df, interaction_dict = generate_games_dataframe(gcs_filename, bucket_name, logger)

            list_of_interaction_dicts.append(interaction_dict)

            if df is not None:
                list_of_game_dfs.append(df)

        df_combined = pd.concat(list_of_game_dfs)
        df_interaction_list = pd.DataFrame(list_of_interaction_dicts)
        log_printer("Transformed all downloads into list of dataframes and concatenated together", logger)
    return (
        df,
        df_combined,
        df_interaction_list,
        gcs_filename,
        i,
        interaction_dict,
        list_of_game_dfs,
        list_of_interaction_dicts,
    )


@app.cell
def _(df_combined):
    df_combined
    return


@app.cell
def _(
    df_combined,
    location,
    log_printer,
    logger,
    return_missing_data_list,
    table_id_games,
):
    # Determine missing game_id's from BigQuery and filter list accordingly
    games_missing_from_bq = return_missing_data_list("game_id", table_id_games, df_combined["game_id"], location, logger)
    df_filtered = df_combined[df_combined["game_id"].isin(games_missing_from_bq)]
    games_filtered_away = len(df_combined) - len(df_filtered)
    print("\n")
    log_printer(f"Number of game_id's filtered away from combined dataframe: {games_filtered_away}", logger)

    # De-duplication process for game_id's in scenarios where where players inside batch play each other
    df_deduplicated = df_filtered.drop_duplicates(subset="game_id", keep="first")
    duplicates_removed = len(df_filtered) - len(df_deduplicated)
    log_printer(f"Number of duplicate game_id's removed from combined dataframe: {duplicates_removed}", logger)
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
def _(df_interaction_list):
    df_interaction_list
    return


@app.cell
def _(
    append_df_to_bigquery_table,
    bucket_name,
    deletion_interaction_list_handler,
    df_deduplicated,
    df_interaction_list,
    logger,
    script_setting,
    table_id_games,
    table_id_loading_completed,
):
    if script_setting == "prod":
        deletion_interaction_list_handler(df_interaction_list, bucket_name, logger)
        append_df_to_bigquery_table(df_deduplicated, table_id_games, logger)
        append_df_to_bigquery_table(df_interaction_list, table_id_loading_completed, logger)
    return


if __name__ == "__main__":
    app.run()
