variable "project_id" {
    type = string
    description = "GCP project identity"
}

variable "bucket_region" {
    type = string
    description = "Created bucket region"
}

variable "deployment_bucket" {
    type = string
    description = "Name of bucket containing deployment objects"
}

variable "trigger_bucket" {
    type = string
    description = "Name of bucket for trigger facilitation"
}

variable "ingestion_script" {
    type = string
    description = "Path to ingestion script"
}

variable "function_gcs_ingestion" {
    type = string
    description = "Path to gcs ingestion functions"
}

variable "function_shared" {
    type = string
    description = "Path to shared functions"
}

variable "ingestion_input_config" {
    type = string
    description = "Path to ingestion input configuration"
}

variable "vm_pubsub_topic" {
    type = string
    description = "Name of Pub/Sub topic for initialising the VM's"
}

variable "job_region" {
    type = string
    description = "Job region"
}
