
#
# This module does status lookups.
#


#
# Check the either the number of outages (for a current reading) 
# or a change in outages (for a trend period), do a lookup, and 
# return the string "green", "yellow", or "red".
#

def get_status(key, num):

    #
    # This is our "default" value, which will keep the text grey.
    # We use this for trending values, where a small decrease isn't
    # necessary worth turning yellow over.
    #
    retval = ""

    if key == "current":
        if num < 10000:
            retval = "green"
        elif num < 50000:
            retval = "yellow"
        else:
            retval = "red"

    elif key == "1hour":
        if num <= 0:
            retval = "green"
        elif num >= 100 and num < 10000:
            #
            # If the nnumber went down by less than 100, we don't care all that much.
            #
            retval = "yellow"
        elif num >= 10000:
            retval = "red"
        
    elif key == "3hour":
        if num <= 0:
            retval = "green"
        elif num >= 300 and num < 30000:
            #
            # If the nnumber went down by less than 300, we don't care all that much.
            #
            retval = "yellow"
        elif num <= -30000:
            retval = "red"
        
    else:
        raise Exception(f"Unknown key: {key}")   

    return(retval)


