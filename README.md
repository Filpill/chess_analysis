# Chess.com API - Data Engineering Pipeline
Designing a data pipeline for analysing Chess Game Data.

## CI/CD Process
Below is a rough guideline of the CI/CD process that gets executed when the **main** branch is updated.
<p align = center>
<img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/cicd.drawio.png " alt="drawing" width="800"/>
</p>

#### Project Directories
The project is segmented into the following directories and contain the following 
- **scripts** - Core python scripts/notebooks to process chess data
- **functions** - Functions which are imported into the core data processing scripts
- **inputs** - JSON files which supply input parameters into core data processing scripts:wq
- **diagrams** - Illustrations for architectural design

#### Terraform Config
- **.github/workflows/terraform.yml** - Terraform config for GCP authentication and terraform deployment steps
- **providers.tf** - Configuration for GCP project
- **main.tf** - Configuration for GCP resources being created/updated/deleted
- **backend.tf** - Storage location of terraform state file
- **variables.tf** - Variable declaration for configuration
- **terraform.tfvars** - Values for declared variables

#### Python Environment
- **pyproject.toml** - Python configurarion and key library dependencies
- **uv.lock** - Captures all the packages and versions to be installed to execute project

## Architecture Diagram
<p align = center>
<img src="https://github.com/Filpill/chess_analysis/blob/main/diagrams/architecture/architecture.drawio.png " alt="drawing" width="800"/>
</p>

## Chess Analysis
<p align = center>
<img src="https://github.com/Filpill/chess_analysis/blob/main/charts/top_openings.png" alt="drawing" width="800"/>
<img src="https://github.com/Filpill/chess_analysis/blob/main/charts/time_of_day.png" alt="drawing" width="800"/>
</p>
