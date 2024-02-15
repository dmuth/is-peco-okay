
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


#
# Get the current outage status from PECO.
#
def get_peco_status(event, context):

    #
    # Grab the "interval_generation_data" field, which contains a URL fragment.
    # This changes about every 10 minutes, as it looks like the final URL is a 
    # static JSON file being served from S3.
    #
    url_1="https://kubra.io/stormcenter/api/v1/stormcenters/39e6d9f3-fdea-4539-848f-b8631945da6f/views/789577bd-d2c6-42b8-af4b-b51ae6f52b6c/currentState"
    result = requests.get(url_1)
    #print(json.dumps(result.json(), indent = 4)) # Debugging

    url_fragment = result.json()["data"]["interval_generation_data"]
    url_2=f"https://kubra.io/{url_fragment}/public/summary-1/data.json"
    #print(url_2) # Debugging
    result = requests.get(url_2)

    results = {}
    results["date"] = result.json()["summaryFileData"]["date_generated"]
    results["total_customers"] = results["total_customers"] = (
        result.json()["summaryFileData"]["totals"][0]["total_cust_s"])
    results["total_customers_active_percent"] = (
        result.json()["summaryFileData"]["totals"][0]["total_percent_cust_active"]["val"])
    results["total_customers_outage"] = (
        result.json()["summaryFileData"]["totals"][0]["total_cust_a"]["val"])
    results["total_customers_outage_percent"] = (
        result.json()["summaryFileData"]["totals"][0]["total_percent_cust_a"]["val"])
    results["total_outages"] = (
        result.json()["summaryFileData"]["totals"][0]["total_outages"])
    #print(f"{json.dumps(results, indent = 4)}") # Debugging

    response = {"statusCode": 200, "body": json.dumps(results, indent = 4)}

    return(response)


