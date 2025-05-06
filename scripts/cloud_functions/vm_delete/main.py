import re
import json
import base64
import functions_framework
import google.cloud.logging as cloud_logging
from googleapiclient import discovery

PROJECT = "checkmate-453316"
ZONE = "europe-west1-c"

def initialise_cloud_logger(project_id):
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def delete_vm(project, zone, instance_name, logger):
    compute = discovery.build('compute', 'v1')
    request = compute.instances().delete(
        project=project,
        zone=zone,
        instance=instance_name
    )
    response = request.execute()
    logger.log_text(f"Delete request sent for VM: {instance_name}", severity="INFO")
    return response

@functions_framework.cloud_event
def pubsub_handler(cloud_event):

    # Initialise logging object
    logger = initialise_cloud_logger(PROJECT)

    # Decode the incoming Pub/Sub message
    logger.log_text(f"Printing incoming cloud event: {cloud_event}", severity="INFO")

    try:
        # Get base64-encoded data from Pub/Sub message via CloudEvent
        message_data = cloud_event.data["message"]["data"]
        payload = base64.b64decode(message_data).decode("utf-8")
        logger.log_text(f"Decoded Pub/Sub message payload: {payload}", severity="INFO")

        # Parse the JSON log entry
        log_entry = json.loads(payload)

        # Extract the VM name from the log's jsonPayload._HOSTNAME
        vm_name = log_entry.get("jsonPayload", {}).get("_HOSTNAME")
        if not vm_name:
            logger.log_text("No _HOSTNAME found in log entry.", severity="ERROR")
            return

        logger.log_text(f"Deleting VM: {vm_name}", severity="WARNING")
        delete_vm(PROJECT, ZONE, vm_name, logger)

    except Exception as e:
        logger.log_text(f"Error handling CloudEvent: {e}", severity="ERROR")
