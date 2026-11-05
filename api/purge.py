"""Scheduled cleanup entry point for expired outage records."""

import logging

from .lib import db


logger = logging.getLogger(__name__)


def main() -> int:
    removed = db.purge_expired_records()
    logger.info("Removed %d expired records.", removed)
    return removed


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    main()
