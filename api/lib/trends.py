            
#
# Module for calculating trends across data.
#

from datetime import datetime


#
# Get our hourly trend across stats for a certain number of hours.
#
def get_hourly_trend(stats, num_hours):

    retval = {}

    #
    # Get our start time and calulate the target time.
    # We want to get the reading from just before that target time.
    #
    start = datetime.fromisoformat(stats[0]["PecoDateTime"].replace('Z', '+00:00')).timestamp()
    #end = datetime.fromisoformat(stats[-1]["PecoDateTime"].replace('Z', '+00:00')).timestamp() # Debugging
    #print(f"Debug num_hours: {num_hours}, start: {stats[0]['PecoDateTime']}, end: {stats[-1]['PecoDateTime']}, diff: {(start - end)}")
    target = start - (num_hours * 3600)

    customers_outages_end = int(stats[0]["customers_outages"])

    #
    # Loop through our row, and when the time_t difference exceeds the number of hours,
    # grab that difference.
    #
    for row in stats:
        time_t = datetime.fromisoformat(row["PecoDateTime"].replace('Z', '+00:00')).timestamp()

        if time_t <= target:
            #print(f"DEBUG Target found: {row['PecoDateTime']}") # Debugging
            customers_outages_start = int(row["customers_outages"])
            retval["num"] = customers_outages_end - customers_outages_start
            break

    else:
        return(retval)

    #
    # Calculate direction of the difference for trending purposes.
    #
    retval["direction"] = ""
    if retval["num"] > 0:
        retval["direction"] = "up"
    else:
        retval["direction"] = "down"

    return(retval)

