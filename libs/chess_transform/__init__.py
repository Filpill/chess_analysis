"""
Chess Game Data Transformation Library

Functions for transforming and loading chess game data from GCS to BigQuery.
"""

from .chess_transform import (
    script_date_endpoint_selection,
    extract_last_url_component,
    convert_unix_ts_to_date,
    compare_sets_and_return_non_matches,
    extract_eco_url_from_pgn,
    return_missing_data_list,
    gcs_action_taken_dict,
    generate_games_dataframe,
    deletion_interaction_list_handler,
)

__version__ = "0.1.0"

__all__ = [
    "script_date_endpoint_selection",
    "extract_last_url_component",
    "convert_unix_ts_to_date",
    "compare_sets_and_return_non_matches",
    "extract_eco_url_from_pgn",
    "return_missing_data_list",
    "gcs_action_taken_dict",
    "generate_games_dataframe",
    "deletion_interaction_list_handler",
]
