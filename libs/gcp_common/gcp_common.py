"""
GCP Common Utilities

Common functions for interacting with Google Cloud Platform services.
"""

import os
import json
import base64
import numpy as np
import pandas as pd
from typing import List
import google.cloud.logging as cloud_logging
from google.cloud import secretmanager, storage, bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime, timezone


def log_printer(msg, logger, severity="INFO", console_print=True):
    """
    Log message to both Cloud Logging and console.

    Args:
        msg: Message to log
        logger: Cloud Logging logger instance
        severity: Log severity level (INFO, WARNING, ERROR, etc.)
        console_print: Whether to also print to console
    """
    logger.log_text(msg, severity=severity)

    if console_print:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        formatter = f"[{severity}] {timestamp}:"
        print(f"{formatter} {msg}")


def initialise_cloud_logger(project_id: str):
    """
    Initialize a Cloud Logging logger for the given project.

    Args:
        project_id: GCP project ID

    Returns:
        Cloud Logging logger instance
    """
    client = cloud_logging.Client(project=project_id)
    logger = client.logger(__name__)
    return logger


def gcp_access_secret(project_id, secret_id, version_id="latest"):
    """
    Access a secret from GCP Secret Manager.

    Args:
        project_id: GCP project ID
        secret_id: Secret name/ID
        version_id: Secret version (default: "latest")

    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')


def read_cloud_scheduler_message():
    """
    Read and decode a Cloud Scheduler message from Pub/Sub.

    Reads the MESSAGE environment variable (base64-encoded JSON),
    decodes it, and returns the parsed dictionary.

    Returns:
        Dictionary containing the Cloud Scheduler message, or None if not present
    """
    message = os.getenv("MESSAGE")
    if message is not None:
        decoded_message = base64.b64decode(message).decode("utf-8")
        cloud_scheduler_dict = json.loads(decoded_message)
        return cloud_scheduler_dict
    else:
        return None


def append_prefix_to_gcs_files(bucket_name, prefix, excluded_prefixes, logger=None):
    """
    Append a prefix to GCS file names, excluding specified prefixes.

    Args:
        bucket_name: Name of the GCS bucket
        prefix: Prefix to append to file names
        excluded_prefixes: List of prefixes to exclude from renaming
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    # The for loop will exlude any files that should not be targeted in the renaming
    for blob in blobs:
        if any(blob.name.startswith(f"{prefix}/") for prefix in excluded_prefixes):
            if logger:
                log_printer("Skipping {blob.name} | Excluded from renaming process", logger)
            continue

        new_name = f"{prefix}/{blob.name}"
        bucket.rename_blob(blob, new_name)
        if logger:
            log_printer(f"Renamed {blob.name} -> {new_name}", logger)


def rename_prefix_of_gcs_files(bucket_name, old_prefix, new_prefix, logger=None):
    """
    Rename the prefix of GCS files by copying and deleting.

    Args:
        bucket_name: Name of the GCS bucket
        old_prefix: Old prefix to replace
        new_prefix: New prefix to use
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=old_prefix)

    for blob in blobs:
        new_name = blob.name.replace(old_prefix, new_prefix, 1)
        new_blob = bucket.copy_blob(blob, bucket, new_name)
        blob.delete()
        if logger:
            log_printer(f"Renamed {blob.name} -> {new_name}", logger)
        else:
            print(f"Renamed {blob.name} -> {new_name}")


def upload_json_to_gcs_bucket(bucket_name, object_name, data, logger=None):
    """
    Upload JSON data to a GCS bucket.

    Args:
        bucket_name: Name of the GCS bucket
        object_name: Name of the object to create in GCS
        data: Response object with .json() method
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(json.dumps(data.json()), content_type="application/json")
    if logger:
        log_printer(f'Success | Uploaded {object_name} to GCS bucket: {bucket_name}', logger)


def list_files_in_gcs(bucket_name, logger=None):
    """
    List all files in a GCS bucket.

    Args:
        bucket_name: Name of the GCS bucket
        logger: Optional Cloud Logging logger instance

    Returns:
        List of file names in the bucket
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    file_list = [blob.name for blob in blobs]
    if logger:
        log_printer(f'Listing Files in GCS bucket: {bucket_name}', logger)
    return file_list


def download_content_from_gcs(gcs_filename, bucket_name, logger=None):
    """
    Download content from a GCS object as text.

    Args:
        gcs_filename: Name of the file in GCS
        bucket_name: Name of the GCS bucket
        logger: Optional Cloud Logging logger instance

    Returns:
        Content of the file as string
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_filename)

    if logger:
        log_printer(f"Downloading from GCS: {gcs_filename}", logger)
    content = blob.download_as_text()
    return content


