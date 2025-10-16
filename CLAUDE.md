# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chess.com API data engineering pipeline built on Google Cloud Platform (GCP). The system ingests chess game data from Chess.com's API, stores it in Google Cloud Storage (GCS), loads it into BigQuery for analytics, and provides visualization through Dash web applications.

**Related Repositories:**
- Data Transformation: https://github.com/Filpill/dbt_chess
- Data Orchestration: https://github.com/Filpill/airflow_chess

## Python Environment

This project uses **uv** package manager (not pip). Key files:
- `pyproject.toml` - Main dependency declarations
- `uv.lock` - Exact package versions
- `.python-version` - Python 3.11

### Common Commands

```bash
# Create virtual environment
uv venv --python 3.11

# Activate environment
source .venv/bin/activate

# Install dependencies
uv sync

# Add new package
uv add <package-name>
```

## Core Scripts

The repository contains two primary data processing scripts (both are Marimo notebooks):

### 1. GCS Ingestion Script
**Path:** `scripts/gcs_chess_ingestion.py`
- Fetches chess game data from Chess.com API leaderboards and player endpoints
- Stores JSON responses in GCS bucket at `gs://chess-api`
- Uses `scripts/inputs/gcs_ingestion_settings.json` for configuration
- Implements idempotency checks to avoid re-downloading existing data
- Uses exponential backoff for API rate limiting

### 2. BigQuery Transform/Load Script
**Path:** `scripts/bigquery_chess_transform_load.py`
- Reads JSON files from GCS
- Transforms and loads game data into BigQuery dataset `chess_raw`
- Two main tables: `games` (partitioned by `game_date`) and `loading_completed` (tracks processed GCS objects)
- Uses `scripts/inputs/bq_load_settings.json` for configuration
- Handles deduplication of game_id's when players in batch play each other

**Script Settings:** Both scripts support `script_setting` parameter:
- `"prod"` - Full production run
- `"test"` - Limited data volume for testing
- `"dev"` - Single test case (specified in config)
- `"default"` - Uses manual date ranges from config

## Architecture: Event-Driven VM Orchestration

The pipeline uses an event-driven architecture with ephemeral VMs:

1. **Cloud Scheduler** triggers Pub/Sub message with job configuration (JSON files in `scripts/cloud_scheduler_json/`)
2. **VM Initialiser** (Cloud Run service at `cloud_run/vm_initialiser/main.py`) receives Pub/Sub message and creates GCE VM with containerized workload
3. **VM executes** Python script inside Docker container pulled from Artifact Registry
4. **Log Sink** detects container exit event and publishes to delete-vm-topic
5. **VM Deleter** (Cloud Run service at `cloud_run/vm_deleter/main.py`) receives message and deletes the VM

**Key Design:** VMs are zone-resilient - the initialiser iterates through multiple zones (europe-west1/2) if resources are exhausted.

## Docker Images

Docker images package the execution environment and are stored in GCP Artifact Registry at `europe-west2-docker.pkg.dev/checkmate-453316/docker-chess-repo/`.

**Key Images:**
- `gcs_python_executor` - Runs Any Python Script Saved within GCS
  - Uses `uv sync --frozen` to install dependencies from `pyproject.toml` and `uv.lock`
  - Installs local libraries (`gcp_common`, `alerts`, `chess_ingestion`, `chess_transform`) automatically
  - Downloads scripts from GCS at runtime and executes them in a virtual environment
- `vm_initialiser` - Cloud Run service for creating VMs
- `vm_deleter` - Cloud Run service for deleting VMs
- `dash_chess_app` - Chess analysis Dash application
- `bq_monitor_dash` - BigQuery monitoring dashboard

Each Docker directory contains:
- `Dockerfile` - Image configuration
- `variables` - Build parameters (image name, AR repo)
- Build/push scripts for deploying to Artifact Registry

**Note:** Docker image deployments are manual (via CLI), not automated through CI/CD.

## Terraform Infrastructure

All GCP resources are managed via Terraform:

- `main.tf` - Primary resource definitions (Cloud Run services, Pub/Sub topics, Cloud Scheduler jobs, Eventarc triggers, Log Sinks)
- `providers.tf` - GCP provider configuration
- `backend.tf` - State file stored in GCS
- CI/CD via `.github/workflows/terraform.yml` - Runs `terraform apply` on push to main branch

