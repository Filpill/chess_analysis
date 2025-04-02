FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

# Change to bash shell
SHELL ["/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Install pip, git, and other dependencies
RUN apt-get update && apt-get install -y python3-pip git curl vim

# Create virual environemnt and install dependencies
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/cloud_functions/vm_start/requirements.txt > /app/requirements.txt
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/cloud_functions/vm_start/main.py > /app/main.py
RUN pip install -r /app/requirements.txt --break-system-packages

# Set the entrypoint
CMD ["python3", "/app/main.py"]
