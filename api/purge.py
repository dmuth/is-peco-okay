"""Scheduled cleanup entry point for expired outage records."""

from .lib import db


def main() -> int:
    return db.purge_expired_records()


if __name__ == "__main__":
    print(f"Removed {main()} expired records.")
