# Create storage bucket for object related to deployments
resource "google_storage_bucket" "static" {
    name          = var.deployment_bucket
    location      = var.bucket_region
    storage_class = "STANDARD"

    uniform_bucket_level_access = true
}

# Gather all files needed for deployment
locals {
    files = [
        { file_path = var.ingestion_script },
        { file_path = var.function_gcs_ingestion },
        { file_path = var.function_shared },
        { file_path = var.ingestion_input_config },
    ]
}

# Upload deployment objects to GCS deployment bucket
resource "google_storage_bucket_object" "objects" {
    for_each = { for file in local.files : file.file_path => file }

    name    = each.value.file_path
    source  = each.value.file_path
    bucket  = google_storage_bucket.static.id
}

# Create Pub/Sub Topic for launching a VM Instance
resource "google_pubsub_topic" "start_vm_topic" {
    name = var.vm_pubsub_topic
}

# Create a Cloud Scheduler Job
resource "google_cloud_scheduler_job" "gcs_chess_ingestion_job" {
    paused        = false
    name          = "gcs_chess_ingestion_job"
    region        = var.job_region
    description   = "Chess API Data Ingestion Job to GCS"
    schedule      = "0 0 3 * *"
    pubsub_target {
        topic_name = resource.google_pubsub_topic.start_vm_topic.id
        data       = filebase64("./pipelines/gcs_chess_ingestion_job_config.json")
    }
}
