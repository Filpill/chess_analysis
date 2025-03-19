variable "project_id" {
    description = "GCP project identity"
    type = string
}

variable "deployment_bucket_name" {
    description = "Name of bucket containing deployment objects"
    type = string
}

variable "ingestion_script_name" {
    description = "Name of ingestion script"
    type = string
}

variable "ingestion_script_path" {
    description = "Path to ingestion script"
    type = string
}
