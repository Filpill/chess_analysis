import sys
import json
import time
import random
import requests
import google.cloud.logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging

from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from google.cloud import storage
from itertools import product

def log_printer(msg, logger, severity="INFO", console_print=True):

    logger.log_text(msg, severity=severity)

    if console_print == True:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        formatter = f"[{severity}] {timestamp}:"
        print(f"{formatter} {msg}")

def initialise_cloud_logger(project_id: str):
    client = cloud_logging.Client(project=project_id)
    logger = client.logger(__name__)
    return logger


def gcp_access_secret(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')
