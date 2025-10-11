import marimo

__generated_with = "0.11.30"
app = marimo.App(width="full")


@app.cell
def _():
    # Imports
    import os
    import sys
    sys.path.append(f"./functions")

    from alerts_func import load_environmental_var_config
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
        # ----- Email / Discord Config -----
        alert_cfg = load_environmental_var_config()
        os.environ["APP_ENV"]   = "PROD"
        os.environ["TO_ADDRS"]  = os.getenv("SMTP_USER")  # Format must be comma-separated strings to parse multiple emails

        if os.getenv("APP_ENV") == "PROD":
            os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord"
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
