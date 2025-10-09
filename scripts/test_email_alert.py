import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # Imports
    import os
    import sys
    sys.path.append(f"./functions")

    from alerts_func import _format_html_stack
    from alerts_func import _base_info_html
    from alerts_func import build_error_email
    from alerts_func import send_email_message
    from alerts_func import global_excepthook
    from alerts_func import _threading_excepthook

    from shared_func import gcp_access_secret
    from shared_func import initialise_cloud_logger
    return (
        build_error_email,
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
        # Initialise Logger
        project_id = "checkmate-453316"
        logger = initialise_cloud_logger(project_id)    
        logger.log_text("EMAIL ALERT TEST -- Script Initilisation", severity="WARNING")


        # Gmail Creds
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
        os.environ["APP_ENV"]   = "TEST"

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
