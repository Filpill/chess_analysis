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
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/requirements.txt                           > /app/requirements.txt
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/test_pub_sub_message.py            > /app/main.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/functions/shared_func.py           > /app/functions/shared_func.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/scripts/functions/__init__.py              > /app/functions/__init__.py
RUN pip install -r /app/requirements.txt --break-system-packages

# Set the entrypoint
CMD ["python3", "/app/main.py"]
