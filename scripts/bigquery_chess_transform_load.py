import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # The Usual
    import os
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

    from gcp_common import log_printer
    from gcp_common import initialise_cloud_logger
    from gcp_common import list_files_in_gcs
    from gcp_common import download_content_from_gcs
    from gcp_common import delete_gcs_object
    from gcp_common import check_bigquery_dataset_exists
    from gcp_common import check_bigquery_table_exists
    from gcp_common import create_bigquery_dataset
    from gcp_common import create_bigquery_table
    from gcp_common import append_df_to_bigquery_table
    from gcp_common import query_bq_to_dataframe
    from gcp_common import read_cloud_scheduler_message

    from alerts import load_alerts_environmental_config
    from alerts import create_bq_run_monitor_datasets
    from alerts import append_to_trigger_bq_dataset

    from chess_transform import script_date_endpoint_selection
    from chess_transform import extract_last_url_component
    from chess_transform import convert_unix_ts_to_date
    from chess_transform import return_missing_data_list
    from chess_transform import generate_games_dataframe
    from chess_transform import compare_sets_and_return_non_matches
    from chess_transform import deletion_interaction_list_handler
    return (
        CloudLoggingHandler,
        List,
        NotFound,
        append_df_to_bigquery_table,
        append_to_trigger_bq_dataset,
        bigquery,
        check_bigquery_dataset_exists,
        check_bigquery_table_exists,
        cloud_logging,
        compare_sets_and_return_non_matches,
        convert_unix_ts_to_date,
        create_bigquery_dataset,
        create_bigquery_table,
        create_bq_run_monitor_datasets,
        delete_gcs_object,
        deletion_interaction_list_handler,
        download_content_from_gcs,
        extract_last_url_component,
        generate_games_dataframe,
        initialise_cloud_logger,
        json,
        list_files_in_gcs,
        load_alerts_environmental_config,
        log_printer,
        mo,
        np,
        os,
        pandas_gbq,
        pd,
        pyarrow,
        query_bq_to_dataframe,
        read_cloud_scheduler_message,
        return_missing_data_list,
        script_date_endpoint_selection,
        setup_logging,
        storage,
        sys,
        warnings,
    )


@app.cell
def _(
    append_to_trigger_bq_dataset,
    create_bq_run_monitor_datasets,
    initialise_cloud_logger,
    json,
    load_alerts_environmental_config,
    log_printer,
    os,
    read_cloud_scheduler_message,
    script_date_endpoint_selection,
):
    # Context switch: Use Cloud Scheduler config if available, otherwise use local config
    cloud_scheduler_dict = read_cloud_scheduler_message()

    if cloud_scheduler_dict is not None:
        bq_load_settings = cloud_scheduler_dict
        config_source = "Cloud Scheduler"
    else:
        # Local configuration
        bq_load_settings = {
            "app_env": "DEV",
            "test_volume": 2,
            "dev_testcase": "player/emeraldddd/games/2024/10",
            "date_endpoint": "2025/04",
            "project_id": "checkmate-453316",
            "bucket_name": "chess-api",
            "dataset_name": "chess_raw",
            "location": "EU"
        }
        config_source = "Local Config"

    # Extract configuration variables
    date_endpoint   = script_date_endpoint_selection(bq_load_settings) # type: ignore
    app_env         = bq_load_settings["app_env"]                  # prod/test/dev
    test_volume     = bq_load_settings["test_volume"]              # For "test" setting Max number of files to be downloaded during testing mode
    dev_testcase    = bq_load_settings["dev_testcase"]             # Singular endpoint testing
    dataset_name    = bq_load_settings["dataset_name"]
    location        = bq_load_settings["location"]

    dataset_id = f"{bq_load_settings['project_id']}.{dataset_name}"

    # Initialise Logger Object
    logger = initialise_cloud_logger(bq_load_settings["project_id"])

    # Log cloud scheduler message and config source
    log_printer(f"Cloud Scheduler Message: {cloud_scheduler_dict}", logger)
    log_printer(f"Config Source: {config_source} | Initialising Transform Script to Incrementally Insert data into BigQuery | Project: {bq_load_settings['project_id']} | Bucket: {bq_load_settings['bucket_name']} | App Env: {app_env} | date_endpoint: {date_endpoint}", logger)

    # Activate alerting functionality only when running from Cloud Scheduler
    if cloud_scheduler_dict is not None:
        log_printer("Activating alerting functionality", logger)

        # Set APP_ENV environment variable for alerts
        os.environ["APP_ENV"] = app_env
        os.environ["PROJECT_ID"] = bq_load_settings["project_id"]

        # Load alert configuration and setup monitoring
        load_alerts_environmental_config()
        create_bq_run_monitor_datasets(bq_load_settings["project_id"], logger)
        append_to_trigger_bq_dataset(bq_load_settings["project_id"], logger)

        log_printer("Alerting functionality activated", logger)
    return (
        app_env,
        bq_load_settings,
        cloud_scheduler_dict,
        config_source,
        dataset_id,
        dataset_name,
        date_endpoint,
        dev_testcase,
        f,
        location,
        logger,
        test_volume,
    )


