import marimo

__generated_with = "0.11.30"
app = marimo.App(width="medium")


@app.cell
def _():
    # Standard Library
    import os
    import sys
    import json
    import time
    import random
    import logging
    import requests
    from datetime import date, datetime, timedelta
    from dateutil.relativedelta import relativedelta
    from itertools import product

    # Google Libraries
    import google.cloud.logging as cloud_logging
    from google.cloud import storage
    return (
        cloud_logging,
        date,
        datetime,
        json,
        logging,
        os,
        product,
        random,
        relativedelta,
        requests,
        storage,
        sys,
        time,
        timedelta,
    )


@app.cell
def _(sys):

    # Importing Local Functions
    from gcp_common import initialise_cloud_logger
    from gcp_common import upload_json_to_gcs_bucket
    from gcp_common import list_files_in_gcs
    from gcp_common import read_cloud_scheduler_message
    from gcp_common import log_printer

    from alerts import load_alerts_environmental_config
    from alerts import create_bq_run_monitor_datasets
    from alerts import append_to_trigger_bq_dataset

    from chess_ingestion import script_date_selection
    from chess_ingestion import generate_year_month_list
    from chess_ingestion import get_top_player_list
    from chess_ingestion import generate_remaining_endpoint_combinations
    from chess_ingestion import append_player_endpoints_to_https_chess_prefix
    from chess_ingestion import exponential_backoff_request
    from chess_ingestion import request_from_list_and_upload_to_gcs
    return (
        append_player_endpoints_to_https_chess_prefix,
        append_to_trigger_bq_dataset,
        create_bq_run_monitor_datasets,
        exponential_backoff_request,
        folder,
        folder_list,
        generate_remaining_endpoint_combinations,
        generate_year_month_list,
        get_top_player_list,
        initialise_cloud_logger,
        list_files_in_gcs,
        load_alerts_environmental_config,
        log_printer,
        read_cloud_scheduler_message,
        rel_path,
        request_from_list_and_upload_to_gcs,
        script_date_selection,
        upload_json_to_gcs_bucket,
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
    script_date_selection,
):

    # Context switch: Use Cloud Scheduler config if available, otherwise use local config
    cloud_scheduler_dict = read_cloud_scheduler_message()

    # Using Prod config when message recieved from cloud scheduler
    if cloud_scheduler_dict is not None:
        gcs_ingestion_settings = cloud_scheduler_dict
        config_source = "Cloud Scheduler"
    else:
        # Local configuration - when no message sent to script
        gcs_ingestion_settings = {
            "project_id": "checkmate-453316",
            "bucket_name": "chess-api",
            "app_env": "DEV",
            "start_date": "2025-08-01",
            "end_date": "2025-08-01",
            "request_headers": {
                "User-Agent": "gcs_chess_ingestion.py (Python 3.11) (username: filiplivancic; contact: filiplivancic@gmail.com)"
            }
        }
        config_source = "Local Config"

    # Extract configuration variables
    start_date, end_date = script_date_selection(gcs_ingestion_settings) # type: ignore

    # Initialise Logger Object
    logger = initialise_cloud_logger(gcs_ingestion_settings["project_id"])
    log_printer(f"Cloud Scheduler Message: {cloud_scheduler_dict}", logger)
    log_printer(f"Config Source: {config_source} | Initialising Ingestion Script to Append data to GCS | Project: {gcs_ingestion_settings['project_id']} | Bucket: {gcs_ingestion_settings['bucket_name']} | App Env: {gcs_ingestion_settings['app_env']} | Ingestion Dates: {start_date} - {end_date} ", logger)

    # Activate alerting functionality only when running from Cloud Scheduler
    if cloud_scheduler_dict is not None:
        log_printer("Activating alerting functionality", logger)

        # Set APP_ENV environment variable for alerts
        os.environ["APP_ENV"] = gcs_ingestion_settings["app_env"]
        os.environ["PROJECT_ID"] = gcs_ingestion_settings["project_id"]

        # Load alert configuration and setup monitoring
        load_alerts_environmental_config()
        create_bq_run_monitor_datasets(gcs_ingestion_settings["project_id"], logger)
        append_to_trigger_bq_dataset(gcs_ingestion_settings["project_id"], logger)

        log_printer("Alerting functionality activated", logger)
    return (
        cloud_scheduler_dict,
        config_source,
        end_date,
        f,
        gcs_ingestion_settings,
        logger,
        start_date,
    )


@app.cell
def _(end_date, start_date):
    print(start_date,end_date)
    return


@app.cell
def _(
    datetime,
    exponential_backoff_request,
    gcs_ingestion_settings,
    log_printer,
    logger,
    upload_json_to_gcs_bucket,
):
    # Getting current leaderboard data of top chess players
    log_printer('Requesting the latest leaderboards', logger)
    leaderboards_url = f'https://api.chess.com/pub/leaderboards'
    leaderboards_response = exponential_backoff_request(leaderboards_url, gcs_ingestion_settings["request_headers"], logger)
    gcs_leaderboard_endpoint = f"leaderboards/{datetime.now().strftime('%Y-%m-%d')}/{datetime.now().strftime('%H-%M-%S')}"
    upload_json_to_gcs_bucket(gcs_ingestion_settings["bucket_name"], gcs_leaderboard_endpoint, leaderboards_response, logger)
    return gcs_leaderboard_endpoint, leaderboards_response, leaderboards_url


@app.cell
def _(gcs_ingestion_settings, list_files_in_gcs, logger):
    # Listing the current objects with player data in the chess api storage bucket
    all_files_in_gcs = list_files_in_gcs(gcs_ingestion_settings["bucket_name"], logger)
    players_data_in_gcs = sorted([obj for obj in all_files_in_gcs if obj.startswith("player/")])
    return all_files_in_gcs, players_data_in_gcs


@app.cell
def _(
    append_player_endpoints_to_https_chess_prefix,
    end_date,
    gcs_ingestion_settings,
    generate_remaining_endpoint_combinations,
    generate_year_month_list,
    get_top_player_list,
    leaderboards_response,
    logger,
    players_data_in_gcs,
    start_date,
):
    # Determine list of requests for players and specified period
    year_month_list = generate_year_month_list(start_date, end_date)
    top_player_list = get_top_player_list(leaderboards_response, logger)

    # Determine remaining player/period combinations to request based on contents of GCS bucket
    remaining_combo_list = generate_remaining_endpoint_combinations(
        gcs_ingestion_settings["bucket_name"],
        players_data_in_gcs,
        top_player_list,
        year_month_list,
        logger
    )

    request_urls = append_player_endpoints_to_https_chess_prefix(remaining_combo_list)
    return remaining_combo_list, request_urls, top_player_list, year_month_list


@app.cell
def _(
    gcs_ingestion_settings,
    logger,
    request_from_list_and_upload_to_gcs,
    request_urls,
):
    # Request data from list and upload to GCS
    request_from_list_and_upload_to_gcs(gcs_ingestion_settings["bucket_name"], request_urls, gcs_ingestion_settings["request_headers"], logger)
    return


if __name__ == "__main__":
    app.run()
