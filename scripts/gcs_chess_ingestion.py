import marimo

__generated_with = "0.11.30"
app = marimo.App(width="medium")


@app.cell
def _():
    # Standard Library
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
    sys.path.append("./functions")
    sys.path.append("./inputs")

    from shared import initialise_cloud_logger
    from shared import upload_json_to_gcs_bucket
    from shared import list_files_in_gcs

    from gcs_ingestion import script_date_selection
    from gcs_ingestion import generate_year_month_list
    from gcs_ingestion import get_top_player_list
    from gcs_ingestion import generate_remaining_endpoint_combinations
    from gcs_ingestion import append_player_endpoints_to_https_chess_prefix
    from gcs_ingestion import exponential_backoff_request
    from gcs_ingestion import request_from_list_and_upload_to_gcs
    return (
        append_player_endpoints_to_https_chess_prefix,
        exponential_backoff_request,
        generate_remaining_endpoint_combinations,
        generate_year_month_list,
        get_top_player_list,
        initialise_cloud_logger,
        list_files_in_gcs,
        request_from_list_and_upload_to_gcs,
        script_date_selection,
        upload_json_to_gcs_bucket,
    )


@app.cell
def _(initialise_cloud_logger, json, script_date_selection):
    # Reading Script Input Variables
    with open("./inputs/gcs_ingestion_settings.json") as f:
        gcs_ingestion_settings = json.load(f)

    start_date, end_date = script_date_selection(gcs_ingestion_settings) # type: ignore
    script_setting       = gcs_ingestion_settings.get("script_setting")
    headers              = gcs_ingestion_settings.get("request_headers")
    project_name         = gcs_ingestion_settings.get("project_id")
    bucket_name          = gcs_ingestion_settings.get("bucket_name")

    # Initialise Logger Object
    logger = initialise_cloud_logger(project_name)
    logger.info(f"Project: {project_name} | Bucket: {bucket_name} | Script Setting: {script_setting} | Ingestion Dates: {start_date} - {end_date} ")
    return (
        bucket_name,
        end_date,
        f,
        gcs_ingestion_settings,
        headers,
        logger,
        project_name,
        script_setting,
        start_date,
    )


@app.cell
def _(
    bucket_name,
    datetime,
    exponential_backoff_request,
    headers,
    logger,
    upload_json_to_gcs_bucket,
):
    # Getting current leaderboard data of top chess players
    logger.info('Requesting the latest leaderboards')
    leaderboards_url = f'https://api.chess.com/pub/leaderboards'
    leaderboards_response = exponential_backoff_request(leaderboards_url, headers, logger)
    gcs_leaderboard_endpoint = f"leaderboards/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    upload_json_to_gcs_bucket(bucket_name, gcs_leaderboard_endpoint, leaderboards_response, logger)
    return gcs_leaderboard_endpoint, leaderboards_response, leaderboards_url


@app.cell
def _(
    bucket_name,
    end_date,
    generate_year_month_list,
    get_top_player_list,
    leaderboards_response,
    list_files_in_gcs,
    logger,
    start_date,
):
    # Determine list of requests for players and specified period
    year_month_list = generate_year_month_list(start_date, end_date)
    top_player_list = get_top_player_list(leaderboards_response, logger)

    # Listing the current objects with player data in the chess api storage bucket
    all_files_in_gcs = list_files_in_gcs(bucket_name, logger)
    players_data_in_gcs = sorted([obj for obj in all_files_in_gcs if obj.startswith("player/")])
    return (
        all_files_in_gcs,
        players_data_in_gcs,
        top_player_list,
        year_month_list,
    )


@app.cell
def _(
    append_player_endpoints_to_https_chess_prefix,
    bucket_name,
    generate_remaining_endpoint_combinations,
    logger,
    players_data_in_gcs,
    top_player_list,
    year_month_list,
):
    # Determine remaining player/period combinations to request based on contents of GCS bucket
    remaining_combo_list = generate_remaining_endpoint_combinations(
        bucket_name, 
        players_data_in_gcs, 
        top_player_list, 
        year_month_list, 
        logger
    )

    request_urls = append_player_endpoints_to_https_chess_prefix(remaining_combo_list)
    return remaining_combo_list, request_urls


@app.cell
def _(
    bucket_name,
    headers,
    logger,
    request_from_list_and_upload_to_gcs,
    request_urls,
):
    # Request data from list and upload to GCS
    request_from_list_and_upload_to_gcs(bucket_name, request_urls, headers, logger)
    return


if __name__ == "__main__":
    app.run()
