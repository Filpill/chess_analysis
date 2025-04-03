#============================================
# -------Script Deployment Resources---------
#============================================
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
        { file_path = var.cloud_func_vm_start },
    ]
}

# Upload deployment objects to GCS deployment bucket
resource "google_storage_bucket_object" "objects" {
    for_each = { for file in local.files : file.file_path => file }

    name    = each.value.file_path
    source  = each.value.file_path
    bucket  = google_storage_bucket.static.id
}


#============================================
# -------VM Initialisation Resources---------
#============================================

resource "google_cloud_run_v2_job" "vm_starter_job" {
  name     = "vm-starter-job"
  location = "europe-west1"

  template {
    template {
      containers {
        image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/cloud_job_vm_start:1.0.0"
        env {
          name  = "LOG_EXECUTION_ID"
          value = "true"
          }
        }
        timeout = "60s"
        service_account = "startvm-sa@checkmate-453316.iam.gserviceaccount.com"
      }
    }
}

# Create a Cloud Scheduler Job
resource "google_cloud_scheduler_job" "gcs_chess_ingestion_job" {
    paused        = false
    name          = "gcs_chess_ingestion_job"
    region        = "europe-west1"
    description   = "Chess API Data Ingestion Job to GCS"
    schedule      = "0 11 3 * *"
    time_zone     = "Europe/London"

    
    http_target {
      http_method = "POST"
      uri         = "https://${google_cloud_run_v2_job.vm_starter_job.location}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/checkmate-453316/jobs/vm-starter-job:run"
      
      oauth_token {
        service_account_email = "startvm-sa@checkmate-453316.iam.gserviceaccount.com"
    }
  }
}
