
import json

import requests

import lib.peco as peco
import lib.db as db
import lib.trends as trends
import lib.status as status


#
# Read the most recent record from DynamoDB
#
def get_status(event, context):

    table = db.get_table("main")
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = 1)

    #print("Debugging", json.dumps(items, indent = 4))
    #items[0] = False # Debugging
    #items[0] = {} # Debugging
    #items = False # Debugging

    if type(items) is list and len(items):

        if type(items[0]) is dict:
            stats = items[0]
            stats = db.convert_decimals_to_ints(stats)
            response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Item is not a dictonary."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}

    return(response)


#
# Parse our arguments (only argument supported at this time is num),
# do a sanity check, and return the value or raise an exception.
#
def parseArgsRecent(event):

    retval = 6

    if not "queryStringParameters" in event:
        return(retval)

    if not "num" in event["queryStringParameters"]:
        return(retval)

    num = int(event["queryStringParameters"]["num"])

    if num < 0 or num > 144:
        error_string = f"Acceptable values are between 1 and 144, inclusive. {num} is out of bounds."
        raise Exception(error_string)

    retval = num
    return(retval)


#
# Read the most recent statuses from DynamoDB.
# Default is 12 statuses (1 hour).
# This function will dedupe multiple reads for the same timespan.
#
def get_status_recent(event, context):

    try:
        num = parseArgsRecent(event)

    except Exception as e:
        response = {"statusCode": 422, "body": str(e)}
        return(response)

    table = db.get_table("main")
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = num)

    #print("Debugging", json.dumps(items, indent = 4), len(items))
    #print("Debugging", items, len(items))
    #items[0] = False # Debugging
    #items[0] = {} # Debugging
    #items = False # Debugging

    if type(items) is list and len(items):

        #
        # Check to see if the first result the old style of data.  If it is,
        # bail out, because we have nothing usable until cron runs.
        #
        if type(items[0]) is dict:
            if "raw" in items[0]:
                print(f"ERROR: First row has 'raw' key, which means it is in the old style and not usable.  Bailing out!")
                response = {"statusCode": 500, "body": "First result was in old format and is unusable. Wait for cron to run."}
                return(response)

        if type(items[0]) is dict:

            stats = _sanitize_rows(items)

            #
            # Sometimes we get an extra row, and we want to make sure that the number
            # of rows we return is exactly what we ask for.
            #
            stats = stats[:num]

            data = {}
            data["current"] = stats[0]
            data["recent"]= stats

            data["current"]["status"] = status.get_status("current", int(data["current"]["customers_outages"]))

            data["trends"] = _get_trends(table, dates, data)

            #print("Debugging", json.dumps(data, indent = 4))
            #print("Debug Trends", data["trends"])
            #
            # Dump in some debugging info here.
            #
            data["debug"] = {}
            data["debug"]["len"] = len(items)
            data["debug"]["start"] = data["recent"][0]["DateTime"]
            data["debug"]["end"] = data["recent"][-1]["DateTime"]
            #print(data["debug"], len(data["recent"])) # Debugging

            response = {"statusCode": 200, "body": json.dumps(data, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Item is not a dictonary."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}
        return(response)

    #print(f"Debug num: {num}, limit: {limit}, num items: {len(items)}, unique_rows: {len(stats)}")

    return(response)


#
# Get our trends.
#
def _get_trends(table, dates, data):

    retval = {}

    trend = trends.get_hourly_trend(data["recent"], 1)
    if trend:
        retval["1hour"] = trend
        retval["1hour"]["status"] = status.get_status("1hour", retval["1hour"]["num"])

    trend = trends.get_hourly_trend(data["recent"], 3)
    if trend:
        retval["3hour"] = trend
        retval["3hour"]["status"] = status.get_status("3hour", retval["3hour"]["num"])

    if len(data["recent"]) > 140:
        #
        # If we already have 24 hours (or close enough to it), just 
        # grab the very last item.
        #
        tmp = data["recent"][-1]
    else:
        #
        # If we don't have 24 hours worth of data, fetch that row explicitly.
        #
        tmp = db.get_item_24hours_ago(table, dates["yesterday"], dates["hour_yesterday"])

    if len(tmp):
        hours_ago_24 = db.convert_decimals_to_ints(tmp)

        retval["24hour"] = {}
        retval["24hour"]["num"] = (data["current"]["outages"] 
            - hours_ago_24["outages"])

        if retval["24hour"]["num"] > 0:
            retval["24hour"]["direction"] = "up"
        else:
            retval["24hour"]["direction"] = "down"

        retval["24hour"]["status"] = status.get_status("24hour", retval["24hour"]["num"])

    return(retval)


#
# Sanitize our rows, removing old style rows.
# 
def _sanitize_rows(items):

    retval = []

    for row in items:

        # If this is an old-style row, skip it.
        if "raw" in row:
            continue

        row = db.convert_decimals_to_ints(row)

        retval.append(row)

    #print("DEBUG", len(retval), retval)

    return(retval)


#
# Get the live status from PECO
#
def get_status_live(event, context):

    stats, _ = peco.get_stats()

    #print("DEBUG", stats) # Debugging
    response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

    return(response)