@app.cell
def _(
    bq_load_settings,
    check_bigquery_dataset_exists,
    create_bigquery_dataset,
    dataset_id,
    location,
    logger,
):
    if check_bigquery_dataset_exists(dataset_id, logger) == False:
        create_bigquery_dataset(bq_load_settings["project_id"], dataset_id, location, logger)
    return


@app.cell
def _(
    bigquery,
    bq_load_settings,
    check_bigquery_table_exists,
    create_bigquery_table,
    dataset_name,
    logger,
):
    # Definining Schema of Loading Completed BigQuery Table
    table_id_loading_completed = f"{bq_load_settings['project_id']}.{dataset_name}.loading_completed"

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
    bq_load_settings,
    check_bigquery_table_exists,
    create_bigquery_table,
    dataset_name,
    logger,
):
    # Definining Schema of Games BigQuery Table
    table_id_games = f"{bq_load_settings['project_id']}.{dataset_name}.games"

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
def _(bq_load_settings, date_endpoint, list_files_in_gcs, logger):
    # List player objects from GCS
    files_in_gcs = list_files_in_gcs(bq_load_settings["bucket_name"], logger)
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
    app_env,
    bq_load_settings,
    dev_testcase,
    endpoints_missing_from_bq,
    generate_games_dataframe,
    log_printer,
    logger,
    pd,
    test_volume,
):
    if app_env == "DEV":
        df_combined, interaction_dict = generate_games_dataframe(dev_testcase, bq_load_settings["bucket_name"], logger)
        df_interaction_list = pd.DataFrame([interaction_dict])
        print("Downloaded test case to dataframe")

    # Download game data from each endpoint in GCS and store dataframes into list
    if app_env in ("PROD", "TEST"):
        list_of_game_dfs = []
        list_of_interaction_dicts = []
        for i, gcs_filename in enumerate(endpoints_missing_from_bq):

            # When in test setting, this will apply a limiter to the volume of data being
            if app_env == "TEST" and i == test_volume:
                break

            df, interaction_dict = generate_games_dataframe(gcs_filename, bq_load_settings["bucket_name"], logger)

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
    app_env,
    append_df_to_bigquery_table,
    bq_load_settings,
    deletion_interaction_list_handler,
    df_deduplicated,
    df_interaction_list,
    logger,
    table_id_games,
    table_id_loading_completed,
):
    if app_env == "PROD":
        deletion_interaction_list_handler(df_interaction_list, bq_load_settings["bucket_name"], logger)
        append_df_to_bigquery_table(df_deduplicated, table_id_games)
        append_df_to_bigquery_table(df_interaction_list, table_id_loading_completed)
    return


if __name__ == "__main__":
    app.run()
