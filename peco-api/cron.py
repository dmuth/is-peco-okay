

import json

import lib


#
# Our entrypoint to the cron functionality.
#
def main(event, context):

    #
    # Grab our table client, dates, and stats.
    #
    table = lib.get_dynamodb_table()
    dates = lib.get_dates()
    stats, url = lib.get_peco_stats()

    data = {}

    # The dates are our partition and sort keys
    data["Date"] = dates["date"]
    data["DateTime"] = dates["datetime"]

    # Save the raw data and URL that we got from PECO.
    data["raw"] = {
        "url": url,
        "payload": json.dumps(stats),
        }

    #
    # (re-)calculate percents, then save humanized data to a new dictionary.
    #
    pct_outage = ( stats["total_customers_outage"] / stats["total_customers"] * 100 )
    pct_active = f"{ (100 - pct_outage):.2f}"

    data["humanized"] = {
        "datetime": stats["date"],
        "customers": str(stats["total_customers"]),
        "customers_active_percent": pct_active,
        "customers_outages": str(stats["total_customers_outage"]),
        "outages": str(stats["total_outages"]),
        }
 
    #
    # Finally, write everything to DynamoDB
    #
    #print("DEBUG", json.dumps(data, indent = 2)) # Debugging
    lib.put_item(table, data)



