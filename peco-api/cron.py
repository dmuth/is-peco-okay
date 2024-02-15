

from datetime import datetime

import lib

#
# Our entrypoint to the cron functionality.
#
def main(event, context):
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %H:%M:%S")

    stats = None
    #stats = lib.get_peco_stats()
    print("TEST", now_str, stats)


