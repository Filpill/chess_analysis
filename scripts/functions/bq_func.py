import sys
import json
import numpy as np
import pandas as pd
import datetime as dt
from typing import List

import google.cloud.logging as cloud_logging
from google.cloud import bigquery
from google.cloud import storage
from google.cloud.exceptions import NotFound

from shared_func import log_printer

def create_bigquery_table(
    table_id: str,
    schema: List[bigquery.SchemaField],
    logger,
    time_partitioning_field: str = None,
) -> bigquery.Table:

    client = bigquery.Client()
    table = bigquery.Table(table_id, schema=schema)

    # Add partitioning if specified
    if time_partitioning_field:
        log_printer(f'Adding paritioning scheme against {time_partitioning_field}', logger)
        table.time_partitioning = bigquery.TimePartitioning(
              type_=bigquery.TimePartitioningType.DAY
            , field=time_partitioning_field
        )

    table = client.create_table(table)
    log_printer(f"Created table {table_id}", logger)
    return table

def create_bigquery_dataset(project_id: str ,dataset_id: str, location: str, logger):
    client = bigquery.Client()
    full_id = f"{project_id}.{dataset_id}"   
    dataset = bigquery.Dataset(full_id)
    dataset.location = location
 
    dataset = client.create_dataset(dataset, timeout=30)  # timeout in seconds
    log_printer(f"Created dataset {full_id}", logger)

def check_bigquery_dataset_exists(dataset_id: str, logger) -> bool:

    client = bigquery.Client()
    try:
        client.get_dataset(dataset_id)
        log_printer(f"Dataset {dataset_id} already exists", logger)
        return True

    except NotFound:
        log_printer(f"Dataset {dataset_id} doesn't exists", logger)
        return False


def check_bigquery_table_exists(table_id: str, logger) -> bool:

    client = bigquery.Client()
    try:
        client.get_table(table_id)
        log_printer(f"Table {table_id} already exists", logger)
        return True

    except NotFound:
        log_printer(f"Table {table_id} doesn't exists", logger)
        return False

def append_df_to_bigquery_table(df: pd.DataFrame, table_id: str, logger) -> None:

    # Configure the query job to append results
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
          write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    # Load the DataFrame into BigQuery
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete
    log_printer(f"{len(df)} records appended to {table_id}", logger)


def query_bq_to_dataframe(
        query: str, location: str, logger: cloud_logging.Logger
) -> pd.DataFrame:

    client = bigquery.Client()
    log_printer(f"Executing query: {query}", logger)

    # Execute the query and get the result as a pandas DataFrame
    query_job = client.query(query, location=location)

    # Log job status information
    job_id = query_job.job_id
    log_printer(f"Query job started with job ID: {job_id}", logger)

    # Wait for the job to complete and convert the results to DataFrame
    df = query_job.to_dataframe()

    # Log the size of the resulting DataFrame
    rows = len(df)
    cols = len(df.columns)
    log_printer(f"Query completed successfully. DataFrame created with {rows} rows and {cols} columns.", logger)

    return df


def create_bq_run_monitor_datasets(project_id, logger):
    # Definining Schema of Runs Being Triggered/Failed in Python
    location = "EU"
    dataset_name = f"00_pipeline_monitor"
    if check_bigquery_dataset_exists(dataset_name, logger) == False:
        create_bigquery_dataset(project_id, dataset_name, location, logger)

    table_name = "runs_triggered"
    table_runs_triggered = f"{project_id}.{dataset_name}.{table_name}"

    schema_runs_triggered = [
        bigquery.SchemaField(name="run_id",         field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        bigquery.SchemaField(name="run_date",       field_type="DATE",       mode="REQUIRED",  description="Date of the pipeline run"),
        bigquery.SchemaField(name="run_dt",         field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the pipeline run"),
        bigquery.SchemaField(name="script_name",    field_type="STRING",     mode="REQUIRED",  description="Name of script"),
        bigquery.SchemaField(name="environment",    field_type="STRING",     mode="REQUIRED",  description="Name of environement e.g.: PROD/DEV/TEST"),
        bigquery.SchemaField(name="hostname",       field_type="STRING",     mode="REQUIRED",  description="Name of machine running script"),
        bigquery.SchemaField(name="python_version", field_type="STRING",     mode="REQUIRED",  description="Python version used during runtime"),
    ]
    loading_time_partitioning_field ="run_date"

    if check_bigquery_table_exists(table_runs_triggered, logger) == False:
        create_bigquery_table(table_runs_triggered, schema_runs_triggered, logger, loading_time_partitioning_field)

    table_name = "runs_failed"
    table_runs_failed = f"{project_id}.{dataset_name}.{table_name}"

    schema_runs_failed = [
        bigquery.SchemaField(name="run_id",          field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        bigquery.SchemaField(name="run_failed_date", field_type="DATE",       mode="REQUIRED",  description="Date of the failed pipeline run"),
        bigquery.SchemaField(name="run_failed_dt",   field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the failed pipeline run"),
        bigquery.SchemaField(name="failed_filename", field_type="STRING",     mode="REQUIRED",  description="Name of file that failed"),
        bigquery.SchemaField(name="exception_type",  field_type="STRING",     mode="REQUIRED",  description="Type of exception"),
        bigquery.SchemaField(name="exception_value", field_type="STRING",     mode="REQUIRED",  description="Value of exception"),
        bigquery.SchemaField(name="stack_trace",     field_type="STRING",     mode="REQUIRED",  description="Details of error produced"),
    ]
    loading_time_partitioning_field ="run_failed_date"

    if check_bigquery_table_exists(table_runs_failed, logger) == False:
        create_bigquery_table(table_runs_failed, schema_runs_failed, logger, loading_time_partitioning_field)
