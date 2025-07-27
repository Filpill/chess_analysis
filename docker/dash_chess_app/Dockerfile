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
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/requirements.txt                         > /app/requirements.txt
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/chess_app/main.py                   > /app/main.py
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/chess_app/assets/img/wk.png         > /app/assets/img/wk.png
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/chess_app/assets/img/bk.png         > /app/assets/img/bk.png
RUN curl https://raw.githubusercontent.com/Filpill/chess_analysis/refs/heads/main/dash/chess_app/assets/img/chess_logo.png > /app/assets/img/chess_logo.png
RUN pip install -r /app/requirements.txt --break-system-packages

# Set the entrypoint
CMD ["gunicorn", "--bind", ":8080", "main:server"]
