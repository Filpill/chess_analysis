FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:stable

# Change to bash shell
SHELL ["/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Install pip, git, and other dependencies
RUN apt-get update && apt-get install -y python3.11-venv python3-pip git curl

# Create virual environemnt and install dependencies
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/requirements.txt > requirements.txt
RUN python3.11 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

# Set the entrypoint
CMD ["bash"]
