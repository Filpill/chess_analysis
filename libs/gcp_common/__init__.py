"""
GCP Common Utilities Library

Provides common GCP functions for Cloud Logging, Secret Manager, Pub/Sub, Cloud Storage, and BigQuery.
"""

from .gcp_common import (
    log_printer,
    initialise_cloud_logger,
    gcp_access_secret,
    read_cloud_scheduler_message,
    append_prefix_to_gcs_files,
    rename_prefix_of_gcs_files,
    upload_json_to_gcs_bucket,
    list_files_in_gcs,
    download_content_from_gcs,
    delete_gcs_object,
    create_bigquery_table,
    create_bigquery_dataset,
    check_bigquery_dataset_exists,
    check_bigquery_table_exists,
    append_df_to_bigquery_table,
    query_bq_to_dataframe,
)

__version__ = "0.1.0"

__all__ = [
    "log_printer",
    "initialise_cloud_logger",
    "gcp_access_secret",
    "read_cloud_scheduler_message",
    "append_prefix_to_gcs_files",
    "rename_prefix_of_gcs_files",
    "upload_json_to_gcs_bucket",
    "list_files_in_gcs",
    "download_content_from_gcs",
    "delete_gcs_object",
    "create_bigquery_table",
    "create_bigquery_dataset",
    "check_bigquery_dataset_exists",
    "check_bigquery_table_exists",
    "append_df_to_bigquery_table",
    "query_bq_to_dataframe",
]
