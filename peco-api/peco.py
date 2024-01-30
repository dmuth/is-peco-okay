
import json

import requests

import lib


#
# Get the current outage status from PECO.
#
def get_peco_status(event, context):

    stats, _ = lib.get_peco_stats()

    response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

    return(response)


