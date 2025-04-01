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
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def upload_json_to_gcs_bucket(bucket_name, object_name, data, logger):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(json.dumps(data.json()), content_type="application/json")
    logger.log_text(f'Success | Uploaded {object_name} to GCS bucket: {bucket_name}', severity="INFO")

def list_files_in_gcs(bucket_name, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    file_list = [blob.name for blob in blobs]
    logger.log_text(f'Listing Files in GCS bucket: {bucket_name}', severity="INFO")
    return file_list 