**Important:** Terraform workflow syncs the following to `gs://chess-deployments/` bucket:
- `scripts/` directory (excluding `__pycache__` and `__marimo__` directories)
- `pyproject.toml`, `uv.lock`, `.python-version` (for dependency management)
- `libs/` directory (local Python packages: `gcp_common`, `alerts`, `chess_ingestion`, `chess_transform`)

## Function Libraries

### Core Function Modules (Legacy)
Reusable functions are organized in `scripts/functions/`:
- `ingestion_func.py` - API requests, endpoint generation, exponential backoff
- `transform_func.py` - Data transformation, date conversion, dataframe generation
- `gcs_func.py` - GCS operations (upload, download, list, delete)
- `bq_func.py` - BigQuery operations (create datasets/tables, query, append)

These functions are imported by the main processing scripts via relative path manipulation (`sys.path.append`).

### GCP Common Library (gcp_common_lib)
A proper Python package for common GCP utilities located in `libs/gcp_common_lib/`:
- **Installation**: Configured as local editable package in `pyproject.toml` - install with `uv sync`
- **Import**: `from gcp_common_lib import log_printer, initialise_cloud_logger, gcp_access_secret, read_cloud_scheduler_message`
- **Features**: Cloud Logging initialization, log printing to console+cloud, Secret Manager access, Pub/Sub message decoding
- **Replaces**: `shared_func.py` (old import path)

### Alerts Library (alerts_lib)
A proper Python package for alerting functionality located in `libs/alerts_lib/`:
- **Installation**: Configured as local editable package in `pyproject.toml` - install with `uv sync`
- **Import**: `from alerts_lib import load_alerts_environmental_config, global_excepthook`
- **Features**: Email alerts (Gmail SMTP), Discord webhooks, BigQuery run monitoring
- **Usage**: Sets up global exception hooks to automatically send alerts on crashes
- **Configuration**: Via environment variables (`TOGGLE_ENABLED_ALERT_SYSTEMS`, `TO_ADDRS`, `APP_ENV`)
- **Dependencies**: Depends on `gcp-common` for Secret Manager access

See `docs/ALERTS_MIGRATION.md`, `docs/GCP_COMMON_MIGRATION.md`, and `docs/LIBRARY_ARCHITECTURE.md` for details.

## Dash Applications

Two Dash web applications for visualization:

1. **Chess Analysis App** (`dash/chess_app/main.py`)
   - Queries BigQuery aggregate tables (`prod_aggregate.weekly_openings`)
   - Interactive visualizations: bar charts, sunbursts, scatter plots, heatmaps
   - Filters: date range, time class, opening archetypes, minimum games threshold
   - Deployed to Cloud Run

2. **BQ Monitor** (`dash/bq_monitor/bq_monitor.py`)
   - Monitors BigQuery job execution
   - Deployed to Cloud Run

Both apps use `gunicorn` for production serving (port 8080) and authenticate with GCP via default service account credentials.

## Testing Workflows

- Use `script_setting: "dev"` in config JSON files to test individual endpoints without full pipeline execution
- Use `script_setting: "test"` with `test_volume` parameter to limit data volume
- Cloud Scheduler jobs have `paused` parameter in Terraform to disable scheduling
- Test Pub/Sub messages can be sent via `scripts/test_pub_sub_message.py`
- Test alerting via `scripts/test_alert.py`

## GCP Project Configuration

- Project ID: `checkmate-453316`
- Primary Region: `europe-west2`
- GCS Bucket: `chess-api`
- BigQuery Dataset: `chess_raw`
- Data Location: `EU`

## Common Development Patterns

1. **Adding new scheduled job:**
   - Create JSON config in `scripts/cloud_scheduler_json/`
   - Add Cloud Scheduler resource in `main.tf` referencing the JSON
   - Ensure corresponding Docker image exists in Artifact Registry

2. **Modifying data processing:**
   - Edit Marimo notebooks (`gcs_chess_ingestion.py` or `bigquery_chess_transform_load.py`)
   - Update library functions in `libs/` if reusable logic changes
   - Test locally with `script_setting: "dev"`
   - Changes sync to GCS on next terraform apply (scripts, libraries, and dependencies)
   - Only rebuild Docker image if modifying the container environment itself

3. **Updating infrastructure:**
   - Modify `main.tf`
   - Commit to feature branch and test
   - Merge to main triggers automatic `terraform apply`
