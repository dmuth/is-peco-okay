
import json

import requests

import lib.peco as peco
import lib.db as db


#
# Read the most recent record from DynamoDB
#
def get_status(event, context):

    table = db.get_table()
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = 1)

    #print("Debugging", json.dumps(items, indent = 4))
    #print("Debugging", json.dumps(items[0]["humanized"], indent = 4))
    #items[0] = False # Debugging
    #items[0] = {} # Debugging
    #items = False # Debugging

    if type(items) is list and len(items):

        if type(items[0]) is dict and "humanized" in items[0]:
            stats = items[0]["humanized"]
            response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Found latest result, but missing computed array."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}

    return(response)


#
# Read the most recent statuses from DynamoDB.
# Default is 12 statuses (1 hour).
# This function will dedupe multiple reads for the same timespan.
#
def get_status_recent(event, context):

    table = db.get_table()
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = 12)

    #print("Debugging", json.dumps(items, indent = 4))
    #print("Debugging", json.dumps(items[0]["humanized"], indent = 4))
    #items[0] = False # Debugging
    #items[0] = {} # Debugging
    #items = False # Debugging

    if type(items) is list and len(items):

        if type(items[0]) is dict and "humanized" in items[0]:
            stats = _get_unique_rows(items)
            response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Found latest result, but missing computed array."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}

    return(response)


#
# Take a list of stats and dedup readings during the same time.
# PECO updates its status every 10 minutes, and the crontab reads once
# every 5 minutes, just in case a single read fails.
#
def _get_unique_rows(items):

    stats = []
    last = ""

    for row in items:

        if row["humanized"]["datetime"] == last:
            continue

        stats.append(row["humanized"])

        last = row["humanized"]["datetime"]


    # TEST
    #print("TEST", stats[0])
    #print("TEST", stats)
    #print("TEST LEN", len(stats))
    #stats = []

    return(stats)


#
# Get the live status from PECO
#
def get_status_live(event, context):

    stats, _ = peco.get_stats()

    #print("DEBUG", stats) # Debugging
    response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

    return(response)


