FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

# Change to bash shell
SHELL ["/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Make directories for storing functions and input files
RUN mkdir /app/inputs && mkdir /app/functions

# Install pip, git, and other dependencies
RUN apt-get update && apt-get install -y python3-pip git curl vim

# Create virual environemnt and install dependencies
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/requirements.txt                          > /app/requirements.txt
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/bigquery_chess_transform_load.py > /app/main.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/inputs/bq_load_settings.json              > /app/inputs/bq_load_settings.json
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/functions/shared_func.py                  > /app/functions/shared_func.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/functions/gcs_func.py                     > /app/functions/gcs_func.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/functions/bq_func.py                      > /app/functions/bq_func.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/functions/transform_func.py               > /app/functions/transform_func.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/functions/__init__.py                     > /app/functions/__init__.py
RUN pip install -r /app/requirements.txt --break-system-packages

# Set the entrypoint
CMD ["python3", "/app/main.py"]
