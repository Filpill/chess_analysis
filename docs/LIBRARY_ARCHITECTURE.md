# Library Architecture

This document explains the architecture and dependencies between the custom Python libraries in this project.

## Project Structure

```
chess_analysis/
├── libs/                           # All custom libraries
│   ├── gcp_common/                # Foundation library
│   │   ├── __init__.py
│   │   ├── gcp_common.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── alerts/                    # Alerting library
│   │   ├── __init__.py
│   │   ├── alerts.py
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── this-is-fine.jpg
│   │
│   ├── chess_ingestion/           # Chess.com API ingestion
│   │   ├── __init__.py
│   │   ├── chess_ingestion.py
│   │   └── pyproject.toml
│   │
│   └── chess_transform/           # Chess data transformation
│       ├── __init__.py
│       ├── chess_transform.py
│       └── pyproject.toml
│
├── scripts/                       # Pipeline scripts
├── docs/                          # Documentation
└── pyproject.toml                 # Main project config
```

## Library Dependency Graph

```
chess-analysis (main project)
│
├── gcp_common (foundation - no dependencies)
│   └── Provides: Cloud Logging, Secret Manager, Pub/Sub, GCS, BigQuery utilities
│
├── alerts (depends on gcp_common)
│   └── Provides: Email, Discord, BigQuery alerting & monitoring
│
├── chess_ingestion (depends on gcp_common)
│   └── Provides: Chess.com API ingestion, exponential backoff, GCS upload
│
└── chess_transform (depends on gcp_common)
    └── Provides: Data transformation, ECO extraction, deduplication, BigQuery loading
```

## Design Principles

### 1. Single Source of Truth
- **Problem**: GCP utility functions (Secret Manager, BigQuery, GCS) were duplicated across multiple files
- **Solution**: All GCP operations consolidated in `gcp_common`, other libraries import from it
- **Benefit**: One place to maintain and update GCP operations

### 2. Clear Dependency Hierarchy
- **Foundation Layer**: `gcp_common` has no internal dependencies
- **Feature Layers**: `alerts`, `chess_ingestion`, `chess_transform` build on top of foundation
- **Benefit**: No circular dependencies, clear layering, easy to test

### 3. Domain Separation
- **GCP utilities**: Generic GCP operations → `gcp_common`
- **Alerting**: Error notification and monitoring → `alerts`
- **Chess ingestion**: API requests and GCS upload → `chess_ingestion`
- **Chess transformation**: Data processing and BigQuery loading → `chess_transform`

### 4. Re-exports for Convenience
Libraries re-export commonly used functions from `gcp_common`:

```python
# These all work - same functions!
from alerts import gcp_access_secret
from chess_ingestion import log_printer  # (via gcp_common import)
from gcp_common import gcp_access_secret, log_printer
```

**Why?** Backwards compatibility and convenience - existing code continues to work without changes.

## Library Details

### gcp_common
**Purpose**: Common GCP utilities used across the project (foundation layer)

**Core Functions**:
- `initialise_cloud_logger(project_id)` - Cloud Logging setup
- `log_printer(msg, logger, severity, console_print)` - Dual logging
- `gcp_access_secret(project_id, secret_id, version_id)` - Secret Manager access
- `read_cloud_scheduler_message()` - Pub/Sub message decoding

**GCS Functions**:
- `upload_json_to_gcs_bucket()` - Upload JSON to GCS
- `list_files_in_gcs()` - List bucket contents
- `download_content_from_gcs()` - Download file content
- `delete_gcs_object()` - Delete GCS object
- `append_prefix_to_gcs_files()` - Rename with prefix
- `rename_prefix_of_gcs_files()` - Batch rename

**BigQuery Functions**:
- `check_bigquery_dataset_exists()` - Check dataset existence
- `create_bigquery_dataset()` - Create dataset
- `check_bigquery_table_exists()` - Check table existence
- `create_bigquery_table()` - Create table with optional partitioning
- `append_df_to_bigquery_table()` - Append DataFrame
- `query_bq_to_dataframe()` - Execute query, return DataFrame

