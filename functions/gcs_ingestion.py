import re
import sys
import json
import time
import random
import logging
import requests
import google.cloud.logging as cloud_logging

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from google.cloud import storage
from itertools import product

sys.path.append("../functions")
from shared import *

def script_date_selection(gcs_ingestion_settings):
    script_setting = gcs_ingestion_settings.get("script_setting")
    if script_setting == 'default':
        start_date = date.today() - relativedelta(months=12)
        end_date = date.today()

    if script_setting == 'manual':
        start_date = datetime.strptime(gcs_ingestion_settings.get("manual_start_date"), "%Y-%m-%d").date() 
        end_date = datetime.strptime(gcs_ingestion_settings.get("manual_end_date"), "%Y-%m-%d").date() 
    
    return start_date, end_date 

def generate_year_month_list(start_date: date, end_date: date):

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
    # Find all possible chess formats being tracked on leaderboard
    format_list = list(leaderboard_response.json().keys())

    # Get all the top player names from each chess format
    logger.info('Retrieving the names of top chess players')
    top_player_list = []
    for form in format_list:
        for i in range(len(leaderboard_response.json().get(form))):
            user = leaderboard_response.json().get(form)[i].get('username')
            top_player_list.append(user.lower())
            
    # Deduplicate usernames
    top_player_list = list(set(top_player_list))
    return top_player_list


def generate_remaining_endpoint_combinations(bucket_name, players_data_in_gcs, top_player_list, year_month_list, logger):

    # Cross product of usernames with the date period selected
    all_player_date_combinations = sorted([f"player/{player}/games/{period}" for player, period in product(top_player_list, year_month_list)])

    # If the combination does not exist in GCS --> add to remaining combination list so it can be requested
    remaining_combinations = [combo for combo in all_player_date_combinations if combo not in players_data_in_gcs]
                
    logger.info(f"Total request combinations: {len(all_player_date_combinations)}")
    logger.info(f"Number of remaining requests: {len(remaining_combinations)}")
    
    return remaining_combinations


def append_player_endpoints_to_https_chess_prefix(remaining_combo_list):

    # Convert combos into URL request list
    request_urls = [f"https://api.chess.com/pub/{endpoint}" for endpoint in remaining_combo_list]

    return request_urls


def exponential_backoff_request(url, headers, logger, max_retries=5, base_delay=10, max_delay=120):

    retries = 0
    while retries < max_retries:
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        if status_code == 200:
            return response
        
        wait_time = min(base_delay * (4 ** retries) + random.uniform(0, 1), max_delay)
        logger.warning(f"HTTP Status Code: {status_code} | Retry {retries + 1}/{max_retries} - Sleeping {wait_time:.2f} seconds | URL: {url}")
        time.sleep(wait_time)
        retries += 1
    
    logger.warning("Max retries reached. Request failed for {url}")
    return None


def request_from_list_and_upload_to_gcs(bucket_name, request_urls, headers, logger):
    logger.info('Requesting archived game data')
    for url in request_urls:

        # Requesting Data
        games_response = exponential_backoff_request(url, headers, logger)

        # Extracting player and period components from url to build GCS path to save to
        match = re.search(r'player/([^/]+)/games/(\d{4}/\d{2})', url)
        if match:
            player = match.group(1)
            period = match.group(2)
        gcs_player_endpoint = f"player/{player}/games/{period}" 

        # Saving Data to GCS
        upload_json_to_gcs_bucket(bucket_name, gcs_player_endpoint, games_response, logger)
