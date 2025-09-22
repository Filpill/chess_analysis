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
message = os.getenv("MESSAGE")
print(f"THIS IS THE RAW MESSAGE DATA: {message}")

try:
    logger.log_text(f"---TEST START--- Initialising Test Script For Passing In PUB/SUB MESSAGE into ENV variable")

    # Test example input
    #message = "eyJlbmRfZGF0ZSI6IjIwMjUtMDMtMzEiLCJqb2JfbmFtZSI6InRlc3RfcHViX3N1Yl9tZXNzYWdlIiwic2NyaXB0X3NldHRpbmciOiJ0ZXN0Iiwic2V0dGluZzEiOiJBIiwic2V0dGluZzIiOiJCIiwic2V0dGluZzMiOiJDIiwic3RhcnRfZGF0ZSI6IjIwMjQtMDQtMDEifQ=="

    # Retrieving MESSAGE environement variable which came from pub/sub
    decoded_message = base64.b64decode(message).decode("utf-8")
    input_dict = json.loads(decoded_message)

    for i in range(5):
        time.sleep(1)
        if message:
            logger.log_text(f"| {i} | -----TESTING------ Raw Pub/Sub Message: {message} Recieved DataType: {type(message)}" )
            logger.log_text(f"| {i} | -----TESTING------ Decoded Pub/Sub Message: {decoded_message}" )
            logger.log_text(f"| {i} | -----TESTING------ Converted into python dictionary for script settings: {input_dict}" )
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
