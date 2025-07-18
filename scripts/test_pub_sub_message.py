import os
import sys
import time
import json
import base64
import traceback
import google.cloud.logging as cloud_logging
from google.cloud import storage

sys.path.append(f"./functions")
sys.path.append(f"../functions")
from shared_func import initialise_cloud_logger

# Initialise Logger
project_name = "checkmate-453316"
logger = initialise_cloud_logger(project_name)

try:
    logger.log_text(f"Initialising Test Script For Passing In PUB/SUB MESSAGE into ENV variable")

    # Retrieving MESSAGE environement variable which came from pub/sub
    #message = "{job_name : test_pub_sub_message}"
    message = os.getenv("MESSAGE")
    #decoded_message = base64.b64decode(message).decode("utf-8")

    if message:
        logger.log_text(f"-----TESTING------ Recieved Pub/Sub Message: {message}" )
        logger.log_text(f"-----TESTING------ Recieved Pub/Sub Message Type: {type(message)}" )
    else:
        logger.log_text(f"------TESTING------- No Message Inside Environment Variable" )

except Exception as e:
    error_message = f"-----------TESTING EXCEPTION------- Exception occurred: {str(e)}\n{traceback.format_exc()}"
    try:
        logger.log_text(error_message, severity="ERROR")
    except:
        pass  # If logger fails, don't crash again

logging.shutdown()
time.sleep(2)
