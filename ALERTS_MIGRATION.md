# Alerts Library Migration Guide

The `alerts_func.py` has been converted into a proper Python package that can be imported anywhere.

## What Changed

### Before (Old Way)
```python
# Had to manipulate sys.path
import sys
sys.path.append("./functions")
from alerts_func import load_alerts_environmental_config, global_excepthook
```

### After (New Way)
```python
# Clean import from installed package
from alerts_lib import load_alerts_environmental_config, global_excepthook
```

## Installation

The library is already configured as a local editable package. Just run:

```bash
uv sync
```

This installs `alerts-lib` from the `./alerts_lib` directory.

## Package Structure

```
alerts_lib/
├── pyproject.toml           # Package configuration
├── README.md                # Usage documentation
└── alerts_lib/
    ├── __init__.py          # Public API exports
    ├── alerts.py            # Main implementation
    └── this-is-fine.jpg     # Alert email image
```

## Available Functions

```python
from alerts_lib import (
    # Configuration
    load_alerts_environmental_config,

    # Message builders
    build_error_email_msg,
    build_error_discord_msg,

    # Senders
    send_email_message,
    send_discord_message,

    # BigQuery monitoring
    create_bq_run_monitor_datasets,
    append_to_trigger_bq_dataset,
    append_to_failed_bq_dataset,

    # Exception hook
    global_excepthook,
)
```

## Usage Example

See `scripts/example_alerts_usage.py` for a complete working example.

Basic pattern:
```python
import os
import sys
from alerts_lib import (
    load_alerts_environmental_config,
    create_bq_run_monitor_datasets,
    append_to_trigger_bq_dataset,
    global_excepthook
)

# Load config
env_vars = load_alerts_environmental_config()

# Configure alerts
os.environ["TOGGLE_ENABLED_ALERT_SYSTEMS"] = "email,discord,bq"
os.environ["TO_ADDRS"] = "your-email@example.com"
os.environ["APP_ENV"] = "PROD"
os.environ["PROJECT_ID"] = "checkmate-453316"

# Install global exception hook
sys.excepthook = global_excepthook

# Setup monitoring (first time)
project_id = "checkmate-453316"
create_bq_run_monitor_datasets(project_id, logger=None)

# Record run trigger
append_to_trigger_bq_dataset(project_id, logger=None)

# Your code here...
```

## Migrating Existing Scripts

For scripts currently using `alerts_func.py`:

1. Replace `sys.path.append("./functions")` with nothing
2. Replace `from alerts_func import ...` with `from alerts_lib import ...`
3. Test the script

## Benefits

1. **No sys.path manipulation**: Clean imports that work from any directory
2. **Proper dependency management**: `uv` handles installation
3. **Editable mode**: Changes to `alerts_lib/` are immediately available
4. **Versioning**: Can be versioned and distributed separately
5. **Type hints**: Can add type stubs for better IDE support
6. **Testing**: Easier to unit test as a proper package

## Docker Integration

To use in Docker images, add to your Dockerfile:

```dockerfile
# Copy alerts library
COPY alerts_lib /app/alerts_lib

# Install with uv
RUN uv sync
```

Or if you want to publish it to PyPI later:

```dockerfile
RUN uv pip install alerts-lib
```

## Backwards Compatibility

The original `scripts/functions/alerts_func.py` still exists and can still be used with the old `sys.path.append()` method if needed. However, new code should use `alerts_lib` import.
