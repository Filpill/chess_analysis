#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="gs://chess-deployments/*"
DEST_DIR="/app"

# Safe access with default empty string so -u doesn't explode
GAC_PATH="${GOOGLE_APPLICATION_CREDENTIALS:-}"

if [[ -n "$GAC_PATH" ]]; then
  echo "INFO: Activating service account from $GAC_PATH"
  gcloud auth activate-service-account --key-file="$GAC_PATH"
else
  echo "INFO: GOOGLE_APPLICATION_CREDENTIALS not set; assuming Workload Identity / ADC"
  # On Cloud Run, this is normal. Ensure the runtime service account has the right IAM roles.
fi

echo "Downloading contents of ${BUCKET_NAME} → ${DEST_DIR}"
gsutil -m cp -r "$BUCKET_NAME" "$DEST_DIR/"
echo "Download complete"

# Install python dependencies using uv sync
echo "Installing dependencies with uv sync..."
cd /app
uv sync --frozen --no-dev
echo "Dependencies installed successfully"

# Activate virtual environment created by uv sync
export PATH="/app/.venv/bin:$PATH"

# Extract script name from Pub/Sub Message via Cloud Scheduler
DECODED_MESSAGE=$(echo "$MESSAGE" | base64 --decode)
SCRIPT_NAME=$(echo "$DECODED_MESSAGE" | jq -r '.script_name')
echo "Running Script: $SCRIPT_NAME"

if [[ -z "$SCRIPT_NAME" ]]; then
  echo '{"severity":"ERROR","message":"script_name key not found in $MESSAGE after cloud scheduler trigger"}'
  exit 1
fi

# Run Python Script (using venv python, maintaining repo structure)
python /app/scripts/$SCRIPT_NAME
