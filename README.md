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
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/exports/cicd.png " alt="drawing" width="800"/>
</p>

#### Project Directories
The project is segmented into the following directories which contain the following:

<div align = center>
  
| Directory  | Description |
| :------------- | :------------- |
| **scripts/**   | Core python scripts/notebooks to process chess data  |
| **scripts/cloud_functions/**   | Python Functions for instantiating or controlling GCP resources  |
| **docker/**   | Contains dockerfiles to define toolng environment for running data deployment pipeline  |
| **dash/**   | Contains files for developing "Dash" python applications  |
| **bigquery/**   | Contains files runnining SQL scripts on BQ  |
| **functions/** | Functions which are imported into the core data processing scripts  |
| **inputs/** | Input parameter files for passing into core data processing scripts |
| **diagrams/** | Illustrations for architectural design  |
  
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

| File | Description |
| :------------- | :------------- |
| **pyproject.toml** | Keep track of key library dependencies |
| **uv.lock** | Precisely captures all python package versions |
| **requirements.txt** | Default python requirements file compiled from pyproject.toml |

</div>

To create a virtual environment:
```bash
uv venv --python 3.11
```

To add packages to pyproject.toml:
```bash
uv add <package-name>
```

To compile package to requirements.txt:
```bash
uv pip compile pyproject.toml > requirements.txt
```

To activate virtual environment locally:
```bash
source .venv/bin/activate
```

To install python library requirements:
```bash
uv sync
```

#### Docker Image
A docker image has been created to package together the necessary gcloud and python tooling so it can be readily pulled by the Virtual Machine.

> *Does not house any script files; docker image will not automatically update on each pipeline revision.*

<div align = center>

| Docker File | Description |
| :------------- | :------------- |
| **Dockerfile** | Configuration creating tool environment ready for executing |
| **variables** | List of variables for plugging into local command-line docker scripts  |

</div>

> *Local docker bash scripts are not saved in this project repo*

## Pipeline Architecture
This is a high-level view of the key components in the pipeline architecture for executing data pipeline resources to both ingest, transform and load our chess data:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/exports/pipeline_architecture.png " alt="drawing" width="800"/>
</p>

## Ingestion Dataflow into GCS
The following flow chart illustrates how data is processed when ingesting data into GCS:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/exports/ingestion_dataflow.png " alt="drawing" width="800"/>
</p>

## Transform/Load Dataflow into BigQuery
The following flow chart illustrates how data is processed when transforming and loading data from GCS to BigQuery:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/exports/transform_dataflow.png " alt="drawing" width="800"/>
</p>

## BigQuery SQL Transformation and Data Modelling
This illustration contains the high-level data model for the BigQuery SQL transformations:
<p align = center>                                                                                                                                   
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/exports/sql_tables.png " alt="drawing" width="800"/> 
</p>                                                                                                                                                 


## Chess Analysis
Here are a couple of sample matplotlib charts which are analysing some player data:
<p align = center>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/analysis/top_openings.png" alt="drawing" width="800"/>
    <img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/analysis/time_of_day.png" alt="drawing" width="800"/>
</p>
