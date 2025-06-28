import re
import json
import base64
import subprocess
import functions_framework
import google.cloud.logging as cloud_logging
from googleapiclient import discovery
from google.auth import default

def initialise_cloud_logger(project_id):
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def create_instance_with_container(
    INSTANCE_NAME,
    PROJECT_ID,
    ZONE,
    CONTAINER_IMAGE,
    SUB_NET,
    SERVICE_ACCOUNT,
    MACHINE_TYPE,
    BOOT_DISK_SIZE_GB,
    BOOT_DISK_TYPE,
    SCOPES
):
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
          --image=projects/cos-cloud/global/images/cos-stable-117-18613-164-98 \
          --boot-disk-size={BOOT_DISK_SIZE_GB} \
          --boot-disk-type={BOOT_DISK_TYPE} \
          --boot-disk-device-name=instance-20250403-171730 \
          --container-image={CONTAINER_IMAGE} \
          --container-restart-policy=never \
          --container-privileged \
          --no-shielded-secure-boot \
          --shielded-vtpm \
          --shielded-integrity-monitoring \
          --labels=goog-ec-src=vm_add-gcloud,container-vm=cos-stable-117-18613-164-98
      """

    runner = subprocess.run(["bash", "-c", vm_initialiser_script], capture_output=True, text=True)
    return runner

@functions_framework.cloud_event 
def pubsub_handler(cloud_event): 

    PROJECT_ID="checkmate-453316"
    ZONE="europe-west1-c"
    SUB_NET="filip-vpc"
    MACHINE_TYPE="e2-medium"
    BOOT_DISK_SIZE_GB=10
    BOOT_DISK_TYPE="pd-balanced"
    SERVICE_ACCOUNT="startvm-sa@checkmate-453316.iam.gserviceaccount.com"
    SCOPES="https://www.googleapis.com/auth/cloud-platform"

    # Initialise logging object
    logger = initialise_cloud_logger(PROJECT_ID)

    # Raw the incoming Pub/Sub message
    logger.log_text(f"Printing incoming cloud event for VM Initialiser: {cloud_event}", severity="INFO")

    try:
        # Get base64-encoded data from Pub/Sub message via CloudEvent
        message_data = cloud_event.data["message"]["data"]
        payload = base64.b64decode(message_data).decode("utf-8")
        logger.log_text(f"Decoded Pub/Sub message payload: {payload}", severity="INFO")

        # Parse the JSON log entry
        cloud_scheduler_message = json.loads(payload)

        # Extract the jobName from the message delivered by the cloud scheduler
        job_name = cloud_scheduler_message["jobName"]

        # If anything missing - return a NULL value and print log
        if not job_name:
            logger.log_text("No jobName found in message sent by cloud scheduler", severity="ERROR")
            return

        # Name for VM and Container Image to pull down
        JOB_NAME=job_name
        INSTANCE_NAME=job_name.replace("_", "-")
        CONTAINER_IMAGE=f"europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/{INSTANCE_NAME}:latest"

        # Run function for initialising VM with workload
        logger.log_text(f"Running VM initialiser script for cloud scheduler job: {INSTANCE_NAME}...", severity="INFO")

        vm_creator = create_instance_with_container(
            INSTANCE_NAME,
            PROJECT_ID,
            ZONE,
            CONTAINER_IMAGE,
            SUB_NET,
            SERVICE_ACCOUNT,
            MACHINE_TYPE,
            BOOT_DISK_SIZE_GB,
            BOOT_DISK_TYPE,
            SCOPES
        )

        print("VM Creation Complete!")

    except Exception as e:
        logger.log_text(f"Error handling CloudEvent: {e}", severity="ERROR")

