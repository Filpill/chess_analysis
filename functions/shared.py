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

def initialise_cloud_logger(project_id: str):
    logging_client = cloud_logging.Client(project=project_id)
    logging_client.setup_logging()
    logger = logging.getLogger(__name__)
    logger.propagate = True
    return logger

def upload_json_to_gcs_bucket(bucket_name, object_name, data, logger):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(json.dumps(data.json()), content_type="application/json")
    logger.info(f'Success | Uploaded {object_name} to GCS bucket: {bucket_name}')

def list_files_in_gcs(bucket_name, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    file_list = [blob.name for blob in blobs]
    return file_list 

def exponential_backoff_request(url, headers, logger, max_retries=5, base_delay=1, max_delay=30):

    retries = 0
    while retries < max_retries:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        
        wait_time = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
        logger.warning(f"Retry {retries + 1}/{max_retries} | URL: {url} | Waiting {wait_time:.2f} seconds before retrying...")
        time.sleep(wait_time)
        retries += 1
    
    logger.warning("Max retries reached. Request failed for {url}")
    return None

