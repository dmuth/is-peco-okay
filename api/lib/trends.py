            
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

    #
    # Add in a buffer to our target time.  This is because readings from PECO are roughly
    # (but not exactly) every 10 minutes, and with a cron schedule of once per minute, we could
    # be in a situation where we want the reading from 3h ago, but it is like, 3hm2 ago, or
    # even 3m5s ago.
    #
    # The tradeoff here is that we might get a reading from 50m or 2h50m ago, but I feel being
    # one datapiont away is better than having a trend show up as "unavailable" in the UI 
    # while the data is there.
    #
    if num_hours == 1:
        target = target + (600 * 1)
    elif num_hours == 3:
        target = target + (600 * 2)

    customers_outages_end = int(stats[0]["customers_outages"])

    #
    # Loop through our row, and when the time_t difference exceeds the number of hours,
    # grab that difference.
    #
    for row in stats:
        time_t = datetime.fromisoformat(row["PecoDateTime"].replace('Z', '+00:00')).timestamp()

        #print(f"DEBUG: {target}, {time_t}, {time_t - target}") # Debugging
        if time_t <= target:
            #print(f"DEBUG Target found: {row['PecoDateTime']}, diff: {start - time_t}") # Debugging
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

