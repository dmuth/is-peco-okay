
#
# Module for interacting with DynamoDB.
#

from datetime import datetime, timedelta
from decimal import Decimal
import os

import boto3
from boto3.dynamodb.conditions import Key
import pytz



#
# Return an object for the DynamoDB Table
#
# key - Used to determine which table to return.
#
def get_table(key):

    if key == "main":
        table_name = os.environ["DYNAMO_TABLE_NAME"]
    elif key == "archive":
        table_name = os.environ["DYNAMO_TABLE_NAME_ARCHIVE"]
    else:
        raise Exception(f"Unknown key for DynamoDB table: {key}")

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    return(table)


#
# Get relevant dates all at once.
#
def get_dates():

    retval = {}

    now = datetime.now(pytz.utc)

    retval["date"] = now.strftime('%Y-%m-%d')
    retval["datetime"] = now.strftime('%Y-%m-%dT%H:%M:%S %Z')
    retval["hour"] = now.strftime('%Y%m%d%H')
    yesterday = now - timedelta(days=1)
    retval["yesterday"] = yesterday.strftime('%Y-%m-%d')
    retval["hour_yesterday"] = yesterday.strftime('%Y%m%d%H')

    return(retval)


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
        KeyConditionExpression = Key(key).eq(value),
        ConsistentRead = False,
        ScanIndexForward = False,
        Limit = limit
        )

    if "Items" in items:
        retval = items["Items"]
    #del items["Items"]; print("DEBUG Items", key, items) # Debugging
    #print("DEBUG Response size:", table, key, value, items["ResponseMetadata"]["HTTPHeaders"]["content-length"]) # Debugging

    return(retval)


#
# Fields come out of DyanmoDB in arbitrary order, and I would like to sort
# the humanized dic for easier consumption by humans.
#
def sort_humanized_dict(item):

    if item == "datetime":
        return(0, item)
    elif item == "customers":
        return(1, item)
    elif item == "customers_outages":
        return(2, item)
    elif item == "outages":
        return(3, item)
    elif item == "customers_active_percent":
        return(4, item)

    return(99, item)


#
# Get recent items.
# 
def get_items_recent(table, dates, limit = 1):

    data = {
        "Date": dates["date"],
        "DateTime": dates["datetime"],
        }

    retval = get_items(table, "Date", data["Date"], limit = limit)
    #retval = retval[:9] # Debugging - force an incomplete fetch for today

    #
    # If we didn't fetch enough items, we're probably at the start of the day.
    # Try fetching more items from yesterday.
    #
    if len(retval) < limit:
        new_limit = limit - len(retval)
        data["Date"] = dates["yesterday"]
        #print(f"DEBUG: Only fetched {len(retval)} items, fetching {new_limit} more from yesterday ({data['Date']})")
        retval += get_items(table, "Date", data["Date"], limit = new_limit)

    return(retval)


#
# Convert all decimal types in this dict to floats or integers.
#
# They needed to be stored in DynamoDB as Decimal types (or at least Boto required it),
# but we'd like them as floats or ints in Python for my own sanity.
#
def convert_decimals_to_ints(data):

    for key, value in data.items():

        if isinstance(value, Decimal):
            if value.as_tuple().exponent:
                data[key] = float(value)
            else:
                data[key] = int(value)

    return(data)


#
# Get an item from 24 hours ago.
#
def get_item_24hours_ago(table, date_yesterday, hour_yesterday):

    retval = []

    items = table.query(
        IndexName = "Hour",
        KeyConditionExpression = 
            Key("Date").eq(date_yesterday) & Key("Hour").eq(hour_yesterday),
        ConsistentRead = False,
        ScanIndexForward = False,
        Limit = 1
        )

    if "Items" in items:
        # If we have an old-style row, don't return anything.
        if len(items["Items"]):
            if "humanized" in items["Items"][0]:
                return(retval)
            retval = items["Items"][0]

    return(retval)

