# Imports
import os
import sys
import ssl
import html
import uuid
import types
import socket
import smtplib
import requests
import traceback
import threading
import marimo as mo
import pandas as pd
from datetime import datetime
from email.message import EmailMessage
from email.utils import make_msgid
from datetime import datetime, timezone

from pygments import highlight
from pygments.lexers import PythonTracebackLexer
from pygments.formatters import HtmlFormatter
_PYGMENTS_FORMATTER = HtmlFormatter(noclasses=True)

sys.path.append(f"./functions")
from shared_func import gcp_access_secret
from bq_func import append_df_to_bigquery_table

def _generate_run_uuid():
    return str(uuid.uuid4())


def load_alerts_environmental_config():
    # Gmail Creds For Alerting Email Account
    project_id = "checkmate-453316"
    gmail_user_address_secretname = "my_gmail"
    gmail_app_passkey_secretname  = "gmail_app_pass"
    version_id = "latest"
    gmail_user = gcp_access_secret(project_id, gmail_user_address_secretname, version_id)
    gmail_passkey = gcp_access_secret(project_id, gmail_app_passkey_secretname, version_id)
    run_id = _generate_run_uuid()

    # Set Default Global Environmental Variables
    RUN_ID = os.getenv("RUN_ID", run_id)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").lower()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", gmail_user)
    SMTP_PASS = os.getenv("SMTP_PASS", gmail_passkey)
    TOGGLE_ENABLED_ALERT_SYSTEMS= os.getenv("TOGGLE_ENABLED_ALERT_SYSTEMS", "").lower() # Default Disabled - email,discord - Enable on script level

    env_vars =  {
        "RUN_ID": RUN_ID,
        "SMTP_HOST": SMTP_HOST,
        "SMTP_PORT": SMTP_PORT,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASS": SMTP_PASS,
        "TOGGLE_ENABLED_ALERT_SYSTEMS": TOGGLE_ENABLED_ALERT_SYSTEMS,
    }

    for key, value in env_vars.items():
        os.environ[key] = str(value)

    return env_vars


def _format_stacktrace_text(exc_type, exc_value, exc_traceback, max_chars=1500, max_frames=30):
    try:
        tbe = traceback.TracebackException.from_exception(exc_value)
        if tbe and tbe.stack and len(tbe.stack) > max_frames:
            tbe.stack = tbe.stack[-max_frames:]      # keep the tail
        text = "".join(tbe.format())
    except Exception:
        # last-ditch fallback if something is very broken
        tb_text = "".join(traceback.format_tb(exc_traceback)) if isinstance(exc_traceback, types.TracebackType) else ""
        text = f"{getattr(exc_type,'__name__',str(exc_type))}: {exc_value}\n{tb_text}"
    if len(text) > max_chars:
        text = "...(truncated)...\n" + text[-max_chars:]
    return text


def _format_html_stacktrace(stack_trace: str) -> str:
    highlighted = highlight(stack_trace, PythonTracebackLexer(), _PYGMENTS_FORMATTER)
    return f"""
<div style="max-width:720px;margin:16px auto;padding:0 8px;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
  <div style="border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);overflow:hidden;">
    <div style="background:#111827;color:#fff;padding:12px 16px;font-weight:600;">Stack Trace</div>
    <div style="background:#0b1020;padding:12px 16px;">{highlighted}</div>
  </div>
</div>
"""


def _collect_error_metadata(exc_traceback, exc_type, exc_value):
    return {
        "run_id" : os.getenv("RUN_ID"),
        "run_failed_date" : pd.Timestamp.now(tz="UTC").date(),
        "run_failed_dt" : pd.Timestamp.now(tz="UTC").floor("s"),
        "failed_filename" : os.path.basename(sys.argv[0]),
        "exception_type" : exc_type,
        "exception_value" : exc_value,
        "stack_trace" : "".join(_format_stacktrace_text(exc_type, exc_value, exc_traceback)),
        "hostname" : socket.gethostname(),
        "environment" : os.getenv("APP_ENV", "UNDEFINED"),
        "python_version" : sys.version,
        "process" : sys.argv[0],
        "python_path" : sys.argv[0]
    }


def _collect_run_trigger_metadata():
    return {
        "run_id" : os.getenv("RUN_ID"),
        "run_start_date" : pd.Timestamp.now(tz="UTC").date(),
        "run_start_dt" : pd.Timestamp.now(tz="UTC").floor("s"),
        "script_name" : os.path.basename(sys.argv[0]),
        "environment" : os.getenv("APP_ENV", "UNDEFINED"),
        "hostname" : socket.gethostname(),
        "python_version" : sys.version,
    }


