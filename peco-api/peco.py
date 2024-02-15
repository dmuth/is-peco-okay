
import json

import requests

import lib


def hello(event, context):
    body = {
        "test": "test2",
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


#
# Get the current outage status from PECO.
#
def get_peco_status(event, context):

    stats = lib.get_peco_stats()

    response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

    return(response)


