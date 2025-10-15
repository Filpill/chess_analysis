# Library Architecture

This document explains the architecture and dependencies between the custom Python libraries in this project.

## Project Structure

```
chess_analysis/
├── libs/                           # All custom libraries
│   ├── gcp_common_lib/            # Foundation library
│   │   ├── gcp_common_lib/
│   │   │   ├── __init__.py
│   │   │   └── gcp_common.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── alerts_lib/                # Alerting library
│       ├── alerts_lib/
│       │   ├── __init__.py
│       │   └── alerts.py
│       ├── pyproject.toml
│       └── README.md
│
├── scripts/                       # Pipeline scripts
├── docs/                          # Documentation
└── pyproject.toml                 # Main project config
```

## Library Dependency Graph

```
chess-analysis (main project)
├── gcp_common_lib (foundation)
│   └── Provides: Cloud Logging, Secret Manager, Pub/Sub utilities
│
└── alerts_lib (depends on gcp_common_lib)
    └── Provides: Email, Discord, BigQuery alerting
```

## Design Principles

### 1. Single Source of Truth
- **Problem**: `gcp_access_secret` was duplicated in both libraries
- **Solution**: `alerts_lib` imports from `gcp_common_lib`
- **Benefit**: One place to maintain and update

### 2. Clear Dependency Hierarchy
- **Foundation Layer**: `gcp_common_lib` has no internal dependencies
- **Feature Layer**: `alerts_lib` builds on top of foundation
- **Benefit**: No circular dependencies, clear layering

### 3. Re-exports for Convenience
`alerts_lib` re-exports `gcp_access_secret` so users can import from either:

```python
# Both work - same function!
from alerts_lib import gcp_access_secret
from gcp_common_lib import gcp_access_secret
```

**Why?** Existing code using `alerts_lib.gcp_access_secret` continues to work without changes.

## Library Details

### gcp_common_lib
**Purpose**: Common GCP utilities used across the project

**Functions**:
- `initialise_cloud_logger(project_id)` - Cloud Logging setup
- `log_printer(msg, logger, severity, console_print)` - Dual logging
- `gcp_access_secret(project_id, secret_id, version_id)` - Secret Manager access
- `read_cloud_scheduler_message()` - Pub/Sub message decoding

**Dependencies**: Only Google Cloud SDK packages

**Import**: `from gcp_common_lib import ...`

### alerts_lib
**Purpose**: Alerting and error notification system

**Functions**:
- `load_alerts_environmental_config()` - Configure alert system
- `global_excepthook` - Automatic exception handling
- `send_email_message()` - Email via SMTP
- `send_discord_message()` - Discord webhook
- `create_bq_run_monitor_datasets()` - BigQuery monitoring tables
- `append_to_trigger_bq_dataset()` - Log run triggers
- `append_to_failed_bq_dataset()` - Log failures

**Dependencies**:
- `gcp_common_lib` (for Secret Manager access)
- Google Cloud BigQuery
- pandas, pygments, requests

**Import**: `from alerts_lib import ...`

## Usage Patterns

### Pattern 1: Using Foundation Only
```python
from gcp_common_lib import initialise_cloud_logger, log_printer

logger = initialise_cloud_logger("checkmate-453316")
log_printer("Processing started", logger)
```

### Pattern 2: Using Alerts (Foundation Included)
```python
from alerts_lib import (
    load_alerts_environmental_config,
    global_excepthook,
    gcp_access_secret,  # Re-exported from gcp_common_lib
)
import sys

env_vars = load_alerts_environmental_config()
sys.excepthook = global_excepthook
```

### Pattern 3: Using Both Explicitly
```python
from gcp_common_lib import initialise_cloud_logger, log_printer
from alerts_lib import global_excepthook

logger = initialise_cloud_logger("checkmate-453316")
log_printer("Setting up alerts", logger)
sys.excepthook = global_excepthook
```

## Migration Path

When adding functionality:

1. **Is it GCP-related and broadly useful?** → Add to `gcp_common_lib`
2. **Is it alerting/notification specific?** → Add to `alerts_lib`
3. **Is it pipeline-specific?** → Keep in `scripts/functions/`

## Benefits of This Architecture

✅ **No Code Duplication** - Single source of truth for shared functions
✅ **Clear Dependencies** - Easy to understand what depends on what
✅ **Backwards Compatible** - Re-exports maintain existing code
✅ **Maintainable** - Changes propagate automatically via imports
✅ **Testable** - Libraries can be tested independently
✅ **Reusable** - Can be extracted to separate repos if needed

## Future Considerations

If these libraries grow significantly, consider:

1. **Separate repositories** - Each library in its own repo with proper versioning
2. **PyPI publishing** - Install via `pip install gcp-common alerts-lib`
3. **Semantic versioning** - Track breaking changes properly
4. **CI/CD** - Automated testing for each library
