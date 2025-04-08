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

from shared_func import log_printer

def upload_json_to_gcs_bucket(bucket_name, object_name, data, logger):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(json.dumps(data.json()), content_type="application/json")
    log_printer(f'Success | Uploaded {object_name} to GCS bucket: {bucket_name}', logger)

def list_files_in_gcs(bucket_name, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    file_list = [blob.name for blob in blobs]
    log_printer(f'Listing Files in GCS bucket: {bucket_name}', logger)
    return file_list 

def download_content_from_gcs(gcs_filename, bucket_name, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_filename)
    
    log_printer(f"Downloading from GCS: {gcs_filename}",logger)
    content = blob.download_as_text()
    return content

def delete_gcs_object(gcs_filename, bucket_name, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_filename)

    blob.delete()
    log_printer(f"Deleted object {gcs_filename} from bucket {bucket_name}",logger)
