# Custom Libraries

This directory contains custom Python libraries used by the chess data pipeline.

## Libraries

### gcp_common_lib
**Purpose**: Common GCP utilities (foundation layer)

**Location**: `libs/gcp_common_lib/`

**Provides**:
- Cloud Logging initialization
- Log printing (dual output to cloud + console)
- Secret Manager access
- Pub/Sub message decoding

**Import**: `from gcp_common_lib import ...`

**Documentation**: See `gcp_common_lib/README.md`

### alerts_lib
**Purpose**: Alerting and error notification system

**Location**: `libs/alerts_lib/`

**Provides**:
- Email alerts via Gmail SMTP
- Discord webhook notifications
- BigQuery run monitoring
- Global exception hooks

**Dependencies**: `gcp-common`

**Import**: `from alerts_lib import ...`

**Documentation**: See `alerts_lib/README.md`

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
   ├── my_new_lib/
   │   ├── __init__.py
   │   └── module.py
   ├── pyproject.toml
   └── README.md
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
