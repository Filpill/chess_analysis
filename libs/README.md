# Custom Libraries

This directory contains custom Python libraries used by the chess data pipeline.

## Libraries

### gcp_common
**Purpose**: Common GCP utilities (foundation layer)

**Location**: `libs/gcp_common/`

**Provides**:
- Cloud Logging initialization and log printing (dual output to cloud + console)
- Secret Manager access
- Pub/Sub message decoding
- GCS operations (upload, download, list, delete, rename)
- BigQuery operations (create datasets/tables, query, append data)

**Import**: `from gcp_common import ...`

**Documentation**: See `gcp_common/README.md`

### alerts
**Purpose**: Alerting and error notification system

**Location**: `libs/alerts/`

**Provides**:
- Email alerts via Gmail SMTP
- Discord webhook notifications
- BigQuery run monitoring
- Global exception hooks for automatic error reporting

**Dependencies**: `gcp-common`

**Import**: `from alerts import ...`

**Documentation**: See `alerts/README.md`

### chess_ingestion
**Purpose**: Chess.com API data ingestion functions

**Location**: `libs/chess_ingestion/`

**Provides**:
- Date range selection for ingestion
- Chess.com leaderboard and player endpoint generation
- Exponential backoff request handling
- Batch API requests with automatic retry
- Direct upload to GCS

**Dependencies**: `gcp-common`

**Import**: `from chess_ingestion import ...`

### chess_transform
**Purpose**: Chess game data transformation and loading

**Location**: `libs/chess_transform/`

**Provides**:
- GCS to DataFrame transformation
- Chess opening (ECO) extraction from PGN
- Game data deduplication
- Missing data detection (compare local vs BigQuery)
- GCS object lifecycle management (deletion of empty files)

**Dependencies**: `gcp-common`

**Import**: `from chess_transform import ...`

## Installation

All libraries are configured as editable packages in the main `pyproject.toml`:

```bash
uv sync
```

## Adding New Libraries

1. Create directory: `libs/my_new_lib/`
2. Create package structure:
   ```
   libs/my_new_lib/
   ├── __init__.py
   ├── my_new_lib.py
   ├── pyproject.toml
   └── README.md (optional)
   ```
3. Add to main `pyproject.toml`:
   ```toml
   [project]
   dependencies = [
       "my-new-lib",
       # ...
   ]

   [tool.uv.sources]
   my-new-lib = { path = "./libs/my_new_lib", editable = true }
   ```
4. Run `uv sync`

## Architecture

See `docs/LIBRARY_ARCHITECTURE.md` for detailed architecture documentation including:
- Dependency graph
- Design principles
- Usage patterns
- Migration guidelines
