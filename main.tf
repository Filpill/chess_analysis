#============================================
# -------Script Deployment Resources---------
#============================================
# Create storage bucket for object related to deployments
resource "google_storage_bucket" "static" {
    name          = "chess-deployments"
    location      = "EU"
    storage_class = "STANDARD"

    uniform_bucket_level_access = true
}

# Gather all files needed for deployment
locals {
    files = [
        { file_path = "scripts/functions/bq_func.py" },
        { file_path = "scripts/functions/gcs_func.py" },
        { file_path = "scripts/functions/transform_func.py" },
        { file_path = "scripts/functions/shared_func.py" },
        { file_path = "scripts/inputs/gcs_ingestion_settings.json" },
        { file_path = "scripts/inputs/bq_load_settings.json" },
        { file_path = "scripts/bigquery_chess_transform_load.py" },
        { file_path = "scripts/gcs_chess_ingestion.py" },
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
# -------VM Init and Deleter Resources-------
#============================================

resource "google_pubsub_topic" "start-vm-topic" {
  name = "start-vm-topic"
}

resource "google_pubsub_topic" "delete_vm_topic" {
  name = "delete-vm-topic"
}

resource "google_logging_project_sink" "docker_exit_sink" {
  name        = "docker-exit-sink"
  description = "Sink for extracting the docker container exit logs"
  project     = "checkmate-453316"

  destination = "pubsub.googleapis.com/projects/checkmate-453316/topics/delete-vm-topic"

  filter = <<EOT
    logName="projects/checkmate-453316/logs/cos_system"
    resource.type="gce_instance"
    jsonPayload.MESSAGE:"container die"
    jsonPayload.MESSAGE:"image=europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo"
EOT

  unique_writer_identity = true
}


resource "google_cloud_run_v2_service" "vm_initialiser" {
  name     = "vm-initialiser"
  location = "europe-west1"

  template {
    containers {
      image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/vm_initialiser:latest"
      env {
        name  = "LOG_EXECUTION_ID"
        value = "true"
      }
    }
    timeout        = "60s"
    service_account = "startvm-sa@checkmate-453316.iam.gserviceaccount.com"
  }
}

resource "google_cloud_run_v2_service" "vm_deleter" {
  name     = "vm-deleter"
  location = "europe-west2"

  deletion_protection = false 

  template {
    containers {
      image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/vm_deleter:latest"
      env {
        name  = "LOG_EXECUTION_ID"
        value = "true"
      }
    }
    timeout        = "60s"
    service_account = "startvm-sa@checkmate-453316.iam.gserviceaccount.com"
  }
}

resource "google_eventarc_trigger" "vm_deletion_trigger" {
  name     = "trigger-vm-deletion"
  location = "europe-west2"
  project  = "checkmate-453316"

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.pubsub.topic.v1.messagePublished"
  }

  transport {
    pubsub {
      topic = google_pubsub_topic.delete_vm_topic.id
    }
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.vm_deleter.name
      region  = google_cloud_run_v2_service.vm_deleter.location
      path    = "/"
    }
  }

  service_account = "vm-deleter-sa@checkmate-453316.iam.gserviceaccount.com"

  depends_on = [
    google_cloud_run_v2_service.vm_deleter,
    google_pubsub_topic.delete_vm_topic
  ]
}

#============================================ 
# ---------- Cloud Scheduler Jobs ----------- 
#============================================ 

# Create Cloud Scheduler Jobs for Ingestion And Loading
resource "google_cloud_scheduler_job" "test_pub_sub_message" {
    paused        = false
    name          = "test_pub_sub_message"
    region        = "europe-west1"
    description   = "Testing Pub Sub Message into VM Workload"
    schedule      = "0 9 3 * *"
    time_zone     = "Europe/London"

    pubsub_target {
      topic_name = google_pubsub_topic.start-vm-topic.id
      data        = base64encode(jsonencode({
          job_name = "test_pub_sub_message",
          script_setting = "test",
          start_date = "2024-04-01",
          end_date = "2025-03-31",
          setting1 = "A",
          setting2 = "B",
          setting3 = "C",
      }))
      attributes = {
        origin = "scheduler"
      }
    }
  }

# Create Cloud Scheduler Jobs for Ingestion And Loading
resource "google_cloud_scheduler_job" "chess_gcs_ingestion" {
    paused        = false
    name          = "chess_gcs_ingestion"
    region        = "europe-west1"
    description   = "Chess API Data Ingestion Job to GCS"
    schedule      = "0 11 3 * *"
    time_zone     = "Europe/London"

    pubsub_target {
      topic_name = google_pubsub_topic.start-vm-topic.id
      data        = base64encode(jsonencode({
          job_name = "chess_gcs_ingestion"
      }))
      attributes = {
        origin = "scheduler"
      }
    }
  }

resource "google_cloud_scheduler_job" "chess_bigquery_load" {
    paused        = false
    name          = "chess_bigquery_load"
    region        = "europe-west1"
    description   = "Loading Raw Chess Data from GCS to BigQuery"
    schedule      = "0 11 4 * *"
    time_zone     = "Europe/London"

    pubsub_target {
      topic_name = google_pubsub_topic.start-vm-topic.id
      data        = base64encode(jsonencode({
          job_name = "chess_bigquery_load"
      }))
      attributes = {
        origin = "scheduler"
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
        image = "europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/bq_monitor_dash:latest"
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
