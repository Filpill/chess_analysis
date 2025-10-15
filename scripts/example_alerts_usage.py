"""
Example script demonstrating how to use the alerts_lib package

This shows the new way to import and use alerts functionality.
"""

import os
import sys
sys.path.append(f"./functions")
from shared_func import initialise_cloud_logger
from shared_func import read_cloud_scheduler_message

# New way: Import from the installed alerts_lib package
from alerts_lib import (
    gcp_access_secret,
    load_alerts_environmental_config,
    create_bq_run_monitor_datasets,
    append_to_trigger_bq_dataset,
    global_excepthook,
)

def main():
    # Configure alerts environment (loads from GCP Secret Manager)
    env_vars = load_alerts_environmental_config()

    # ----- Project and Logger -----
    project_id = "checkmate-453316"
    os.environ["PROJECT_ID"] = project_id
    logger = initialise_cloud_logger(project_id)
    logger.log_text("EMAIL/DISCORD -- ALERT TEST -- Script Initilisation", severity="WARNING")


    # ----- Pub/Sub Message Sent Via Cloud Scheduler -----
    cloud_scheduler_dict = read_cloud_scheduler_message()
    logger.log_text(f"EMAIL/DISCORD -- READING CLOUD SCHEDULER MESSAGE: {cloud_scheduler_dict}", severity="WARNING")

    # ----- APP_ENV Configuration -----
    if cloud_scheduler_dict is not None:
        os.environ["APP_ENV"] = cloud_scheduler_dict["app_env"]
        os.environ["TO_ADDRS"] = cloud_scheduler_dict["to_addrs"]
    if cloud_scheduler_dict is None:
        os.environ["APP_ENV"] = "DEV/TEST"
        os.environ["TO_ADDRS"] = os.getenv("SMTP_USER")

    if os.getenv("APP_ENV") == "PROD":
        os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord,bq" 
    else:
        os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord,bq" # Alert setting for non-prod loads

    # Install the global exception hook (this catches all unhandled exceptions)
    sys.excepthook = global_excepthook

    # Create monitoring datasets (only needed once per project)
    create_bq_run_monitor_datasets(project_id, logger)

    # Record that this run was triggered
    append_to_trigger_bq_dataset(project_id, logger)

    # Your actual script logic goes here
    logger.log_text("Alerts configured! Run ID: {env_vars['RUN_ID']}", severity="INFO")

    # Any unhandled exceptions will automatically trigger alerts
    # Example: This will trigger an alert
    logger.log_text("EMAIL ALERT TEST -- Triggering Manual Failure...", severity="ERROR")
    1/0

if __name__ == "__main__":
    main()
