import os
import sys
import time
import json
import base64
import logging
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
    logger.log_text(f"---TEST START--- Initialising Test Script For Passing In PUB/SUB MESSAGE into ENV variable")

    # Retrieving MESSAGE environement variable which came from pub/sub
    message = os.getenv("MESSAGE")
    #message = "{job_name : test_pub_sub_message}"
    #decoded_message = base64.b64decode(message).decode("utf-8")

    for i in range(5):
        time.sleep(1)
        if message:
            logger.log_text(f"{i}-----TESTING------ Recieved Pub/Sub Message: {message}" )
            logger.log_text(f"{i}-----TESTING------ Recieved Pub/Sub Message Type: {type(message)}" )
        else:
            logger.log_text(f"{i}------TESTING------- No Message Inside Environment Variable", severity="ERROR")

except Exception as e:
        error_message = f"-----------TESTING EXCEPTION------- Exception occurred: {str(e)}\n{traceback.format_exc()}"
        try:
            logger.log_text(error_message, severity="ERROR")
        except:
            pass  # If logger fails, don't crash again

time.sleep(2)
for handler in logging.getLogger().handlers:
    if hasattr(handler, "flush"):
        handler.flush()
time.sleep(2)
