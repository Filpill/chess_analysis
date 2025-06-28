import re
import json
import base64
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
    instance_name,
    project_id,
    zone,
    container_image,
    subnet,
    service_account,
    machine_type="e2-medium",
    boot_disk_size_gb=10,
    boot_disk_type="pd-balanced",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
):
    credentials, _ = default()
    compute = discovery.build("compute", "v1", credentials=credentials)

    # Sanitize instance name
    instance_name = instance_name.replace("_", "-")
    region = "-".join(zone.split("-")[:-1])  # e.g., europe-west1-c → europe-west1

    # ✅ Correctly formatted, unindented YAML string
    container_declaration = f"""spec:
  containers:
    - name: {instance_name}
      image: {container_image}
      command: ["python3", "/app/main.py"]
      stdin: false
      tty: false
  restartPolicy: Never"""

    config = {
        "name": instance_name,
        "machineType": f"zones/{zone}/machineTypes/{machine_type}",
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": "projects/cos-cloud/global/images/cos-stable-117-18613-164-98",
                    "diskSizeGb": boot_disk_size_gb,
                    "diskType": f"zones/{zone}/diskTypes/{boot_disk_type}"
                },
                "deviceName": instance_name
            }
        ],
        "networkInterfaces": [
            {
                "subnetwork": f"regions/{region}/subnetworks/{subnet}",
                "stackType": "IPV4_ONLY",
                "networkTier": "PREMIUM"
            }
        ],
        "serviceAccounts": [
            {
                "email": service_account,
                "scopes": scopes
            }
        ],
        "scheduling": {
            "onHostMaintenance": "MIGRATE",
            "provisioningModel": "STANDARD"
        },
        "labels": {
            "goog-ec-src": "vm_add-gcloud",
            "container-vm": "cos-stable-117-18613-164-98"
        },
        "shieldedInstanceConfig": {
            "enableSecureBoot": False,
            "enableVtpm": True,
            "enableIntegrityMonitoring": True
        },
        "advancedMachineFeatures": {
            "enableNestedVirtualization": False
        },
        "metadata": {
            "items": [
                {
                    "key": "gce-container-declaration",
                    "value": container_declaration
                },
                {
                    "key": "serial-port-logging-enable",
                    "value": "true"
                }
            ]
        }
    }

    print("Sending container declaration:\n", container_declaration)  # 🧪 Optional debug

    request = compute.instances().insert(
        project=project_id,
        zone=zone,
        body=config
    )

    response = request.execute()
    return response

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
        INSTANCE_NAME=job_name
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

        print("Script complete!")

    except Exception as e:
        logger.log_text(f"Error handling CloudEvent: {e}", severity="ERROR")

