import re
import json
import shlex
import base64
import subprocess
import google.cloud.logging as cloud_logging
from flask import Flask, request
from googleapiclient import discovery
from google.auth import default

app = Flask(__name__)

def initialise_cloud_logger(project_id):
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
 
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def create_instance_with_container(
    logger,
    INSTANCE_NAME,
    PROJECT_ID,
    MESSAGE_DATA,
    CONTAINER_IMAGE,
    SUB_NET,
    SERVICE_ACCOUNT,
    MACHINE_TYPE,
    BOOT_DISK_SIZE_GB,
    BOOT_DISK_TYPE,
    SCOPES
):

    zone_list = [
        "europe-west1-b",
        "europe-west1-c",
        "europe-west1-d",
        "europe-west2-a",
        "europe-west2-b",
        "europe-west2-c",
    ]

    for ZONE in zone_list:
        logger.log_text(f"Attempting to create VM in {ZONE}")

        vm_initialiser_script = f"""
            gcloud compute instances create-with-container {INSTANCE_NAME} \
              --project={PROJECT_ID} \
              --zone={ZONE} \
              --machine-type={MACHINE_TYPE} \
              --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet={SUB_NET} \
              --maintenance-policy=MIGRATE \
              --provisioning-model=STANDARD \
              --service-account={SERVICE_ACCOUNT} \
              --scopes={SCOPES} \
              --image=projects/cos-cloud/global/images/cos-stable-121-18867-0-94\
              --boot-disk-size={BOOT_DISK_SIZE_GB} \
              --boot-disk-type={BOOT_DISK_TYPE} \
              --boot-disk-device-name=instance-20250403-171730 \
              --container-image={CONTAINER_IMAGE} \
              --container-env=MESSAGE={MESSAGE_DATA} \
              --container-restart-policy=never \
              --container-privileged \
              --no-shielded-secure-boot \
              --shielded-vtpm \
              --shielded-integrity-monitoring \
              --labels=goog-ec-src=vm_add-gcloud,container-vm=cos-stable-121-18867-0-94
          """

        logger.log_text(f"VM Init Script: {vm_initialiser_script}")

        runner = subprocess.run(["bash", "-c", vm_initialiser_script], capture_output=True, text=True)
        logger.log_text(f"VM creation stdout: {runner.stdout}", severity="INFO")
        logger.log_text(f"VM creation stderr: {runner.stderr}", severity="WARNING")

        if "ZONE_RESOURCE_POOL_EXHAUSTED" not in runner.stderr:
            return runner  # Success or some other error — break and return

    logger.log_text("All zone attempts failed due to resource exhaustion.", severity="ERROR")
    return runner

@app.route("/", methods=["POST"])
def pubsub_handler(): 

    PROJECT_ID="checkmate-453316"
    SUB_NET="filip-vpc"
    MACHINE_TYPE="e2-medium"
    BOOT_DISK_SIZE_GB=10
    BOOT_DISK_TYPE="pd-balanced"
    SERVICE_ACCOUNT="startvm-sa@checkmate-453316.iam.gserviceaccount.com"
    SCOPES="https://www.googleapis.com/auth/cloud-platform"

    # Initialise logging object
    logger = initialise_cloud_logger(PROJECT_ID)

    try:
        # Get base64-encoded data from Pub/Sub message
        ENVELOPE = request.get_json()
        logger.log_text(f"Printing incoming cloud event for VM Initialiser: {ENVELOPE}", severity="INFO")
        if not ENVELOPE:
            logger.log_text("Invalid Pub/Sub message format", severity="ERROR")
            return "Bad Request", 400

        MESSAGE_DATA = ENVELOPE["message"]["data"]
        logger.log_text(f"MESSAGE_DATA before decoding: {MESSAGE_DATA}", severity="INFO")
        if not MESSAGE_DATA:
            logger.log_text("No data in Pub/Sub message", severity="ERROR")
            return "No data", 400

        PAYLOAD = base64.b64decode(MESSAGE_DATA).decode("utf-8")
        logger.log_text(f"Decoded Pub/Sub message payload: {PAYLOAD}", severity="INFO")

        # Parse the JSON log entry
        CLOUD_SCHEDULER_DICT = json.loads(PAYLOAD)

        # Extract the jobName from the message delivered by the cloud scheduler
        JOB_NAME = CLOUD_SCHEDULER_DICT["job_name"]

        # If anything missing - return a NULL value and print log
        if not JOB_NAME:
            logger.log_text("No jobName found in message sent by cloud scheduler", severity="ERROR")
            return "No Job Name", 400

        # Name for VM and Container Image to pull down
        INSTANCE_NAME=JOB_NAME.replace("_", "-")
        CONTAINER_IMAGE=f"europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/{JOB_NAME}:latest"

        # Run function for initialising VM with workload
        logger.log_text(f"Running VM initialiser script for cloud scheduler job: {JOB_NAME}...", severity="INFO")

        vm_creator = create_instance_with_container(
            logger,
            INSTANCE_NAME,
            PROJECT_ID,
            MESSAGE_DATA,
            CONTAINER_IMAGE,
            SUB_NET,
            SERVICE_ACCOUNT,
            MACHINE_TYPE,
            BOOT_DISK_SIZE_GB,
            BOOT_DISK_TYPE,
            SCOPES
        )

        print("VM Creation Complete!")

        return "OK", 200

    except Exception as e:
        logger.log_text(f"Error handling CloudEvent: {e}", severity="ERROR")

if __name__  == "__main__":
    app.run(host="0.0.0.0", port=8080)
