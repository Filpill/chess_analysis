# Chess.com API - Data Engineering Pipeline
I've designed an end-to-end ETL pipeline for ingesting large volumes of data from the chess.com API to GCP for analytical purposes.

> *This pipeline is purely educational in terms of its design in order to learn how to bring together multiple cloud resources into executing a reliable and cohesive data pipeline.*

## Data Ingestion Into GCS

In the chess.com API design, all the historically archived game data is segmented by the **player** endpoint. Before being able to being able to retrieve **game** data, we need a way to harvest a list of usernames.
This is accomplished by making a request to the **leaderboards** endpoint of the chess.com API to get a list of all the top players.

For each **player** in the games archive, we make a list of requests for each **monthly date period**. 

Data landing into the bucket, closely mirrors the pathing of the API endpoints for clarity and consistency.

Before making our requests, we check to see if the data is already exists inside our GCS bucket which yields the following benefits: 
- **Efficiency:** | Not wasting our time re-requesting data we've already ingested.
- **Restartability** | We can easily restart our ingestion scripts if the pipeline fails.

After the GCS ingestion is completed, the data transformation script will follow up to land the data into BigQuery. *< work-in-progress >*

## CI/CD Process
This is rough guideline of the CI/CD process that gets executed when the **main** branch is updated.
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/cicd.drawio.png " alt="drawing" width="800"/>
</p>

#### Project Directories
The project is segmented into the following directories which contain the following:

<div align = center>
  
| Directory  | Description |
| :------------- | :------------- |
| **scripts**   |  Core python scripts/notebooks to process chess data  |
| **functions** | Functions which are imported into the core data processing scripts  |
| **inputs** | Input parameter files for passing into core data processing scripts |
| **diagrams** | Illustrations for architectural design  |
  
</div>

#### Terraform Configuration
The following is an overview of the terraform configuration:

<div align = center>
  
| Terraform File | Description |
| :------------- | :------------- |
| **.github/workflows/terraform.yml**  | Terraform config for GCP authentication and terraform deployment steps |
| **providers.tf** | Declaring GCP project provider |
| **main.tf**  | GCP resource configuration to be created/updated/deleted |
| **backend.tf** | Terraform state file location on GCS |
| **variables.tf** | Variable declaration for terraform configuration |
| **terraform.tfvars*** | Values for declared variables |
  
</div>

#### Python Environment
Python environment is created using the **uv** package manager and the following files specify dependancies:

<div align = center>

| Terraform File | Description |
| :------------- | :------------- |
| **pyproject.toml** | Keep track of key library dependencies |
| **uv.lock** | Precisely captures all package versions to be installed |

</div>

To create a virtual environment:
```bash
uv venv --python 3.11
```

To activate vrtual environment locally:
```bash
source .venv/bin/activate
```

To install python library requirements:
```bash
uv sync
```

## Architecture Diagram
This is a high-level view of the key components in the pipeline architecture and how data is flowing downstream:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/architecture.drawio.png " alt="drawing" width="800"/>
</p>

## Chess Analysis
Here are a couple of sample matplotlib charts which are analysing some player data:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/charts/top_openings.png" alt="drawing" width="800"/>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/charts/time_of_day.png" alt="drawing" width="800"/>
</p>
