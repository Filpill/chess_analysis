## Common dbt Command Template

#### General Commands
```bash
dbt init \<project_name\>              # Initialise project structure for dbt
dbt seed                               # Load static CSV data into warehouse
dbt clean                              # Deletes contents of target folder of compiled code
dbt docs generate                      # Generates a fresh documentation from dbt project
dbt docs serve                         # Serves Documentation on localhost
```

#### Build/Test/Run Models
> A **build** command will run your models, seed files in addition to testing them.
> A **run** command will exclusively run your models.
> A **test** command will exclusively run your dbt tests.

```bash
dbt build/test/run                     # All Models
dbt build/test/run -s \<model name\>   # Run selected model only
dbt build/test/run -s \<model_name\>+  # Run all models downstream of selected
dbt build/test/run -s +\<model_name\>  # Run all models upstream of selected
dbt build/test/run
```

#### Example Command Flags
```bash
dbt run --full-refresh                            # Full overwrite on incremental models
dbt test --vars '{test_start_date: "2025-03-01"}' # Override default testing period
```
