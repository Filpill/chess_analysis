project_id = "checkmate-453316"

bucket_region = "EU"
deployment_bucket = "chess-deployments"
trigger_bucket = "chess-triggers"

ingestion_script = "scripts/gcs_chess_ingestion.py"
transform_script = "scripts/bigquery_chess_transform_load.py"
function_gcs_ingestion = "functions/gcs_func.py"
function_shared = "functions/shared_func.py"
ingestion_input_config = "inputs/gcs_ingestion_settings.json"
cloud_func_vm_start = "scripts/cloud_functions/vm_start/code.zip"

vm_pubsub_topic = "start_vm_topic"
job_region = "europe-west2"
