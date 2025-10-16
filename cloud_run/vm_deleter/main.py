import os
import re
import json
import base64

import google.cloud.logging as cloud_logging
from googleapiclient import discovery
from flask import Flask, request, jsonify
from googleapiclient.errors import HttpError

app = Flask(__name__)

def initialise_cloud_logger(project_id):
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def delete_vm(project, zone, instance_name, logger):
    try:
        compute = discovery.build('compute', 'v1')
        request = compute.instances().delete(
            project=project,
            zone=zone,
            instance=instance_name
        )
        response = request.execute()
        logger.log_text(f"Project ID: {project} | Delete request sent for VM: {instance_name} | zone: {zone}", severity="INFO")
        return response

    except HttpError as e:
        if e.resp.status == 404:
            logger.log_text(f"VM '{instance_name}' not found in zone '{zone}'. It may already be deleted.", severity="WARNING")
            return None
        else:
            logger.log_text(f"Error deleting VM: {e}", severity="ERROR")
            raise

@app.route("/", methods=["POST"])
def pubsub_handler():

    # Initialise logging object
    PROJECT = "checkmate-453316"
    logger = initialise_cloud_logger(PROJECT)

    try:
        # Get base64-encoded data from Pub/Sub message via CloudEvent
        envelope = request.get_json()
        if not envelope:
            logger.log_text("No Pub/Sub message received", severity="ERROR")
            return "Missing data", 400

        message_data = envelope["message"]["data"]
        if not message_data:
            logger.log_text("No data found in the Pub/Sub message", severity="ERROR")
            return "Missing data", 400

        payload = base64.b64decode(message_data).decode("utf-8")
        logger.log_text(f"Decoded Pub/Sub message payload: {payload}", severity="INFO")

        # Parse the JSON log entry
        log_entry = json.loads(payload)

        # Extract the VM name and zone from from the log's jsonPayload._HOSTNAME and resource.labels.zone
        vm_name = log_entry["jsonPayload"]["_HOSTNAME"]
        zone    = log_entry["resource"]["labels"]["zone"]

        # If anything missing - return a NULL value and print log
        if not vm_name:
            logger.log_text("No _HOSTNAME found in log entry.", severity="ERROR")
            return "No VM Name found in logs", 400

        if not zone:
            logger.log_text("No resource.labels.zone found in log entry.", severity="ERROR")
            return "No VM Zone found in logs", 400

        # Delete targeted VM Instance        
        logger.log_text(f"Deleting VM: {vm_name} | zone: {zone}", severity="WARNING")
        delete_vm(PROJECT, zone, vm_name, logger)
        return "VM deletion triggered", 200

    except Exception as e:
        logger.log_text(f"Error handling CloudEvent: {e}", severity="ERROR")
        return "Internal Server Error", 500

if __name__  == "__main__":
    app.run(host="0.0.0.0", port=8080)
