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


# Create a Cloud Scheduler Job
resource "google_cloud_scheduler_job" "gcs_chess_ingestion_job" {
    paused        = false
    name          = "gcs_chess_ingestion_job"
    region        = "europe-west1"
    description   = "Chess API Data Ingestion Job to GCS"
    schedule      = "0 11 3 * *"
    time_zone     = "UTC"

    http_target {

      uri         = "https://vm-starter-810099024571.europe-west1.run.app"
      http_method = "POST"
   
      oidc_token {
          service_account_email = "startvm-sa@checkmate-453316.iam.gserviceaccount.com"
          audience             = "https://europe-west1-checkmate-453316.cloudfunctions.net/vm_starter"
        }
   }

}

#resource "google_cloudfunctions2_function" "vm_starter" {
#  name        = "vm_starter"
#  location    = "europe-west1"
#  description = "A function to initialise a virtual machine"
#
#  build_config {
#      runtime     = "python311"
#      entry_point = "request"
#      source {
#          storage_source {
#              bucket = "chess-deployments"
#              object = "scripts/cloud_functions/vm_start/code.zip"
#          }
#      }
#  }
#
#  service_config {
#      all_traffic_on_latest_revision   = true
#      available_cpu                    = "0.1666"
#      available_memory                 = "256M"
#      environment_variables            = {
#          "LOG_EXECUTION_ID" = "true"
#        }
#      ingress_settings                 = "ALLOW_ALL"
#      max_instance_count               = 100
#      max_instance_request_concurrency = 1
#      min_instance_count               = 0
#      service                          = "projects/checkmate-453316/locations/europe-west1/services/vm-starter"
#      service_account_email            = "810099024571-compute@developer.gserviceaccount.com"
#      timeout_seconds                  = 60
#    }
#}

resource "google_cloud_run_v2_job" "vm_starter_job" {
  name     = "vm-starter-job"
  location = "europe-west1"

  template {
    template {
      containers {
        image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/cloud_job_vm_start:v004"
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
