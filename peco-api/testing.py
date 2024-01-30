
import json
import os

import requests
import boto3

import lib


#
# Read an item
#
def get_item(table, artist, song):

    retval = {}

    item = table.get_item(
        Key = {
            "Artists": artist,
            "SongTitle": song,
        },
        ConsistentRead = True,
        )

    if "Item" in item:
        retval = item["Item"]

    return(retval)


def main(event, context):

    body = {
        "test": "test2",
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    table = lib.get_dynamodb_table()
    dates = lib.get_dates()

    data = {
        "Date": dates["date"],
        "DateTime": dates["datetime"],
        }

    items = lib.get_items(table, "Date", data["Date"], limit = 6)
    #print(items)
    print(f"NUM ITEMS: {len(items)}")
    print(items[0])
    print(items[0]["humanized"])
    #print(json.dumps(items[0]["humanized"], indent = 2))

    #if items:
    #    print("ITEM FOUND - Incrementing SongTitle...")
    #    item = items[0]
    #    songtitle = int(item["SongTitle"])
    #    songtitle += 1
    #    print(f"New song title: {songtitle}")
    #
    #    data["SongTitle"] = str(songtitle)
    #
    #response = put_item(table, data)


    #item = get_item(table, data["Artists"], data["SongTitle"])
    #if item:
    #    print(f"HIT: {item}")
    #else:
    #    print("MISS: Did not find item!  Let's insert it...")
    #    response = put_item(table, data)
    #    item = get_item(table, data["Artists"], data["SongTitle"])
    #    print(f"HIT: {item}")


    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


