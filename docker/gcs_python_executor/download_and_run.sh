#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="gs://chess-deployments/*"
DEST_DIR="/scripts"

# Activate Service Account
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

echo "Downloading contents of ${BUCKET_NAME} → ${DEST_DIR}"
gsutil -m cp -r "$BUCKET_NAME" "$DEST_DIR/"
echo "Download complete"

# Install python dependencies
pip install -r /scripts/requirements.txt --break-system-packages

# Run Python Script
python /scripts/gcs_chess_ingestion.py
