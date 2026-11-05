
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from .lib import db, peco, status, trends


router = APIRouter()


@router.get("/peco", response_model=None)
def get_status() -> dict | PlainTextResponse:
    """Return the most recent saved status record."""

    table = db.get_table("main")
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = 1)

    if type(items) is list and len(items):

        if type(items[0]) is dict:
            stats = items[0]
            return db.convert_decimals_to_ints(stats)

        else:
            print(f"ERROR: Bad item: {items[0]}")
            return PlainTextResponse("Item is not a dictonary.", status_code=500)

    else:
        print(f"ERROR: Bad repsonse: {items}")
        return PlainTextResponse(
            "Did not find any results from our database query.",
            status_code=500,
        )


def parse_args_recent(num: str | None) -> int:
    """Parse the optional recent-record count, preserving the existing limits."""

    if num is None:
        return 6
    num = int(num)

    if num < 0 or num > 144:
        error_string = f"Acceptable values are between 1 and 144, inclusive. {num} is out of bounds."
        raise ValueError(error_string)

    return num


@router.get("/peco/recent", response_model=None)
def get_status_recent(num: str | None = None) -> dict | PlainTextResponse:
    """Return recent statuses and their calculated trends."""

    try:
        num = parse_args_recent(num)

    except ValueError as e:
        return PlainTextResponse(str(e), status_code=422)

    table = db.get_table("main")
    dates = db.get_dates()

    items = db.get_items_recent(table, dates, limit = num)

    if type(items) is list and len(items):

        if type(items[0]) is dict:
            if "raw" in items[0]:
                print(f"ERROR: First row has 'raw' key, which means it is in the old style and not usable.  Bailing out!")
                return PlainTextResponse(
                    "First result was in old format and is unusable. Wait for cron to run.",
                    status_code=500,
                )

        if type(items[0]) is dict:

            stats = _sanitize_rows(items)

            #
            # Sometimes we get an extra row, and we want to make sure that the number
            # of rows we return is exactly what we ask for.
            #
            stats = stats[:num]

            data = {}
            data["current"] = stats[0]
            data["recent"] = stats

            data["current"]["status"] = status.get_status("current", int(data["current"]["customers_outages"]))

            data["trends"] = _get_trends(table, dates, data)

            data["debug"] = {}
            data["debug"]["len"] = len(items)
            data["debug"]["start"] = data["recent"][0]["DateTime"]
            data["debug"]["end"] = data["recent"][-1]["DateTime"]
            return data

        else:
            print(f"ERROR: Bad item: {items[0]}")
            return PlainTextResponse("Item is not a dictonary.", status_code=500)

    else:
        print(f"ERROR: Bad repsonse: {items}")
        return PlainTextResponse(
            "Did not find any results from our database query.",
            status_code=500,
        )


def _get_trends(table, dates, data):

    retval = {}

    trend = trends.get_hourly_trend(data["recent"], 1)
    if trend:
        retval["1hour"] = trend
        retval["1hour"]["status"] = status.get_status("1hour", retval["1hour"]["num"])

    trend = trends.get_hourly_trend(data["recent"], 3)
    if trend:
        retval["3hour"] = trend
        retval["3hour"]["status"] = status.get_status("3hour", retval["3hour"]["num"])

    if len(data["recent"]) > 140:
        #
        # If we already have 24 hours (or close enough to it), just 
        # grab the very last item.
        #
        tmp = data["recent"][-1]
    else:
        #
        # If we don't have 24 hours worth of data, fetch that row explicitly.
        #
        tmp = db.get_item_24hours_ago(table, dates["yesterday"], dates["hour_yesterday"])

    if len(tmp):
        hours_ago_24 = db.convert_decimals_to_ints(tmp)

        retval["24hour"] = {}
        retval["24hour"]["num"] = (data["current"]["customers_outages"] 
            - hours_ago_24["customers_outages"])

        if retval["24hour"]["num"] > 0:
            retval["24hour"]["direction"] = "up"
        else:
            retval["24hour"]["direction"] = "down"

        retval["24hour"]["status"] = status.get_status("24hour", retval["24hour"]["num"])

    return(retval)


def _sanitize_rows(items):

    retval = []

    for row in items:

        # If this is an old-style row, skip it.
        if "raw" in row:
            continue

        row = db.convert_decimals_to_ints(row)

        retval.append(row)

    return(retval)