def _error_metadata_html(exc_traceback, exc_type, exc_value) -> str:
    metadata =_collect_error_metadata(exc_traceback, exc_type, exc_value)
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;margin:0 auto;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
  <tr>
    <td style="padding:16px 8px;">
      <h2 style="margin:0 0 8px 0;font-size:18px;">🚨 Python Runtime Exception: {html.escape(exc_type.__name__)}</h2>
      <p style="margin:0 0 4px 0;"><strong>Run ID:</strong> {html.escape(metadata["run_id"])}</p>
      <p style="margin:0 0 4px 0;"><strong>Environment:</strong> {html.escape(metadata["environment"])}</p>
      <p style="margin:0 0 4px 0;"><strong>Hostname:</strong> {metadata["hostname"]}</p>
      <p style="margin:0 0 4px 0;"><strong>Time:</strong> {metadata["run_failed_dt"]}</p>
      <p style="margin:0 0 4px 0;"><strong>Python Filepath:</strong> {metadata["python_path"]}</p>
      <p style="margin:0 0 4px 0;"><strong>Python Version:</strong> {metadata["python_version"]}</p>
      <p style="margin:12px 0 0 0;"><strong>Error Description:</strong> {html.escape(exc_type.__name__)} — {html.escape(str(exc_value))}</p>
    </td>
  </tr>
</table>
"""


def _make_image_content_id():
    script_dir = os.path.dirname(os.path.abspath(__file__))                   
    image_path = os.path.join(script_dir, "..", "images", "this-is-fine.jpg") 
    cid = make_msgid(domain="alert.local")  # unique content ID               
    return image_path, cid


def build_error_discord_msg(exc_type, exc_value, exc_traceback) -> str: 
    metadata =_collect_error_metadata(exc_traceback, exc_type, exc_value)
    return (
        f"# **🚨 [{metadata['environment']}] Python Runtime Exception** — {metadata['failed_filename']}\n"
        f"**Run ID:** `{metadata['run_id']}`\n"
        f"**Error Description:** `{exc_type.__name__}` — `{str(exc_value)}`\n"
        f"**Time:** `{metadata['run_failed_dt']}`\n"
        f"**Environment:** `{metadata['environment']}`\n"
        f"**Hostname:** `{metadata['hostname']}`\n"
        f"**Python Filepath:** `{metadata['python_path']}`\n"
        f"**Python Version:** `{metadata['python_version']}`\n\n"
        f"**Stack Trace:**\n"
        f"```python\n{metadata['stack_trace']}```"
    )


def build_error_email_msg(exc_type, exc_value, exc_traceback) -> EmailMessage:

    image_path, cid = _make_image_content_id()
    metadata =_collect_error_metadata(exc_traceback, exc_type, exc_value)

    subject = f"[{metadata['environment']}] Script: {metadata['failed_filename']} — Error: {exc_type.__name__} — Hostname: {metadata['hostname']}"

    html_body = f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f9fafb;font-family:Arial, sans-serif;">
    <table role="presentation" align="center" style="margin:0 auto;max-width:900px;">
      <tr valign="middle">
        <td style="padding:4px;text-align:left;">
          {_error_metadata_html(exc_traceback, exc_type, exc_value)}
        </td>
        <td style="padding:4px 4px 4px 4px;text-align:center;">
          <img src="cid:{cid[1:-1]}" alt="Error image"
               style="height:250px;display:block;"/>
        </td>
      </tr>
    </table>
    <div style="padding:16px;">
      {_format_html_stacktrace(metadata['stack_trace'])}
    </div>
  </body>
</html>"""

    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = ", ".join([a.strip() for a in os.getenv("TO_ADDRS","").split(",") if a.strip()])
    msg["Subject"] = subject
    msg.set_content("") # Multipart 
    msg.add_alternative(html_body, subtype="html")

    # Attach image with CID
    with open(image_path, "rb") as img:
        msg.get_payload()[1].add_related(
            img.read(),
            maintype="image",
            subtype="jpg",
            cid=cid
        )
    return msg


SSL_CONTEXT = ssl.create_default_context()
def send_email_message(msg: EmailMessage):

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # ensure int
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=SSL_CONTEXT)  # STARTTLS only
            smtp.ehlo()
            if SMTP_USER and SMTP_PASS:
                smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except Exception:
        print("Failed to send error email:\n", traceback.format_exc(), file=sys.stderr)

def send_discord_message(msg):

    project_id = "checkmate-453316"
    secret_name = "discord-alert-webhook"
    version_id = "latest"
    webhook_url = gcp_access_secret(project_id, secret_name, version_id)

    data = {
        "content": f"{msg}"
    }

    response = requests.post(webhook_url, json=data)

    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")