**Dependencies**: Only Google Cloud SDK packages

**Import**: `from gcp_common import ...`

### alerts
**Purpose**: Alerting and error notification system

**Functions**:
- `load_alerts_environmental_config()` - Configure alert system
- `global_excepthook` - Automatic exception handling
- `send_email_message()` - Email via SMTP
- `send_discord_message()` - Discord webhook
- `create_bq_run_monitor_datasets()` - BigQuery monitoring tables
- `append_to_trigger_bq_dataset()` - Log run triggers
- `append_to_failed_bq_dataset()` - Log failures
- `build_error_email_msg()` - Build HTML email
- `build_error_discord_msg()` - Build Discord message

**Dependencies**:
- `gcp_common` (for Secret Manager, BigQuery operations)
- pandas, pygments, requests

**Import**: `from alerts import ...`

### chess_ingestion
**Purpose**: Chess.com API data ingestion with retry logic and GCS upload

**Functions**:
- `script_date_selection()` - Select date range for ingestion
- `generate_year_month_list()` - Generate YYYY/MM list
- `get_top_player_list()` - Extract players from leaderboard
- `generate_remaining_endpoint_combinations()` - Determine missing data
- `append_player_endpoints_to_https_chess_prefix()` - Build API URLs
- `exponential_backoff_request()` - HTTP request with retry
- `request_from_list_and_upload_to_gcs()` - Batch request and upload

**Dependencies**:
- `gcp_common` (for GCS operations)
- requests, python-dateutil

**Import**: `from chess_ingestion import ...`

### chess_transform
**Purpose**: Chess game data transformation and BigQuery loading

**Functions**:
- `script_date_endpoint_selection()` - Select date for loading
- `extract_last_url_component()` - Parse URL component
- `convert_unix_ts_to_date()` - Timestamp conversion
- `compare_sets_and_return_non_matches()` - Set difference
- `extract_eco_url_from_pgn()` - Extract ECO from PGN string
- `return_missing_data_list()` - Find missing data vs BigQuery
- `gcs_action_taken_dict()` - Create interaction metadata
- `generate_games_dataframe()` - Transform GCS JSON to DataFrame
- `deletion_interaction_list_handler()` - Delete empty GCS files

**Dependencies**:
- `gcp_common` (for GCS and BigQuery operations)
- pandas, numpy, python-dateutil

**Import**: `from chess_transform import ...`

## Usage Patterns

### Pattern 1: Using Foundation Only
```python
from gcp_common import initialise_cloud_logger, log_printer

logger = initialise_cloud_logger("checkmate-453316")
log_printer("Processing started", logger)
```

### Pattern 2: Using Alerts (Foundation Included)
```python
from alerts import (
    load_alerts_environmental_config,
    global_excepthook,
    gcp_access_secret,  # Re-exported from gcp_common
)
import sys

env_vars = load_alerts_environmental_config()
sys.excepthook = global_excepthook
```

### Pattern 3: Chess Ingestion Pipeline
```python
from gcp_common import initialise_cloud_logger, list_files_in_gcs
from chess_ingestion import (
    script_date_selection,
    generate_year_month_list,
    get_top_player_list,
    generate_remaining_endpoint_combinations,
    request_from_list_and_upload_to_gcs,
)

# Initialize logging
logger = initialise_cloud_logger("checkmate-453316")

# Get existing data
files_in_gcs = list_files_in_gcs("chess-api", logger)
players_data = [f for f in files_in_gcs if f.startswith("player/")]

# Determine what to fetch
year_month_list = generate_year_month_list(start_date, end_date)
top_players = get_top_player_list(leaderboard_response, logger)
remaining = generate_remaining_endpoint_combinations(
    bucket_name, players_data, top_players, year_month_list, logger
)

# Fetch and upload
request_from_list_and_upload_to_gcs(bucket_name, request_urls, headers, logger)
```

