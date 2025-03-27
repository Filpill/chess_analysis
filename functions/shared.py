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
