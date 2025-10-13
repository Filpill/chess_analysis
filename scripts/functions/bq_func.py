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

def append_df_to_bigquery_table(df: pd.DataFrame, table_id: str, logger=None) -> None:

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