def create_bq_run_monitor_datasets(project_id, logger):
    # Definining Schema of Runs Being Triggered/Failed in Python
    location = "EU"
    dataset_name = f"00_pipeline_monitor"
    if check_bigquery_dataset_exists(dataset_name, logger) == False:
        create_bigquery_dataset(project_id, dataset_name, location, logger)

    table_name = "runs_triggered"
    table_runs_triggered = f"{project_id}.{dataset_name}.{table_name}"

    schema_runs_triggered = [
        bigquery.SchemaField(name="run_id",         field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        bigquery.SchemaField(name="run_start_date", field_type="DATE",       mode="REQUIRED",  description="Date of the pipeline run"),
        bigquery.SchemaField(name="run_start_dt",   field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the pipeline run"),
        bigquery.SchemaField(name="script_name",    field_type="STRING",     mode="REQUIRED",  description="Name of script"),
        bigquery.SchemaField(name="environment",    field_type="STRING",     mode="REQUIRED",  description="Name of environement e.g.: PROD/DEV/TEST"),
        bigquery.SchemaField(name="hostname",       field_type="STRING",     mode="REQUIRED",  description="Name of machine running script"),
        bigquery.SchemaField(name="python_version", field_type="STRING",     mode="REQUIRED",  description="Python version used during runtime"),
    ]
    loading_time_partitioning_field ="run_start_date"

    if check_bigquery_table_exists(table_runs_triggered, logger) == False:
        create_bigquery_table(table_runs_triggered, schema_runs_triggered, logger, loading_time_partitioning_field)

    table_name = "runs_failed"
    table_runs_failed = f"{project_id}.{dataset_name}.{table_name}"

    schema_runs_failed = [
        bigquery.SchemaField(name="run_id",          field_type="STRING",     mode="REQUIRED",  description="UUID of the pipeline run executed"),
        bigquery.SchemaField(name="run_failed_date", field_type="DATE",       mode="REQUIRED",  description="Date of the failed pipeline run"),
        bigquery.SchemaField(name="run_failed_dt",   field_type="TIMESTAMP",  mode="REQUIRED",  description="Datetime of the failed pipeline run"),
        bigquery.SchemaField(name="failed_filename", field_type="STRING",     mode="REQUIRED",  description="Name of file that failed"),
        bigquery.SchemaField(name="exception_type",  field_type="STRING",     mode="REQUIRED",  description="Type of exception"),
        bigquery.SchemaField(name="exception_value", field_type="STRING",     mode="REQUIRED",  description="Value of exception"),
        bigquery.SchemaField(name="stack_trace",     field_type="STRING",     mode="REQUIRED",  description="Details of error produced"),
    ]
    loading_time_partitioning_field ="run_failed_date"

    if check_bigquery_table_exists(table_runs_failed, logger) == False:
        create_bigquery_table(table_runs_failed, schema_runs_failed, logger, loading_time_partitioning_field)


def append_to_trigger_bq_dataset(project_id, logger=None):
    run_metadata = _collect_run_trigger_metadata()
    df = pd.DataFrame([run_metadata])
    metadata_table_id = f"{project_id}.00_pipeline_monitor.runs_triggered"
    append_df_to_bigquery_table(df, metadata_table_id, logger)
    return df


def append_to_failed_bq_dataset(exc_type, exc_value, exc_traceback, logger=None):
    project_id = os.getenv("PROJECT_ID")
    error_metadata = _collect_error_metadata(exc_type, exc_value, exc_traceback)
    df = pd.DataFrame([error_metadata])

    df = df[
        [
            "run_id",
            "run_failed_date",
            "run_failed_dt",
            "failed_filename",
            "exception_type",
        ]
    ]
    metadata_table_id = f"{project_id}.00_pipeline_monitor.runs_failed"
    append_df_to_bigquery_table(df, metadata_table_id)
    return df


def global_excepthook(exc_type, exc_value, exc_traceback):

    if issubclass(exc_type, KeyboardInterrupt):
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)
    email_msg = build_error_email_msg(exc_type, exc_value, exc_traceback)
    discord_msg = build_error_discord_msg(exc_type, exc_value, exc_traceback)

    if "email" in os.getenv("TOGGLE_ENABLED_ALERT_SYSTEMS"):
        send_email_message(email_msg)

    if "discord" in os.getenv("TOGGLE_ENABLED_ALERT_SYSTEMS"):
        send_discord_message(discord_msg)

    if "bq" in os.getenv("TOGGLE_ENABLED_ALERT_SYSTEMS"):
        append_to_failed_bq_dataset(exc_type, exc_value, exc_traceback)

    # Mirror to stderr locally
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


# Install hooks
sys.excepthook = global_excepthook
def _threading_excepthook(args: threading.ExceptHookArgs):
    global_excepthook(args.exc_type, args.exc_value, args.exc_traceback)

if hasattr(threading, "excepthook"):
    threading.excepthook = _threading_excepthook
