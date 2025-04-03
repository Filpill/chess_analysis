import subprocess
import google.cloud.logging as cloud_logging
from googleapiclient import discovery
from google.oauth2 import service_account
from google.auth import default

def initialise_cloud_logger(project_id):
    client = cloud_logging.Client(project=project_id)
    client.setup_logging()
  
    logger = client.logger(__name__)
    logger.propagate = False
    return logger

def main():
    credentials, project_id = default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    # Initialise Logger Object
    logger = initialise_cloud_logger(project_id)
    logger.log_text(f"Reading VM initialiser script", severity="INFO")

    # Read shell script
    with open("vm_initialiser.sh", "r") as file:
        vm_initialiser_script = file.read()

    # Run the shell script using subprocess
    logger.log_text(f"Running VM initialiser script...", severity="INFO")
    script_runner = subprocess.run(["bash", "-c", vm_initialiser_script], capture_output=True, text=True)

    # Print the output and errors (if any)
    logger.log_text(script_runner.stdout, severity="INFO")
    logger.log_text(script_runner.stderr, severity="INFO")
    print("Script complete!")

if __name__ == "__main__":
    main()
