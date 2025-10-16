"""
Chess.com API Data Ingestion Functions

Functions for fetching chess game data from Chess.com API leaderboards
and player endpoints, with exponential backoff and GCS upload.
"""

import re
import time
import random
import requests
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from itertools import product

from gcp_common import upload_json_to_gcs_bucket, log_printer


def script_date_selection(gcs_ingestion_settings):
    """
    Select date range for ingestion based on script settings.

    Args:
        gcs_ingestion_settings: Dictionary with script_setting and optional manual dates

    Returns:
        Tuple of (start_date, end_date)
    """
    script_setting = gcs_ingestion_settings.get("script_setting")
    if script_setting == 'default':
        start_date = (date.today() - relativedelta(months=1)).replace(day=1)
        end_date   = (date.today() - relativedelta(months=1)).replace(day=1)

    if script_setting == 'manual':
        start_date = datetime.strptime(gcs_ingestion_settings.get("manual_start_date"), "%Y-%m-%d").date()
        end_date = datetime.strptime(gcs_ingestion_settings.get("manual_end_date"), "%Y-%m-%d").date()

    return start_date, end_date


def generate_year_month_list(start_date: date, end_date: date):
    """
    Generate list of year/month strings between start and end dates.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of strings in format "YYYY/MM"
    """
    # Ensure we start from the first day of the start month
    current_date = start_date.replace(day=1)

    # Move end_date to the last complete month
    if end_date.day > 1:
        end_date = end_date.replace(day=1)                           # Move to the first of the month
        end_date = end_date.replace(month=end_date.month - 1 or 12)  # Step back one month
        if end_date.month == 12:                                     # Handle year change if stepping back from January
            end_date = end_date.replace(year=end_date.year - 1)

    date_list = []

    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y/%m"))
        # Move to the next month
        next_month = current_date.month % 12 + 1
        next_year = current_date.year + (1 if next_month == 1 else 0)
        current_date = date(next_year, next_month, 1)

    return date_list


def get_top_player_list(leaderboard_response, logger):
    """
    Extract list of top players from Chess.com leaderboard response.

    Args:
        leaderboard_response: Response object from Chess.com leaderboard API
        logger: Cloud logging logger instance

    Returns:
        List of player usernames (deduplicated)
    """
    # Find all possible chess formats being tracked on leaderboard
    format_list = list(leaderboard_response.json().keys())

    # Get all the top player names from each chess format
    log_printer('Retrieving the names of top chess players', logger)
    top_player_list = []
    for form in format_list:
        for i in range(len(leaderboard_response.json().get(form))):
            user = leaderboard_response.json().get(form)[i].get('username')
            top_player_list.append(user.lower())

    # Deduplicate usernames
    top_player_list = list(set(top_player_list))
    return top_player_list


def generate_remaining_endpoint_combinations(bucket_name, players_data_in_gcs, top_player_list, year_month_list, logger):
    """
    Generate list of API endpoints that haven't been fetched yet.

    Args:
        bucket_name: GCS bucket name
        players_data_in_gcs: List of existing player data paths in GCS
        top_player_list: List of player usernames
        year_month_list: List of year/month strings
        logger: Cloud logging logger instance

    Returns:
        List of remaining endpoint combinations to fetch
    """
    # Cross product of usernames with the date period selected
    all_player_date_combinations = sorted([f"player/{player}/games/{period}" for player, period in product(top_player_list, year_month_list)])

    # If the combination does not exist in GCS --> add to remaining combination list so it can be requested
    remaining_combinations = [combo for combo in all_player_date_combinations if combo not in players_data_in_gcs]

    log_printer(f"Total request combinations: {len(all_player_date_combinations)}", logger)
    log_printer(f"Number of remaining requests: {len(remaining_combinations)}", logger)

    return remaining_combinations


def append_player_endpoints_to_https_chess_prefix(remaining_combo_list):
    """
    Convert endpoint combinations to full Chess.com API URLs.

    Args:
        remaining_combo_list: List of endpoint paths

    Returns:
        List of full URLs
    """
    # Convert combos into URL request list
    request_urls = [f"https://api.chess.com/pub/{endpoint}" for endpoint in remaining_combo_list]

    return request_urls


def exponential_backoff_request(url, headers, logger, max_retries=5, base_delay=3, max_delay=120):
    """
    Make HTTP request with exponential backoff retry logic.

    Args:
        url: URL to request
        headers: Request headers
        logger: Cloud logging logger instance
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Response object or None if failed
    """
    retries = 0
    while retries < max_retries:
        response = requests.get(url, headers=headers)
        status_code = response.status_code

        if status_code == 200:
            return response

        if status_code == 404:
            log_printer(f"404 error for {url} - Endpoint currently not working...Skipping", logger, severity="WARNING")
            return None

        # Will attempt a retry process for non-404 codes with expontential backoff
        wait_time = min(base_delay * (4 ** retries) + random.uniform(0, 1), max_delay)
        log_printer(f"HTTP Status Code: {status_code} | Retry {retries + 1}/{max_retries} - Sleeping {wait_time:.2f} seconds | URL: {url}", logger, severity="WARNING")
        time.sleep(wait_time)
        retries += 1

    log_printer("Max retries reached. Request failed for {url}", logger, severity="ERROR")
    return None


def request_from_list_and_upload_to_gcs(bucket_name, request_urls, headers, logger):
    """
    Request data from list of URLs and upload to GCS.

    Args:
        bucket_name: GCS bucket name
        request_urls: List of URLs to request
        headers: Request headers
        logger: Cloud logging logger instance
    """
    log_printer(f'Requesting archived game data', logger)
    for url in request_urls:

        # Requesting Data
        games_response = exponential_backoff_request(url, headers, logger)

        if games_response == None:
            continue

        # Extracting player and period components from url to build GCS path to save to
        match = re.search(r'player/([^/]+)/games/(\d{4}/\d{2})', url)
        if match:
            player = match.group(1)
            period = match.group(2)
        gcs_player_endpoint = f"player/{player}/games/{period}"

        # Saving Data to GCS
        upload_json_to_gcs_bucket(bucket_name, gcs_player_endpoint, games_response, logger)
