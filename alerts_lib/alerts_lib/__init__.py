"""
Chess Pipeline Alerting Library

Provides email, Discord, and BigQuery alerting functionality for Python data pipelines.
"""

from .alerts import (
    gcp_access_secret,
    load_alerts_environmental_config,
    build_error_email_msg,
    build_error_discord_msg,
    send_email_message,
    send_discord_message,
    create_bq_run_monitor_datasets,
    append_to_trigger_bq_dataset,
    append_to_failed_bq_dataset,
    global_excepthook,
    check_bigquery_dataset_exists,
    create_bigquery_dataset,
    check_bigquery_table_exists,
    create_bigquery_table,
    append_df_to_bigquery_table,
)

__version__ = "0.1.0"

__all__ = [
    "gcp_access_secret",
    "load_alerts_environmental_config",
    "build_error_email_msg",
    "build_error_discord_msg",
    "send_email_message",
    "send_discord_message",
    "create_bq_run_monitor_datasets",
    "append_to_trigger_bq_dataset",
    "append_to_failed_bq_dataset",
    "global_excepthook",
    "check_bigquery_dataset_exists",
    "create_bigquery_dataset",
    "check_bigquery_table_exists",
    "create_bigquery_table",
    "append_df_to_bigquery_table",
]
