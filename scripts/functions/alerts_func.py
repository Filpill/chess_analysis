# Imports
import os
import sys
import ssl
import socket
import html
import smtplib
import requests
import traceback
import threading
import marimo as mo
from datetime import datetime
from email.message import EmailMessage
from email.utils import make_msgid

from pygments import highlight
from pygments.lexers import PythonTracebackLexer
from pygments.formatters import HtmlFormatter
_PYGMENTS_FORMATTER = HtmlFormatter(noclasses=True)

sys.path.append(f"./functions")
from shared_func import gcp_access_secret


def _format_html_stacktrace(stack_text: str) -> str:
    highlighted = highlight(stack_text, PythonTracebackLexer(), _PYGMENTS_FORMATTER)
    return f"""
<div style="max-width:720px;margin:16px auto;padding:0 8px;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
  <div style="border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);overflow:hidden;">
    <div style="background:#111827;color:#fff;padding:12px 16px;font-weight:600;">Stack Trace</div>
    <div style="background:#0b1020;padding:12px 16px;">{highlighted}</div>
  </div>
</div>
"""


def _originating_file_error(exc_traceback) -> str:
    tb = traceback.extract_tb(exc_traceback)
    if tb:
        # last frame = where the error actually happened
        return os.path.abspath(tb[-1].filename)
    return os.path.abspath(sys.argv[0])  # fallback


def _base_info_html(exc_traceback, exc_type, exc_value, environment: str) -> str:
    hostname = html.escape(socket.gethostname())
    pyver = html.escape(sys.version)
    process = html.escape(sys.argv[0])
    python_path = html.escape(_originating_file_error(exc_traceback))
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;margin:0 auto;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
  <tr>
    <td style="padding:16px 8px;">
      <h2 style="margin:0 0 8px 0;font-size:18px;">🚨 Python Runtime Exception: {html.escape(exc_type.__name__)}</h2>
      <p style="margin:0 0 4px 0;"><strong>Environment:</strong> {html.escape(environment)}</p>
      <p style="margin:0 0 4px 0;"><strong>Hostname:</strong> {hostname}</p>
      <p style="margin:0 0 4px 0;"><strong>Time:</strong> {ts}</p>
      <p style="margin:0 0 4px 0;"><strong>Python Filepath:</strong> {python_path}</p>
      <p style="margin:0 0 4px 0;"><strong>Python Version:</strong> {pyver}</p>
      <p style="margin:12px 0 0 0;"><strong>Error Description:</strong> {html.escape(exc_type.__name__)} — {html.escape(str(exc_value))}</p>
    </td>
  </tr>
</table>
"""


def build_discord_markdown(exc_traceback, exc_type, exc_value, environment: str) -> str: 
    hostname = socket.gethostname()
    pyver = sys.version
    process = sys.argv[0]
    python_path = _originating_file_error(exc_traceback)
    python_file = os.path.basename(_originating_file_error(exc_traceback)) 
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    exc_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    stack_text = "".join(exc_lines) 
    return (
        f"**🚨 Python Runtime Exception:** `{exc_type.__name__}`\n\n"
        f"**Python File:** `{python_file}`\n"
        f"**Environment:** `{environment}`\n"
        f"**Hostname:** `{hostname}`\n"
        f"**Time:** `{ts}`\n"
        f"**Python Filepath:** `{python_path}`\n"
        f"**Python Version:** `{pyver}`\n\n"
        f"**Error Description:** `{exc_type.__name__}` — `{str(exc_value)}`"
        f"> {stack_text}"
    )


def build_error_email(exc_type, exc_value, exc_traceback) -> EmailMessage:
    exc_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    stack_text = "".join(exc_lines)
    python_path = __file__
    python_file = os.path.basename(_originating_file_error(exc_traceback))
    ENVIRONMENT = os.getenv("APP_ENV", "DEV")
    FROM_ADDR = os.getenv("FROM_ADDR")
    TO_ADDRS = [a.strip() for a in os.getenv("TO_ADDRS","").split(",") if a.strip()]

    subject = f"[{ENVIRONMENT}] Script: {python_file} — Error: {exc_type.__name__} — Hostname: {socket.gethostname()}"

    # ---- Image Setup ----
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "..", "images", "this-is-fine.jpg")
    cid = make_msgid(domain="alert.local")  # unique content ID
    cid_ref = cid[1:-1]

    html_body = f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f9fafb;font-family:Arial, sans-serif;">
    <table role="presentation" align="center" style="margin:0 auto;max-width:900px;">
      <tr valign="middle">
        <td style="padding:4px;text-align:left;">
          {_base_info_html(exc_traceback, exc_type, exc_value, ENVIRONMENT)}
        </td>
        <td style="padding:4px 4px 4px 4px;text-align:center;"> <!-- 👈 right padding -->
          <img src="cid:{cid_ref}" alt="Error image"
               style="height:250px;display:block;"/>
        </td>
      </tr>
    </table>
    <div style="padding:16px;">
      {_format_html_stacktrace(stack_text)}
    </div>
  </body>
</html>"""

    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = ", ".join(TO_ADDRS)
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
    secret_name = "discord-alert-test"
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


def global_excepthook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)
    email_msg = build_error_email(exc_type, exc_value, exc_traceback)
    discord_msg = build_discord_markdown(exc_type, exc_value, exc_traceback)
    send_email_message(email_msg)
    send_discord_message(discord_msg): 
    # Also mirror to stderr locally
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


# Install hooks
sys.excepthook = global_excepthook
def _threading_excepthook(args: threading.ExceptHookArgs):
    global_excepthook(args.exc_type, args.exc_value, args.exc_traceback)

if hasattr(threading, "excepthook"):
    threading.excepthook = _threading_excepthook
