# GCP Common Library

Common GCP utilities for the chess data pipeline - logging, secrets, and pub/sub message handling.

## Installation

From the root of the chess_analysis project:

```bash
uv sync
```

## Usage

```python
from gcp_common_lib import (
    log_printer,
    initialise_cloud_logger,
    gcp_access_secret,
    read_cloud_scheduler_message,
)

# Initialize Cloud Logging
project_id = "checkmate-453316"
logger = initialise_cloud_logger(project_id)

# Log to both Cloud Logging and console
log_printer("Processing started", logger, severity="INFO")

# Access GCP secrets
gmail_user = gcp_access_secret(project_id, "my_gmail", version_id="latest")

# Read Cloud Scheduler Pub/Sub message
cloud_scheduler_dict = read_cloud_scheduler_message()
if cloud_scheduler_dict:
    print(f"Received job: {cloud_scheduler_dict['job_name']}")
```

## Functions

### `initialise_cloud_logger(project_id: str)`
Initialize a Cloud Logging logger for the given GCP project.

**Parameters:**
- `project_id`: GCP project ID

**Returns:**
- Cloud Logging logger instance

### `log_printer(msg, logger, severity="INFO", console_print=True)`
Log message to both Cloud Logging and console.

**Parameters:**
- `msg`: Message to log
- `logger`: Cloud Logging logger instance
- `severity`: Log severity level (INFO, WARNING, ERROR, etc.)
- `console_print`: Whether to also print to console (default: True)

### `gcp_access_secret(project_id, secret_id, version_id="latest")`
Access a secret from GCP Secret Manager.

**Parameters:**
- `project_id`: GCP project ID
- `secret_id`: Secret name/ID
- `version_id`: Secret version (default: "latest")

**Returns:**
- Secret value as string

### `read_cloud_scheduler_message()`
Read and decode a Cloud Scheduler message from Pub/Sub.

Reads the `MESSAGE` environment variable (base64-encoded JSON), decodes it, and returns the parsed dictionary.

**Returns:**
- Dictionary containing the Cloud Scheduler message, or None if not present

## Migration from shared_func.py

**Old way:**
```python
import sys
sys.path.append("./functions")
from shared_func import log_printer, initialise_cloud_logger
```

**New way:**
```python
from gcp_common_lib import log_printer, initialise_cloud_logger
```

All function signatures remain the same - just the import changes!
