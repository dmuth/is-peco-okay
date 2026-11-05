"""Helpers for calculating outage trends from PECO readings."""


def get_trend(current: dict, baseline: dict) -> dict[str, int | str]:
    """Return outage-count change and direction between two readings."""
    difference = int(current["customers_outages"]) - int(
        baseline["customers_outages"]
    )
    return {
        "num": difference,
        "direction": "up" if difference > 0 else "down",
    }
