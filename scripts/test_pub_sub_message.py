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
pub_sub_message = os,getenv("MESSAGE")
if raw:
    message = json.loads(raw)
    statement = f"Recieved Pub/Sub Message: {message}"
    print(statement)
    logger.log_text(statement)

else:
    statement = f"No Message Inside Environment Variable"
    print(statement)
    logger.log_text(statement)
