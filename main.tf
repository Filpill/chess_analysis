provider "google" {
    project = var.project_id
}

# Create storage bucket for object related to deployments
resource "google_storage_bucket" "static" {
    name          = var.deployment_bucket_name
    location      = "EU"
    storage_class = "STANDARD"

    uniform_bucket_level_access = true
}

# Gather all files needed for deployment
locals {
    files = [
        { file_path = "scripts/gcs_chess_ingestion.ipynb" },
        { file_path = "functions/gcs_ingestion.py" },
        { file_path = "functions/shared.py" },
        { file_path = "inputs/gcs_ingestion_settings.json" },
    ]
}

# Upload deployment objects to GCS deployment bucket
resource "google_storage_bucket_object" "objects" {
    for_each = { for file in local.files : file.file_path => file }

    name    = each.value.file_path
    source  = each.value.file_path
    bucket  = google_storage_bucket.static.id
}
