# Alerts Library

Chess Pipeline alerting library for Email, Discord, and BigQuery notifications.

## Installation

From the root of the chess_analysis project:

```bash
uv add ./alerts_lib
```

## Usage

```python
import sys
from alerts_lib import (
    load_alerts_environmental_config,
    create_bq_run_monitor_datasets,
    append_to_trigger_bq_dataset,
    global_excepthook
)

# Configure alerts environment
env_vars = load_alerts_environmental_config()

# Set alert systems to enable (comma-separated: email, discord, bq)
import os
os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord,bq"
os.environ["TO_ADDRS"] = "your-email@example.com"
os.environ["APP_ENV"] = "PROD"
os.environ["PROJECT_ID"] = "checkmate-453316"

# Install global exception hook (automatically sends alerts on crashes)
sys.excepthook = global_excepthook

# Create monitoring datasets (first time setup)
project_id = "checkmate-453316"
logger = None  # Optional: pass your logger
create_bq_run_monitor_datasets(project_id, logger)

# Record run trigger
append_to_trigger_bq_dataset(project_id, logger)

# Your code here...
# Any unhandled exceptions will automatically trigger alerts
```

## Features

- **Email Alerts**: Formatted HTML emails with stack traces
- **Discord Alerts**: Markdown-formatted messages to Discord webhooks
- **BigQuery Logging**: Automatic logging of runs and failures to BigQuery
- **Global Exception Hook**: Automatically captures unhandled exceptions
- **Threading Support**: Handles exceptions in threads

## Environment Variables

- `TOGGLE_ENABLED_ALERT_SYSTEMS`: Comma-separated list (e.g., "email,discord,bq")
- `TO_ADDRS`: Comma-separated email recipients
- `APP_ENV`: Environment name (PROD/DEV/TEST)
- `PROJECT_ID`: GCP project ID
- `RUN_ID`: Optional UUID for run tracking (auto-generated if not set)
- `SMTP_HOST`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USER`: SMTP username (fetched from GCP Secret Manager)
- `SMTP_PASS`: SMTP password (fetched from GCP Secret Manager)
