#!/bin/sh
PROJECT_ID="checkmate-453316"
ZONE="europe-west1-c"
INSTANCE_NAME="vm-chess-ingestion"
SUB_NET="filip-vpc"
MACHINE_TYPE="e2-medium"
SERVICE_ACCOUNT="startvm-sa@checkmate-453316.iam.gserviceaccount.com"
CONTAINER_IMAGE="europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/chess_ingestion_processor:v001"
SCOPES="https://www.googleapis.com/auth/cloud-platform"

gcloud compute instances create-with-container $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$SUB_NET \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=$SERVICE_ACCOUNT \
    --scopes=$SCOPES \
    --image=projects/cos-cloud/global/images/cos-stable-117-18613-164-98 \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-balanced \
    --boot-disk-device-name=instance-20250403-171730 \
    --container-image=$CONTAINER_IMAGE \
    --container-restart-policy=never \
    --container-privileged \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=goog-ec-src=vm_add-gcloud,container-vm=cos-stable-117-18613-164-98