### Pattern 4: Chess Transform Pipeline
```python
from gcp_common import (
    initialise_cloud_logger,
    list_files_in_gcs,
    append_df_to_bigquery_table,
)
from chess_transform import (
    generate_games_dataframe,
    return_missing_data_list,
    deletion_interaction_list_handler,
)

# Initialize
logger = initialise_cloud_logger("checkmate-453316")

# Get endpoints to process
files = list_files_in_gcs(bucket_name, logger)
endpoints = return_missing_data_list("gcs_endpoint", table_id, files, "EU", logger)

# Transform and load
for endpoint in endpoints:
    df_games, interaction_dict = generate_games_dataframe(endpoint, bucket_name, logger)
    if df_games is not None:
        append_df_to_bigquery_table(df_games, table_id_games, logger)

# Cleanup empty files
deletion_interaction_list_handler(df_interactions, bucket_name, logger)
```

### Pattern 5: Complete Pipeline with Alerting
```python
import sys
from alerts import load_alerts_environmental_config, global_excepthook
from gcp_common import initialise_cloud_logger
from chess_ingestion import request_from_list_and_upload_to_gcs
from chess_transform import generate_games_dataframe

# Setup alerting
env_vars = load_alerts_environmental_config()
sys.excepthook = global_excepthook

# Run pipeline (errors automatically reported)
logger = initialise_cloud_logger("checkmate-453316")
request_from_list_and_upload_to_gcs(bucket_name, urls, headers, logger)
df, metadata = generate_games_dataframe(endpoint, bucket_name, logger)
```

## Migration Path

When adding functionality, use this decision tree:

1. **Is it a generic GCP operation (logging, secrets, GCS, BigQuery)?** → Add to `gcp_common`
2. **Is it alerting/notification/monitoring specific?** → Add to `alerts`
3. **Is it Chess.com API ingestion related?** → Add to `chess_ingestion`
4. **Is it chess data transformation/loading related?** → Add to `chess_transform`
5. **Is it highly specific to a single script?** → Keep in the script file

### Examples:
- New GCS operation → `gcp_common`
- Slack notification → `alerts`
- New Chess.com API endpoint handler → `chess_ingestion`
- New chess opening classification logic → `chess_transform`
- One-off data fix script → `scripts/`

### When to Create a New Library:
Consider creating a new library when:
- You have 3+ related functions for a specific domain
- Multiple scripts need the same functionality
- The code is reusable across projects
- Clear separation of concerns is needed

## Benefits of This Architecture

✅ **No Code Duplication** - Single source of truth for shared functions
✅ **Clear Dependencies** - Easy to understand what depends on what
✅ **Domain Separation** - Each library has a clear, focused purpose
✅ **Backwards Compatible** - Re-exports maintain existing code
✅ **Maintainable** - Changes propagate automatically via imports
✅ **Testable** - Libraries can be tested independently
✅ **Reusable** - Can be extracted to separate repos if needed
✅ **Scalable** - Easy to add new libraries following the same pattern

## Historical Context

**Evolution of the architecture:**
1. **Phase 1**: Functions scattered in `scripts/functions/` directory
   - Problems: Hard to find, duplicated code, unclear dependencies
2. **Phase 2**: Created `gcp_common` and `alerts` libraries
   - Consolidated GCP utilities and alerting functions
   - Removed BigQuery function duplication from alerts
3. **Phase 3**: Created `chess_ingestion` and `chess_transform` libraries
   - Moved domain-specific chess data pipeline functions to proper libraries
   - Clear separation between ingestion (API → GCS) and transformation (GCS → BigQuery)

**Result**: Cleaner architecture with four focused, well-defined libraries

## Future Considerations

If these libraries grow significantly, consider:

1. **Separate repositories** - Each library in its own repo with proper versioning
2. **PyPI publishing** - Install via `pip install gcp-common chess-ingestion`
3. **Semantic versioning** - Track breaking changes properly
4. **CI/CD** - Automated testing for each library
5. **Type hints** - Add comprehensive type annotations
6. **Unit tests** - Add test suites for each library
7. **Documentation** - Generate API docs with Sphinx or mkdocs
