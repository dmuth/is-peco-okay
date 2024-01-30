
from datetime import datetime, timedelta
import os

import boto3
import requests


#
# Return an object for the DynamoDB Table
#
def get_dynamodb_table():

    env = os.environ["STAGE"]
    table_name = f"peco-outages-{env}"

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    return(table)


#
# Get relevant dates all at once.
#
def get_dates():

    retval = {}

    retval["date"] = datetime.now().strftime('%Y-%m-%d')
    retval["datetime"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    yesterday = datetime.now() - timedelta(days=1)
    retval["yesterday"] = yesterday.strftime('%Y-%m-%d')

    return(retval)



#
# Download stats from PECO's API.
#
def get_peco_stats():

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

    response = results

    return(response, url_2)


#
# Put an item in the DynamoDB table
#
def put_item(table, data):
    retval = table.put_item(Item = data)
    return(retval)


#
# Retrieve all items that match the supplied key.
# Items will be returned in reverse order.
#
def get_items(table, key, value, limit = 100):

    retval = {}

    items = table.query(
        KeyConditionExpression = boto3.dynamodb.conditions.Key(key).eq(value),
        ScanIndexForward = False,
        Limit = limit
        )

    if "Items" in items:
        retval = items["Items"]

    return(retval)


