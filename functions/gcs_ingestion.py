
import sys
import json
import logging
import requests
import google.cloud.logging as cloud_logging

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from google.cloud import storage
from itertools import product
from time import sleep 

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


def get_request_permutations(bucket_name, top_player_list, logger):
    # Listing the current objects in the chess api storage bucket
    gcs_file_list = list_files_in_gcs(bucket_name, logger)

    # Cross product of usernames with the date period selected
    player_date_permutations = [f"players/{player}/games/{period}" for player, period in product(top_player_list, year_month_list)]

    # Check if those combos exist in GCS currently -- if not remove them from the list
    remaining_game_requests = player_date_permutations[:]
    for combo in remaining_game_requests:
        if combo in gcs_file_list:
            remaining_game_requests.remove(combo)
            
    logger.info(f"Total request combinations: {len(player_date_permutations)}")
    logger.info(f"Number of remaing requests: {len(remaining_game_requests)}")
    
    return remaining_game_requests 


def request_all_games_and_upload_to_gcs(bucket_name, top_player_list, year_month_list, headers, logger):
    logger.info('Requesting archived game data')
    for player in top_player_list:
        for period in year_month_list:
            logger.info(f'Requesting Game Data | player: {player} | period {period}')
            games_url = f'https://api.chess.com/pub/player/{player}/games/{period}'
            games_response = exponential_backoff_request(games_url, headers, logger)
            gcs_player_endpoint = f"players/{player}/games/{period}" 
            upload_json_to_gcs_bucket(bucket_name, gcs_player_endpoint, games_response, logger)
            sleep(1) 

            
def append_prefix_to_gcs_files(prefix, excluded_prefixes, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    
    # The for loop will exlude any files that should not be targeted in the renaming
    for blob in blobs:
        if any(blob.name.startswith(f"{prefix}/") for prefix in excluded_prefixes):
            logger.info("Skipping {blob.name} | Excluded from renaming process")
            continue

        new_name = f"{prefix}/{blob.name}"
        bucket.rename_blob(blob, new_name)
        logger.info(f"Renamed {blob.name} -> {new_name}") 