import marimo

__generated_with = "0.11.30"
app = marimo.App(width="medium")


@app.cell
def _():
    # Standard Library
    import os
    import sys
    import json
    import logging
    from datetime import date, datetime, timedelta
    from dateutil.relativedelta import relativedelta

    # DLT Library
    import dlt

    # Google Libraries
    import google.cloud.logging as cloud_logging
    from google.cloud import storage

    return (
        cloud_logging,
        date,
        datetime,
        dlt,
        json,
        logging,
        os,
        relativedelta,
        storage,
        sys,
        timedelta,
    )


@app.cell
def _(sys):
    # Importing Local Functions
    from gcp_common import initialise_cloud_logger
    from gcp_common import read_cloud_scheduler_message
    from gcp_common import log_printer

    from alerts import load_alerts_environmental_config
    from alerts import create_bq_run_monitor_datasets
    from alerts import append_to_trigger_bq_dataset

    from chess_ingestion import script_date_selection
    from chess_ingestion import generate_year_month_list
    from chess_ingestion import get_top_player_list
    from chess_ingestion import exponential_backoff_request

    return (
        append_to_trigger_bq_dataset,
        create_bq_run_monitor_datasets,
        exponential_backoff_request,
        generate_year_month_list,
        get_top_player_list,
        initialise_cloud_logger,
        load_alerts_environmental_config,
        log_printer,
        read_cloud_scheduler_message,
        script_date_selection,
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

    # Using Prod config when message received from cloud scheduler
    if cloud_scheduler_dict is not None:
        dlt_ingestion_settings = cloud_scheduler_dict
        config_source = "Cloud Scheduler"
    else:
        # Local configuration - when no message sent to script
        dlt_ingestion_settings = {
            "project_id": "checkmate-453316",
            "bucket_name": "dev-chess-api",
            "app_env": "DEV",
            "start_date": "2025-08-01",
            "end_date": "2025-08-01",
            "request_headers": {
                "User-Agent": "gcs_chess_ingestion_dlt.py (Python 3.11) (username: filiplivancic; contact: filiplivancic@gmail.com)"
            }
        }
        config_source = "Local Config"

    # Extract configuration variables
    start_date, end_date = script_date_selection(dlt_ingestion_settings) # type: ignore

    # Initialise Logger Object
    logger = initialise_cloud_logger(dlt_ingestion_settings["project_id"])
    log_printer(f"Cloud Scheduler Message: {cloud_scheduler_dict}", logger)
    log_printer(f"Config Source: {config_source} | Initialising DLT Ingestion Script | Project: {dlt_ingestion_settings['project_id']} | Bucket: {dlt_ingestion_settings['bucket_name']} | App Env: {dlt_ingestion_settings['app_env']} | Ingestion Dates: {start_date} - {end_date}", logger)

    # Activate alerting functionality only when running from Cloud Scheduler
    if cloud_scheduler_dict is not None:
        log_printer("Activating alerting functionality", logger)

        # Set APP_ENV environment variable for alerts
        os.environ["APP_ENV"] = dlt_ingestion_settings["app_env"]
        os.environ["PROJECT_ID"] = dlt_ingestion_settings["project_id"]

        # Load alert configuration and setup monitoring
        load_alerts_environmental_config()
        create_bq_run_monitor_datasets(dlt_ingestion_settings["project_id"], logger)
        append_to_trigger_bq_dataset(dlt_ingestion_settings["project_id"], logger)

        log_printer("Alerting functionality activated", logger)

    return (
        cloud_scheduler_dict,
        config_source,
        dlt_ingestion_settings,
        end_date,
        logger,
        start_date,
    )


@app.cell
def _(end_date, start_date):
    print(start_date, end_date)
    return


@app.cell
def _(
    datetime,
    dlt,
    dlt_ingestion_settings,
    exponential_backoff_request,
    log_printer,
    logger,
):
    # Define DLT resource for leaderboard data
    @dlt.resource(name="leaderboards", write_disposition="replace")
    def fetch_leaderboards():
        """Fetch current Chess.com leaderboards"""
        log_printer('Requesting the latest leaderboards', logger)
        leaderboards_url = 'https://api.chess.com/pub/leaderboards'
        leaderboards_response = exponential_backoff_request(
            leaderboards_url,
            dlt_ingestion_settings["request_headers"],
            logger
        )

        if leaderboards_response:
            data = leaderboards_response.json()
            # Add metadata
            data["_fetched_at"] = datetime.now().isoformat()
            yield data

    return (fetch_leaderboards,)


@app.cell
def _(
    dlt,
    dlt_ingestion_settings,
    exponential_backoff_request,
    generate_year_month_list,
    get_top_player_list,
    log_printer,
    logger,
):
    # Define DLT resource for player game data with idempotency
    @dlt.resource(name="player_games", write_disposition="append")
    def fetch_player_games(leaderboards_data, start_date, end_date):
        """
        Fetch Chess.com player game archives for specified date range
        Uses DLT state management for idempotency - skips already-fetched combinations

        Args:
            leaderboards_data: Leaderboard data to extract player list
            start_date: Start date for game archives
            end_date: End date for game archives
        """
        log_printer('Processing player game data with idempotency checking', logger)

        # Generate date range and player list
        year_month_list = generate_year_month_list(start_date, end_date)

        # Extract top players from leaderboards
        # Mock the response object structure that get_top_player_list expects
        class MockResponse:
            def __init__(self, data):
                self._data = data
            def json(self):
                return self._data

        mock_response = MockResponse(leaderboards_data)
        top_player_list = get_top_player_list(mock_response, logger)

        # Access DLT's state to track processed combinations
        state = dlt.current.source_state()
        if "processed_combinations" not in state:
            state["processed_combinations"] = set()

        processed = state["processed_combinations"]

        # Calculate total and remaining requests
        all_combinations = [(player, period) for player in top_player_list for period in year_month_list]
        remaining_combinations = [
            (player, period) for player, period in all_combinations
            if f"{player}|{period}" not in processed
        ]

        total_combinations = len(all_combinations)
        remaining_count = len(remaining_combinations)
        already_processed = total_combinations - remaining_count

        log_printer(f"Total combinations: {total_combinations}", logger)
        log_printer(f"Already processed: {already_processed}", logger)
        log_printer(f"Remaining to fetch: {remaining_count}", logger)

        # Fetch games for remaining player/period combinations
        completed_requests = 0

        for player, period in remaining_combinations:
            url = f"https://api.chess.com/pub/player/{player}/games/{period}"

            games_response = exponential_backoff_request(
                url,
                dlt_ingestion_settings["request_headers"],
                logger
            )

            completed_requests += 1
            if completed_requests % 50 == 0:
                log_printer(f"Progress: {completed_requests}/{remaining_count} requests completed", logger)

            if games_response:
                data = games_response.json()
                # Add metadata to track the data source
                data["_player"] = player
                data["_period"] = period
                data["_url"] = url

                # Mark this combination as processed
                state["processed_combinations"].add(f"{player}|{period}")

                yield data
            else:
                # Even if request failed (404 or error), mark as processed to avoid re-attempting
                log_printer(f"Marking {player}|{period} as processed despite failed request", logger)
                state["processed_combinations"].add(f"{player}|{period}")

        log_printer(f"Completed fetching {completed_requests} new player/period combinations", logger)

    return (fetch_player_games,)


@app.cell
def _(
    dlt,
    dlt_ingestion_settings,
    end_date,
    fetch_leaderboards,
    fetch_player_games,
    log_printer,
    logger,
    start_date,
):
    # Configure DLT pipeline with GCS filesystem destination
    log_printer("Configuring DLT pipeline", logger)

    pipeline = dlt.pipeline(
        pipeline_name="chess_api_ingestion",
        destination=dlt.destinations.filesystem(
            bucket_url=f"gs://{dlt_ingestion_settings['bucket_name']}"
        ),
        dataset_name="chess_data"
    )

    log_printer(f"DLT Pipeline configured to write to: gs://{dlt_ingestion_settings['bucket_name']}/chess_data", logger)

    # Execute the pipeline
    log_printer("Starting DLT pipeline execution", logger)

    # First, fetch leaderboards
    leaderboards_data = None
    for item in fetch_leaderboards():
        leaderboards_data = item
        break  # Only one item

    if leaderboards_data:
        log_printer("Leaderboards fetched successfully", logger)

        # Run the pipeline with both resources
        load_info = pipeline.run(
            [
                fetch_leaderboards(),
                fetch_player_games(leaderboards_data, start_date, end_date)
            ]
        )

        log_printer(f"DLT Pipeline execution completed: {load_info}", logger)
        log_printer(f"Data loaded to: gs://{dlt_ingestion_settings['bucket_name']}/chess_data", logger)
    else:
        log_printer("Failed to fetch leaderboards, aborting pipeline", logger, severity="ERROR")

    return leaderboards_data, load_info, pipeline


if __name__ == "__main__":
    app.run()
