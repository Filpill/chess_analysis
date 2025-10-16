"""
Chess.com API Ingestion Library

Functions for fetching chess game data from Chess.com API and uploading to GCS.
"""

from .chess_ingestion import (
    script_date_selection,
    generate_year_month_list,
    get_top_player_list,
    generate_remaining_endpoint_combinations,
    append_player_endpoints_to_https_chess_prefix,
    exponential_backoff_request,
    request_from_list_and_upload_to_gcs,
)

__version__ = "0.1.0"

__all__ = [
    "script_date_selection",
    "generate_year_month_list",
    "get_top_player_list",
    "generate_remaining_endpoint_combinations",
    "append_player_endpoints_to_https_chess_prefix",
    "exponential_backoff_request",
    "request_from_list_and_upload_to_gcs",
]
