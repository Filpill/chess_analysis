"""
GCP Common Utilities

Common functions for interacting with Google Cloud Platform services.
"""

import os
import json
import base64
import google.cloud.logging as cloud_logging
from google.cloud import secretmanager
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
