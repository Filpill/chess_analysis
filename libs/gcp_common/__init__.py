"""
GCP Common Utilities Library

Provides common GCP functions for Cloud Logging, Secret Manager, and Pub/Sub message handling.
"""

from .gcp_common import (
    log_printer,
    initialise_cloud_logger,
    gcp_access_secret,
    read_cloud_scheduler_message,
)

__version__ = "0.1.0"

__all__ = [
    "log_printer",
    "initialise_cloud_logger",
    "gcp_access_secret",
    "read_cloud_scheduler_message",
]
