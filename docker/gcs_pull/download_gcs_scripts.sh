#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="gs://chess-deployments/*"
DEST_DIR="./app"

echo "Downloading contents of gs://${BUCKET_NAME} → ${DEST_DIR}"

# Make sure destination exists
mkdir -p "$DEST_DIR"

# -m for parallel (faster), -r for recursive
gsutil -m cp -r "$DEST_DIR/"

echo "Download complete"
