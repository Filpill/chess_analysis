import os
import sys
import json
import base64
import google.cloud.logging as cloud_logging
from google.cloud import storage

sys.path.append(f"./functions")
sys.path.append(f"../functions")
from shared_func import initialise_cloud_logger

try:
    # Initialise Logger
    project_name = "checkmate-453316"
    logger = initialise_cloud_logger(project_name)
    logger.log_text(f"Initialising Test Script For Passing In PUB/SUB MESSAGE into ENV variable")

    # Retrieving MESSAGE environement variable which came from pub/sub
    message = os.getenv("MESSAGE")
    #decoded_message = base64.b64decode(encoded_message).decode("utf-8")

    if encoded_message:
        statement = f"-----TESTING------ Recieved Pub/Sub Message: {message}"
        print(statement)
        logger.log_text(statement)

    else:
        statement = f"------TESTING------- No Message Inside Environment Variable"
        print(statement)
        logger.log_text(statement)

except Exception as e:
    error_message = f"Exception occurred: {str(e)}\n{traceback.format_exc()}"
    print(error_message)
    try:
        logger.log_text(error_message, severity="ERROR")
    except:
        pass  # If logger fails, don't crash again
