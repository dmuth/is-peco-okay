

import json
from decimal import Decimal

import lib.db as db
import lib.peco as peco


#
# Our entrypoint to the cron functionality.
#
def main(event, context):

    #
    # Grab our table client, dates, and stats.
    #
    table = db.get_table()
    dates = db.get_dates()
    stats, url = peco.get_stats()

    data = {}

    # The dates are our partition and sort keys
    data["Date"] = dates["date"]
    data["DateTime"] = dates["datetime"]
    # The hour is for our secondary Index
    data["Hour"] = int(dates["hour"])

    # Save the raw data and URL that we got from PECO.
    data["raw"] = {
        "url": url,
        "payload": json.dumps(stats),
        }

    #
    # (re-)calculate percents, then save humanized data to a new dictionary.
    #
    pct_outage = ( stats["total_customers_outage"] / stats["total_customers"] * 100 )
    pct_active = f"{ (100 - pct_outage):.3f}"

    data["humanized"] = {
        "datetime": stats["date"],
        "customers": int(stats["total_customers"]),
        "customers_outages": int(stats["total_customers_outage"]),
        "outages": int(stats["total_outages"]),
        "customers_active_percent": Decimal(pct_active),
        }

    #
    # Finally, write everything to DynamoDB
    #
    #print("DEBUG", json.dumps(data, indent = 2)) # Debugging
    db.put_item(table, data)



