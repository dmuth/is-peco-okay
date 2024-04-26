
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
            stats = db.convert_decimals_to_ints(stats)
            response = {"statusCode": 200, "body": json.dumps(stats, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Found latest result, but missing computed array."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}

    return(response)


#
# Parse our arguments (only argument supported at this time is num),
# do a sanity check, and return the value or raise an exception.
#
# Note that the number we return is twice what's passed in, since we're taking
# readings from the API every 5 minutes.
#
def parseArgsRecent(event):

    retval = 6

    if not "queryStringParameters" in event:
        return(retval)

    if not "num" in event["queryStringParameters"]:
        return(retval)

    num = int(event["queryStringParameters"]["num"])

    error_string = f"Acceptable values are between 1 and 20, inclusive. {num} is out of bounds."
    if num < 0 or num > 20:
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
        #
        # Since cron gets statuses every 5 minutes, and the data is in 10 minute
        # intervals, let's duplicate our number.  We'll dedup results later.
        #
        limit = num * 2

    except Exception as e:
        response = {"statusCode": 422, "body": str(e)}
        return(response)

    table = db.get_table()
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = limit)

    #print("Debugging", json.dumps(items, indent = 4))
    #print("Debugging", json.dumps(items[0]["humanized"], indent = 4))
    #items[0] = False # Debugging
    #items[0] = {} # Debugging
    #items = False # Debugging

    if type(items) is list and len(items):

        if type(items[0]) is dict and "humanized" in items[0]:

            stats = _get_unique_rows(items)
            #
            # Sometimes we get an extra row, and we want to make sure that the number
            # of rows we return is exactly what we ask for.
            #
            stats = stats[:num]

            for key, row in enumerate(stats):
                stats[key] = db.convert_decimals_to_ints(row)

            data = {}
            data["current"] = stats[0]
            data["recent"]= stats
            data["trends"] = {}

            data["current"]["status"] = status.get_status("current", int(data["current"]["customers_outages"]))

            trend = trends.get_hourly_trend(stats, 1)
            if trend:
                data["trends"]["1hour"] = trend
                data["trends"]["1hour"]["status"] = status.get_status("1hour", data["trends"]["1hour"]["num"])

            trend = trends.get_hourly_trend(stats, 3)
            if trend:
                data["trends"]["3hour"] = trend
                data["trends"]["3hour"]["status"] = status.get_status("3hour", data["trends"]["3hour"]["num"])

            #print("Debug Trends", data["trends"])

            response = {"statusCode": 200, "body": json.dumps(data, indent = 4)}

        else:
            print(f"ERROR: Bad item: {items[0]}")
            response = {"statusCode": 500, "body": "Found latest result, but missing computed array."}

    else:
        print(f"ERROR: Bad repsonse: {items}")
        response = {"statusCode": 500, "body": "Did not find any results from our database query."}

    #print(f"Debug num: {num}, limit: {limit}, num items: {len(items)}, unique_rows: {len(stats)}")

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


    #print("DEBUG", stats[0])
    #print("DEBUG", stats)
    #print("DEBUG LEN", len(stats))
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


