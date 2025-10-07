import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _(__file__):
    # Imports
    import os
    import sys
    import ssl
    import socket
    import html
    import smtplib
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


    def _format_html_stack(stack_text: str) -> str:
        highlighted = highlight(stack_text, PythonTracebackLexer(), _PYGMENTS_FORMATTER)
        return f"""
    <div style="max-width:720px;margin:16px auto;padding:0 8px;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
      <div style="border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);overflow:hidden;">
        <div style="background:#111827;color:#fff;padding:12px 16px;font-weight:600;">Stack Trace</div>
        <div style="background:#0b1020;padding:12px 16px;">{highlighted}</div>
      </div>
    </div>
    """


    def _base_info_html(exc_type, exc_value, environment: str) -> str:
        hostname = html.escape(socket.gethostname())
        pyver = html.escape(sys.version)
        process = html.escape(sys.argv[0])
        python_path = html.escape(__file__)
        python_file = html.escape(os.path.basename(python_path))
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;margin:0 auto;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
      <tr>
        <td style="padding:16px 8px;">
          <h2 style="margin:0 0 8px 0;font-size:18px;">🚨 Python Runtime Exception: {html.escape(exc_type.__name__)}</h2>
          <p style="margin:0 0 4px 0;"><strong>Environment:</strong> {html.escape(environment)}</p>
          <p style="margin:0 0 4px 0;"><strong>Hostname:</strong> {hostname}</p>
          <p style="margin:0 0 4px 0;"><strong>Time:</strong> {ts}</p>
          <p style="margin:0 0 4px 0;"><strong>Process:</strong> {process}</p>
          <p style="margin:0 0 4px 0;"><strong>Python Filepath:</strong> {python_path}</p>
          <p style="margin:0 0 4px 0;"><strong>Python Version:</strong> {pyver}</p>
          <p style="margin:12px 0 0 0;"><strong>Error Description:</strong> {html.escape(exc_type.__name__)} — {html.escape(str(exc_value))}</p>
        </td>
      </tr>
    </table>
    """


    def build_error_email(exc_type, exc_value, exc_traceback) -> EmailMessage:
        exc_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        stack_text = "".join(exc_lines)
        python_path = __file__
        python_file = os.path.basename(python_path)
        ENVIRONMENT = os.getenv("APP_ENV", "DEV")
        FROM_ADDR = os.getenv("FROM_ADDR")
        TO_ADDRS = [a.strip() for a in os.getenv("TO_ADDRS","").split(",") if a.strip()]

        subject = f"[{ENVIRONMENT}] Script: {python_file} — Error: {exc_type.__name__} — Hostname: {socket.gethostname()}"

        # Plain-text fallback
        text_body = (
            f"Uncaught exception\n"
            f"Environment: {ENVIRONMENT}\n"
            f"Host: {socket.gethostname()}\n"
            f"Process: {sys.argv[0]}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Python: {sys.version}\n\n"
            f"Exception: {exc_type.__name__}: {exc_value}\n\n{stack_text}\n"
        )

        # ---- image setup ----
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "this-is-fine.jpg")
        cid = make_msgid(domain="alert.local")  # unique content ID
        cid_ref = cid[1:-1]

        html_body = f"""<!DOCTYPE html>
    <html>
      <body style="margin:0;padding:0;background:#f9fafb;font-family:Arial, sans-serif;">
        <table role="presentation" align="center" style="margin:0 auto;max-width:900px;">
          <tr valign="middle">
            <td style="padding:4px;text-align:left;">
              {_base_info_html(exc_type, exc_value, ENVIRONMENT)}
            </td>
            <td style="padding:4px 4px 4px 4px;text-align:center;"> <!-- 👈 right padding -->
              <img src="cid:{cid_ref}" alt="Error image"
                   style="height:250px;display:block;"/>
            </td>
          </tr>
        </table>
        <div style="padding:16px;">
          {_format_html_stack(stack_text)}
        </div>
      </body>
    </html>"""
    
        msg = EmailMessage()
        msg["From"] = FROM_ADDR
        msg["To"] = ", ".join(TO_ADDRS)
        msg["Subject"] = subject
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        # attach image with CID
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


    def global_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return sys.__excepthook__(exc_type, exc_value, exc_traceback)
        msg = build_error_email(exc_type, exc_value, exc_traceback)
        send_email_message(msg)
        # Also mirror to stderr locally
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


    # Install hooks
    sys.excepthook = global_excepthook
    def _threading_excepthook(args: threading.ExceptHookArgs):
        global_excepthook(args.exc_type, args.exc_value, args.exc_traceback)

    if hasattr(threading, "excepthook"):
        threading.excepthook = _threading_excepthook
    return (
        EmailMessage,
        HtmlFormatter,
        PythonTracebackLexer,
        SSL_CONTEXT,
        build_error_email,
        datetime,
        gcp_access_secret,
        global_excepthook,
        highlight,
        html,
        make_msgid,
        mo,
        os,
        send_email_message,
        smtplib,
        socket,
        ssl,
        sys,
        threading,
        traceback,
    )


@app.cell
def _(gcp_access_secret, os):
    def main():
        # Gmail Creds
        project_id = "checkmate-453316"
        my_gmail_secret = "my_gmail"
        gmail_app_pass_secret = "gmail_app_pass"
        version_id = "latest"
        gmail_user = gcp_access_secret(project_id, my_gmail_secret, version_id)
        gmail_secret = gcp_access_secret(project_id, gmail_app_pass_secret, version_id)

        # ====================
        # Email / SMTP CONFIG
        # ====================
        # After pulling from Secret Manager
        os.environ["SMTP_HOST"] = "smtp.gmail.com"
        os.environ["SMTP_PORT"] = "587"
        os.environ["SMTP_USER"] = gmail_user       # Email used to authenticate with SMTP
        os.environ["SMTP_PASS"] = gmail_secret     # Pass for email sending the alert message
        os.environ["FROM_ADDR"] = gmail_user       # Email which is sending the alert message
        os.environ["TO_ADDRS"]  = f"{gmail_user}"  # Comma-separated emails for recieving alerts for multiple
        os.environ["APP_ENV"]   = "DEV"

        print("trigger manual failure")
        1/0
        #script_dir = os.path.dirname(os.path.abspath(__file__))
        #image_path = os.path.join(script_dir, "images", "this-is-fine.jpg")
        #print(image_path)
    return (main,)


@app.cell
def _(global_excepthook, main):
    from types import SimpleNamespace

    try:
        main()
    except Exception as e:
        # call your hook explicitly
        global_excepthook(type(e), e, e.__traceback__)
        # Re-raise so marimo still shows it
        raise
    return (SimpleNamespace,)


if __name__ == "__main__":
    app.run()
