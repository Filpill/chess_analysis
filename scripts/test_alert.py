import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # Imports
    import os
    from google.cloud import bigquery

    import sys
    sys.path.append(f"./functions")
    from alerts_func import load_alerts_environmental_config
    from alerts_func import _format_html_stacktrace
    from alerts_func import _error_metadata_html
    from alerts_func import build_error_email_msg
    from alerts_func import build_error_discord_msg
    from alerts_func import send_email_message
    from alerts_func import send_discord_message
    from alerts_func import global_excepthook
    from alerts_func import _threading_excepthook

    from shared_func import gcp_access_secret
    from shared_func import initialise_cloud_logger
    from shared_func import read_cloud_scheduler_message

    from bq_func import check_bigquery_dataset_exists
    from bq_func import check_bigquery_table_exists
    from bq_func import create_bigquery_dataset
    from bq_func import create_bigquery_table
    from bq_func import create_bq_run_monitor_datasets
    from bq_func import append_df_to_bigquery_table
    return (
        build_error_email_msg,
        build_error_discord_msg,
        gcp_access_secret,
        global_excepthook,
        initialise_cloud_logger,
        os,
        send_email_message,
        sys,
    )


@app.cell
def _(gcp_access_secret, initialise_cloud_logger, os):
    def main():

        # =======================================================================================
        # ---------------------------------- Setting Globals ------------------------------------
        # =======================================================================================
        # ----- Initialise Logger -----
        project_id = "checkmate-453316"
        logger = initialise_cloud_logger(project_id)
        logger.log_text("EMAIL/DISCORD -- ALERT TEST -- Script Initilisation", severity="WARNING")
        # =======================================================================================
        # ----- Pub/Sub Message Sent Via Cloud Scheduler -----
        cloud_scheduler_dict = read_cloud_scheduler_message()
        logger.log_text(f"EMAIL/DISCORD -- READING CLOUD SCHEDULER MESSAGE: {cloud_scheduler_dict}", severity="WARNING")
        if cloud_scheduler_dict is not None:
            os.environ["APP_ENV"] = cloud_scheduler_dict["app_env"]
        if cloud_scheduler_dict is None:
            os.environ["APP_ENV"] = "DEV/TEST"
        # =======================================================================================
        # ----- Email / Discord Config -----
        alert_config = load_alerts_environmental_config()
        os.environ["TO_ADDRS"]  = os.getenv("SMTP_USER")  # Format must be comma-separated strings to parse multiple emails

        # PROD setting will send alerts, no alerts in DEV or TEST setting
        if os.getenv("APP_ENV") == "PROD":
            os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord"
        else:
            os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "discord"
        # =======================================================================================
        # Definining Schema of Runs Being Triggered/Failed in Python
        create_bq_run_monitor_datasets(project_id, logger)
        #location = "EU"
        #dataset_name = f"00_pipeline_monitor"
        #if check_bigquery_dataset_exists(dataset_name, logger) == False:
        #    create_bigquery_dataset(project_id, dataset_name, location, logger)

        #table_name = "runs_triggered"
        #table_runs_triggered = f"{project_id}.{dataset_name}.{table_name}"

        #schema_runs_triggered = [
        #    bigquery.SchemaField(name="run_id",         field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        #    bigquery.SchemaField(name="run_date",       field_type="DATE",       mode="REQUIRED",  description="Date of the pipeline run"),
        #    bigquery.SchemaField(name="run_dt",         field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the pipeline run"),
        #    bigquery.SchemaField(name="script_name",    field_type="STRING",     mode="REQUIRED",  description="Name of script"),
        #    bigquery.SchemaField(name="environment",    field_type="STRING",     mode="REQUIRED",  description="Name of environement e.g.: PROD/DEV/TEST"),
        #    bigquery.SchemaField(name="hostname",       field_type="STRING",     mode="REQUIRED",  description="Name of machine running script"),
        #    bigquery.SchemaField(name="python_version", field_type="STRING",     mode="REQUIRED",  description="Python version used during runtime"),
        #]
        #loading_time_partitioning_field ="run_date"

        #if check_bigquery_table_exists(table_runs_triggered, logger) == False:
        #    create_bigquery_table(table_runs_triggered, schema_runs_triggered, logger, loading_time_partitioning_field)

        #table_name = "runs_failed"
        #table_runs_failed = f"{project_id}.{dataset_name}.{table_name}"

        #schema_runs_failed = [
        #    bigquery.SchemaField(name="run_id",          field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        #    bigquery.SchemaField(name="run_failed_date", field_type="DATE",       mode="REQUIRED",  description="Date of the failed pipeline run"),
        #    bigquery.SchemaField(name="run_failed_dt",   field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the failed pipeline run"),
        #    bigquery.SchemaField(name="failed_filename", field_type="STRING",     mode="REQUIRED",  description="Name of file that failed"),
        #    bigquery.SchemaField(name="exception_type",  field_type="STRING",     mode="REQUIRED",  description="Type of exception"),
        #    bigquery.SchemaField(name="exception_value", field_type="STRING",     mode="REQUIRED",  description="Value of exception"),
        #    bigquery.SchemaField(name="stack_trace",     field_type="STRING",     mode="REQUIRED",  description="Details of error produced"),
        #]
        #loading_time_partitioning_field ="run_failed_date"

        #if check_bigquery_table_exists(table_runs_failed, logger) == False:
        #    create_bigquery_table(table_runs_failed, schema_runs_failed, logger, loading_time_partitioning_field)

        # =======================================================================================
        logger.log_text("EMAIL ALERT TEST -- Triggering Manual Failure...", severity="ERROR")
        1/0
    return (main,)


@app.cell
def _(global_excepthook, main):
    from types import SimpleNamespace

    try:
        main()
    except Exception as e:
        # call your hook explicitly
        global_excepthook(type(e), e, e.__traceback__)
    return (SimpleNamespace,)


if __name__ == "__main__":
    app.run()
