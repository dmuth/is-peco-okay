

import json
from decimal import Decimal
import time

import lib.db as db
import lib.peco as peco


#
# Our entrypoint to the cron functionality.
#
def main(event, context):

    #
    # Grab our table client, dates, and stats.
    #
    table = db.get_table("main")
    dates = db.get_dates()
    stats, url = peco.get_stats()

    data = {}

    # The dates are our partition and sort keys
    data["Date"] = dates["date"]
    data["DateTime"] = dates["datetime"]
    # The hour is for our secondary Index
    data["Hour"] = dates["hour"]

    # Note the time that PECO puton the update
    data["PecoDateTime"] = stats["date"]

    data["customers"] = int(stats["total_customers"])
    data["customers_outages"] = int(stats["total_customers_outage"])
    data["outages"] = int(stats["total_outages"])
    #
    # Calculate our own percent, to three decimal places.
    #
    pct_outage = ( stats["total_customers_outage"] / stats["total_customers"] * 100 )
    pct_active = f"{ (100 - pct_outage):.3f}"
    data["customers_active_percent"] = pct_active

    #
    # Grab our most recent record, and if the time of the result from PECO matches, 
    # don't enter this since it would just be a duplicate.
    #
    recent = db.get_items_recent(table, dates, 1)
    
    if len(recent) > 0:
        row = recent[0]
        if "PecoDateTime" in row:
            if row["PecoDateTime"] == data["PecoDateTime"]:
                print(f"PecoDateTime of {row['PecoDateTime']} matches. This result is not new, stopping now.")
                return(None)

    #
    # Calculate our TTL for 7 days in the future.
    #
    ttl = 7 * 24 * 60 * 60 
    data["ttl"] = int(time.time() + ttl)

    #
    # Finally, write everything to the main DynamoDB table.
    #
    #print("DEBUG CRON", json.dumps(data, indent = 2)) # Debugging
    db.put_item(table, data)

    #
    # Before we wrap up, let's write the raw stats to our archive table.
    #
    table = db.get_table("archive")
    data = {}
    data["DateTime"] = dates["datetime"]
    data["url"] = url
    data["stats"] = stats

    #
    # DynamoDB doesn't like floating points, so we need to convert them to Decimals.
    # But we're casting them as string first, otherwise we'll wind up with insane
    # approximated values like 99.99000000001, etc.
    #
    for key, value in data["stats"].items():
        if isinstance(value, float):
            data["stats"][key] = Decimal(str(value))

    db.put_item(table, data)


