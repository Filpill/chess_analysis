# GCP Common Library Migration Guide

The `shared_func.py` has been converted into a proper Python package called `gcp_common_lib`.

## What Changed

### Before (Old Way)
```python
# Had to manipulate sys.path
import sys
sys.path.append("./functions")
from shared_func import log_printer, initialise_cloud_logger, gcp_access_secret
```

### After (New Way)
```python
# Clean import from installed package
from gcp_common_lib import log_printer, initialise_cloud_logger, gcp_access_secret
```

## Installation

The library is already configured as a local editable package. Just run:

```bash
uv sync
```

This installs `gcp-common` from the `./gcp_common_lib` directory.

## Package Structure

```
gcp_common_lib/
├── pyproject.toml           # Package configuration
├── README.md                # Usage documentation
└── gcp_common_lib/
    ├── __init__.py          # Public API exports
    └── gcp_common.py        # Main implementation
```

## Available Functions

All functions from `shared_func.py` are available with **identical signatures**:

```python
from gcp_common_lib import (
    # Logging
    log_printer,
    initialise_cloud_logger,

    # Secrets
    gcp_access_secret,

    # Pub/Sub
    read_cloud_scheduler_message,
)
```

## Usage Example

```python
from gcp_common_lib import (
    initialise_cloud_logger,
    log_printer,
    gcp_access_secret,
    read_cloud_scheduler_message,
)

# Initialize logger
project_id = "checkmate-453316"
logger = initialise_cloud_logger(project_id)

# Log with both Cloud Logging and console output
log_printer("Pipeline started", logger, severity="INFO")

# Access secrets
gmail_user = gcp_access_secret(project_id, "my_gmail", version_id="latest")

# Read Cloud Scheduler message
cloud_scheduler_dict = read_cloud_scheduler_message()
if cloud_scheduler_dict:
    job_name = cloud_scheduler_dict["job_name"]
    log_printer(f"Processing job: {job_name}", logger)
```

## Migrating Existing Scripts

For scripts currently using `shared_func.py`:

1. **Remove** `sys.path.append("./functions")` or `sys.path.append(f"{rel_path}functions")`
2. **Replace** `from shared_func import ...` with `from gcp_common_lib import ...`
3. **No other changes needed** - all function signatures are identical

### Example Migration

**Before:**
```python
import sys
rel_path = "./"
folder_list = ["functions", "inputs"]
for folder in folder_list:
    sys.path.append(f"{rel_path}{folder}")

from shared_func import initialise_cloud_logger, log_printer, gcp_access_secret
```

**After:**
```python
from gcp_common_lib import initialise_cloud_logger, log_printer, gcp_access_secret
```

## Benefits

1. **No sys.path manipulation**: Clean imports that work from any directory
2. **Proper dependency management**: `uv` handles installation
3. **Editable mode**: Changes to `gcp_common_lib/` are immediately available
4. **Better documentation**: Docstrings added to all functions
5. **Type hints ready**: Can add type hints for better IDE support

## Docker Integration

To use in Docker images, add to your Dockerfile:

```dockerfile
# Copy gcp_common library
COPY gcp_common_lib /app/gcp_common_lib

# Install with uv (will install from pyproject.toml)
RUN uv sync
```

## Backwards Compatibility

The original `scripts/functions/shared_func.py` still exists and can still be used with the old `sys.path.append()` method if needed. However, **new code should use `gcp_common_lib` import**.

## Function Reference

All functions maintain the same behavior:

| Function | Purpose |
|----------|---------|
| `initialise_cloud_logger(project_id)` | Initialize Cloud Logging logger |
| `log_printer(msg, logger, severity, console_print)` | Log to cloud and console |
| `gcp_access_secret(project_id, secret_id, version_id)` | Access Secret Manager |
| `read_cloud_scheduler_message()` | Decode Cloud Scheduler Pub/Sub message |