def delete_gcs_object(gcs_filename, bucket_name, logger=None):
    """
    Delete an object from a GCS bucket.

    Args:
        gcs_filename: Name of the file to delete
        bucket_name: Name of the GCS bucket
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_filename)

    blob.delete()
    if logger:
        log_printer(f"Deleted object {gcs_filename} from bucket {bucket_name}", logger)


def create_bigquery_table(
    table_id: str,
    schema: List[bigquery.SchemaField],
    logger=None,
    time_partitioning_field: str = None,
) -> bigquery.Table:
    """
    Create a BigQuery table with optional time partitioning.

    Args:
        table_id: Full table ID (project.dataset.table)
        schema: List of BigQuery schema fields
        logger: Optional Cloud Logging logger instance
        time_partitioning_field: Optional field name for time partitioning

    Returns:
        Created BigQuery table object
    """
    client = bigquery.Client()
    table = bigquery.Table(table_id, schema=schema)

    # Add partitioning if specified
    if time_partitioning_field:
        if logger:
            log_printer(f'Adding paritioning scheme against {time_partitioning_field}', logger)
        table.time_partitioning = bigquery.TimePartitioning(
              type_=bigquery.TimePartitioningType.DAY
            , field=time_partitioning_field
        )

    table = client.create_table(table)
    if logger:
        log_printer(f"Created table {table_id}", logger)
    return table


def create_bigquery_dataset(project_id: str, dataset_id: str, location: str, logger=None):
    """
    Create a BigQuery dataset.

    Args:
        project_id: GCP project ID
        dataset_id: Dataset ID
        location: Dataset location (e.g., 'US', 'EU')
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    client = bigquery.Client()
    full_id = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(full_id)
    dataset.location = location

    dataset = client.create_dataset(dataset, timeout=30)  # timeout in seconds
    if logger:
        log_printer(f"Created dataset {full_id}", logger)


def check_bigquery_dataset_exists(dataset_id: str, logger=None) -> bool:
    """
    Check if a BigQuery dataset exists.

    Args:
        dataset_id: Full dataset ID (project.dataset)
        logger: Optional Cloud Logging logger instance

    Returns:
        True if dataset exists, False otherwise
    """
    client = bigquery.Client()
    try:
        client.get_dataset(dataset_id)
        if logger:
            log_printer(f"Dataset {dataset_id} already exists", logger)
        return True

    except NotFound:
        if logger:
            log_printer(f"Dataset {dataset_id} doesn't exists", logger)
        return False


def check_bigquery_table_exists(table_id: str, logger=None) -> bool:
    """
    Check if a BigQuery table exists.

    Args:
        table_id: Full table ID (project.dataset.table)
        logger: Optional Cloud Logging logger instance

    Returns:
        True if table exists, False otherwise
    """
    client = bigquery.Client()
    try:
        client.get_table(table_id)
        if logger:
            log_printer(f"Table {table_id} already exists", logger)
        return True

    except NotFound:
        if logger:
            log_printer(f"Table {table_id} doesn't exists", logger)
        return False


def append_df_to_bigquery_table(df: pd.DataFrame, table_id: str, logger=None) -> None:
    """
    Append a pandas DataFrame to a BigQuery table.

    Args:
        df: Pandas DataFrame to append
        table_id: Full table ID (project.dataset.table)
        logger: Optional Cloud Logging logger instance

    Returns:
        None
    """
    # Configure the query job to append results
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
          write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    # Load the DataFrame into BigQuery
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete

    if logger is not None:
        log_printer(f"{len(df)} records appended to {table_id}", logger)


def query_bq_to_dataframe(query: str, location: str, logger=None) -> pd.DataFrame:
    """
    Execute a BigQuery query and return results as a pandas DataFrame.

    Args:
        query: SQL query string
        location: Query location (e.g., 'US', 'EU')
        logger: Optional Cloud Logging logger instance

    Returns:
        Pandas DataFrame with query results
    """
    client = bigquery.Client()
    if logger:
        log_printer(f"Executing query: {query}", logger)

    # Execute the query and get the result as a pandas DataFrame
    query_job = client.query(query, location=location)

    # Log job status information
    job_id = query_job.job_id
    if logger:
        log_printer(f"Query job started with job ID: {job_id}", logger)

    # Wait for the job to complete and convert the results to DataFrame
    df = query_job.to_dataframe()

    # Log the size of the resulting DataFrame
    rows = len(df)
    cols = len(df.columns)
    if logger:
        log_printer(f"Query completed successfully. DataFrame created with {rows} rows and {cols} columns.", logger)

    return df
