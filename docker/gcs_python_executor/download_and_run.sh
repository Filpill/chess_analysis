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
#MESSAGE="ewogICJzY3JpcHRfbmFtZSI6ICJ0ZXN0X3B1Yl9zdWJfbWVzc2FnZS5weSIsCiAgImpvYl9uYW1lIjogImdjc19weXRob25fZXhlY3V0b3IiLAogICJzY3JpcHRfc2V0dGluZyI6ICJ0ZXN0IiwKICAic3RhcnRfZGF0ZSI6ICIyMDI0LTA0LTAxIiwKICAiZW5kX2RhdGUiOiAiMjAyNS0wMy0zMSIsCiAgInNldHRpbmcxIjogIkEiLAogICJzZXR0aW5nMiI6ICJCIiwKICAic2V0dGluZzMiOiAiQyIKfQo="
DECODED_MESSAGE=$(echo "$MESSAGE" | base64 --decode)
SCRIPT_NAME=$(echo "$DECODED_MESSAGE" | jq -r '.script_name')
echo "Running Script: $SCRIPT_NAME"

if [[ -z "$SCRIPT_NAME" ]]; then
  echo '{"severity":"ERROR","message":"script_name key not found in $MESSAGE after cloud scheduler trigger"}'
  exit 1
fi

# Run Python Script
python /scripts/$SCRIPT_NAME
