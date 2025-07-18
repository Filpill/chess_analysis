import os
import json
import google.cloud.logging as cloud_logging
from google.cloud import storage
from shared_func import initialise_cloud_logger

# Initialise Logger
project_name = "checkmate-453316"
logger = initialise_cloud_logger(project_name)
logger.log_text(f"Initialising Test Script For Passing In PUB/SUB MESSAGE into ENV variable")

# Appending Path To Function
sys.path.append(f"./functions")

# Retrieving MESSAGE environement variable which came from pub/sub
encoded_message = os.getenv("MESSAGE")
decoded_message = base64.b64decode(encoded_message).decode("utf-8")

if encoded_message:
    statement = f"-----TESTING------ Recieved Pub/Sub Message: {encoded_message}"
    print(statement)
    logger.log_text(statement)

else:
    statement = f"------TESTING------- No Message Inside Environment Variable"
    print(statement)
    logger.log_text(statement)
