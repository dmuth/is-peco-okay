import logging

from .lib import db, peco


logger = logging.getLogger(__name__)


#
# Our entrypoint to the cron functionality.
#
def main():

    #
    # Grab our table client, dates, and stats.
    #
    table = db.get_table("main")
    dates = db.get_dates()
    stats, url = peco.get_stats()

    data = {}

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
                logger.info(
                    "PecoDateTime of %s matches. This result is not new, stopping now.",
                    row["PecoDateTime"],
                )
                return(None)

    logger.info(f"Got result from PECO: {data}")

    #
    # Finally, write the latest status record.
    #
    db.put_item(table, data, dates["timestamp"])

    #
    # Before we wrap up, let's write the raw stats to our archive table.
    #
    table = db.get_table("archive")
    data = {}
    data["url"] = url
    data["stats"] = stats

    db.put_item(table, data, dates["timestamp"])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    main()
