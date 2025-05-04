FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

# Change to bash shell
SHELL ["/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Making Directories
RUN mkdir /app/assets && mkdir /app/assets/fonts && mkdir /app/assets/img 

# Install pip, git, and other dependencies
RUN apt-get update && apt-get install -y python3-pip git curl vim

# Create virual environment and install dependencies
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/requirements.txt                        > /app/requirements.txt
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/bq_monitor/bq_monitor.py           > /app/main.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/bq_monitor/assets/styles.css       > /app/assets/styles.css
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/bq_monitor/assets/fonts/trebuc.ttf > /app/assets/fonts/trebuc.ttf
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/bq_monitor/assets/img/bigquery.svg > /app/assets/img/bigquery.svg
RUN pip install -r /app/requirements.txt --break-system-packages

# Set the entrypoint
CMD ["gunicorn", "--bind", ":8080", "main:app.server"]
