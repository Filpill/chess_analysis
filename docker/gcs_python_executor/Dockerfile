FROM python:3.11-slim

# Avoid interactive prompts from apt / gcloud
ENV DEBIAN_FRONTEND=noninteractive \
    CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Install Google Cloud CLI (includes gsutil)
RUN apt-get update && apt-get install -y --no-install-recommends vim jq \
      ca-certificates curl gnupg \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
      | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
      > /etc/apt/sources.list.d/google-cloud-sdk.list \
 && apt-get update && apt-get install -y --no-install-recommends \
      google-cloud-cli \
 && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# (optional) show versions during build logs
RUN gcloud --version && gsutil --version && uv --version

# Set working directory
WORKDIR /app

# Copy your shell script into the container
COPY download_and_run.sh /app/download_and_run.sh
RUN chmod +x /app/download_and_run.sh

# Default command (runs your script)
ENTRYPOINT ["/app/download_and_run.sh"]
