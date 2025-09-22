#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="gs://chess-deployments/*"
DEST_DIR="/scripts"

# Activate Service Account -- (dev purposes only)
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

echo "Downloading contents of ${BUCKET_NAME} → ${DEST_DIR}"
gsutil -m cp -r "$BUCKET_NAME" "$DEST_DIR/"
echo "Download complete"

# Install python dependencies
pip install -r /scripts/requirements.txt --break-system-packages

# Extract script name from Pub/Sub Message via Cloud Scheduler
SCRIPT_NAME=$(echo "$MESSAGE" | jq -r '.script_name')
echo "Running Script: $SCRIPT_NAME"

if [[ -z "$SCRIPT_NAME" ]]; then
  echo "ERROR: script_name key not found in MESSAGE"
  exit 1
fi

# Run Python Script
python /scripts/$SCRIPT_NAME
