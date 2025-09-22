#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="gs://chess-deployments/*"
DEST_DIR="/scripts"

# Extract script name from Pub/Sub Message via Cloud Scheduler
MESSAGE="eyJlbmRfZGF0ZSI6IjIwMjUtMDMtMzEiLCJqb2JfbmFtZSI6InRlc3RfcHViX3N1Yl9tZXNzYWdlIiwic2NyaXB0X3NldHRpbmciOiJ0ZXN0Iiwic2V0dGluZzEiOiJBIiwic2V0dGluZzIiOiJCIiwic2V0dGluZzMiOiJDIiwic3RhcnRfZGF0ZSI6IjIwMjQtMDQtMDEifQ=="
DECODED_MESSAGE=$(echo "$MESSAGE" | base64 --decode)
echo $DECODED_MESSAGE
SCRIPT_NAME=$(echo "$DECODED_MESSAGE" | jq -r '.job_name')
echo "Running Script: $SCRIPT_NAME"
