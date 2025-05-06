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
        { file_path = "functions/bq_func.py" },
        { file_path = "functions/gcs_func.py" },
        { file_path = "functions/transform_func.py" },
        { file_path = "functions/shared_func.py" },
        { file_path = "inputs/gcs_ingestion_settings.json" },
        { file_path = "scripts/bigquery_chess_transform_load.py" },
        { file_path = "scripts/gcs_chess_ingestion.py" },
        { file_path = "scripts/cloud_functions/vm_start/code.zip" },
        { file_path = "scripts/cloud_functions/vm_delete/code.zip" },
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

#============================================
# -----Cloud Run BQ Monitor Service App-----
#============================================
resource "google_cloud_run_service" "bq_monitor_dash" {
  name     = "bq-monitor-dash"
  location = "europe-west2"

  metadata {
    annotations = {
      "run.googleapis.com/ingress"       = "all"
      "run.googleapis.com/launch-stage"  = "GA"
      "run.googleapis.com/authorization-type" = "IAM"
    }
  }

  template {
    spec {
      service_account_name = "bq-monitor@checkmate-453316.iam.gserviceaccount.com"

      containers {
        image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/bq_monitor_dash:1.0.0"
        ports {
          container_port = 8080
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
