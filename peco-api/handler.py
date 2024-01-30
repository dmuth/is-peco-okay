
import json

import requests

def hello(event, context):
    body = {
        "test": "test2",
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

def get_peco_status(event, context):

    data = requests.get("https://httpbin.dmuth.org/uuid")

    response = {"statusCode": 200, "body": data.json()["uuid"]}

    return(response)


