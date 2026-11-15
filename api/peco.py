
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from .lib import db, status, trends


router = APIRouter()


@router.get("/peco", response_model=None)
def get_status() -> dict | PlainTextResponse:
    """Return the most recent saved status record."""

    table = db.get_table("main")
    item = db.get_latest_item(table)
    if item is None:
        return PlainTextResponse(
            "Did not find any results from our database query.",
            status_code=500,
        )
    return db.convert_decimals_to_ints(item)


def parse_args_recent(seconds: str | None) -> int:
    """Parse the requested history window, capped at the database retention period."""

    if seconds is None:
        return 3600
    duration_seconds = int(seconds)

    if duration_seconds < 1 or duration_seconds > 604800:
        error_string = f"Acceptable values are between 1 and 604800 seconds, inclusive. {duration_seconds} is out of bounds."
        raise ValueError(error_string)

    return duration_seconds


@router.get("/peco/recent", response_model=None)
def get_status_recent(
    seconds: str | None = None,
    num: str | None = None,
) -> dict | PlainTextResponse:
    """Return recent statuses and their calculated trends."""

    if num is not None:
        return PlainTextResponse(
            "The num parameter has been replaced by seconds.",
            status_code=422,
        )

    try:
        duration_seconds = parse_args_recent(seconds)

    except ValueError as e:
        return PlainTextResponse(str(e), status_code=422)

    table = db.get_table("main")
    dates = db.get_dates()
    items = db.get_items_for_duration(
        table,
        int(dates["timestamp_us"]),
        duration_seconds,
    )

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

            data = {}
            data["current"] = stats[0]
            data["recent"] = stats

            data["current"]["status"] = status.get_status("current", int(data["current"]["customers_outages"]))

            data["trends"] = _get_trends(table, data)

            data["debug"] = {}
            data["debug"]["len"] = len(items)
            data["debug"]["start"] = data["recent"][0]["timestamp"]
            data["debug"]["end"] = data["recent"][-1]["timestamp"]
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


def _get_trends(table, data):

    retval = {}
    current = data["current"]
    current_timestamp = db.parse_timestamp_microseconds(current["PecoDateTime"])
    trend_periods = (
        ("1hour", 1, 600),
        ("3hour", 3, 1200),
        ("24hour", 24, 600),
    )

    for key, hours, tolerance_seconds in trend_periods:
        target_timestamp = current_timestamp - hours * 3600 * 1_000_000
        baseline = db.get_item_near_reading_time(
            table,
            target_timestamp,
            tolerance_seconds,
        )
        if baseline is None:
            continue

        trend = trends.get_trend(current, baseline)
        trend["status"] = status.get_status(key, trend["num"])
        retval[key] = trend

    return retval


def _sanitize_rows(items):

    retval = []

    for row in items:

        # If this is an old-style row, skip it.
        if "raw" in row:
            continue

        row = db.convert_decimals_to_ints(row)

        retval.append(row)

    return(retval)
