import json
import logging
import google.cloud.logging as cloud_logging
from googleapiclient import discovery
from google.oauth2 import service_account
from google.cloud import secretmanager

def initialise_cloud_logger(PROJECT_ID):
    client = cloud_logging.Client(project=PROJECT_ID)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def gcp_access_secret(PROJECT_ID, SECRET_ID, VERSION_ID="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/{VERSION_ID}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

def main():

    SECRET_ID     = 'VM_SERVICE_ACCOUNT'
    PROJECT_ID    = "checkmate-453316"
    ZONE          = "europe-west2-b"
    INSTANCE_NAME = "chess-ingestion-vm"
    MACHINE_TYPE  = "e2-micro"
    VPC_NAME      = "filip-vpc"
    SUBNET_NAME   = "filip-vpc"

    # Initialise Logger Object
    logger = initialise_cloud_logger(PROJECT_ID)
    logger.log_text(f"Project: {PROJECT_ID} | Initialising VM Script and Deploying VM", severity="INFO")

    service_account_creds = gcp_access_secret(PROJECT_ID, SECRET_ID)
    credentials = service_account.Credentials.from_service_account_file(service_account_creds)
    compute = discovery.build('compute', 'v1', credentials=credentials)

    config = {
        "name": INSTANCE_NAME,
        "machineType": f"zones/{ZONE}/machineTypes/{MACHINE_TYPE}",
        "disks": [{
            "boot": True,
            "initializeParams": {
                "sourceImage": "projects/debian-cloud/global/images/family/debian-12"
            }
        }],
        "networkInterfaces": [{
            "network": f"projects/{PROJECT_ID}/global/networks/{VPC_NAME}",
            "subnetwork": f"projects/{PROJECT_ID}/regions/{ZONE[:-2]}/subnetworks/{SUBNET_NAME}",
            "accessConfigs": [{
                "type": "ONE_TO_ONE_NAT",  # Required for external access
                "name": "External NAT"
            }]
        }]
    }

    operation = compute.instances().insert(
        project=PROJECT_ID,
        zone=ZONE,
        body=config
    ).execute()

    return logger.log_text(f"Instance {INSTANCE_NAME} creation started: {operation}", severity="INFO")

if __name__ == "__main__":
    main()
