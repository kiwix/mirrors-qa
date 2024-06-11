import argparse
import logging

from mirrors_qa_backend import db, logger
from mirrors_qa_backend.db import mirrors
from mirrors_qa_backend.extract import get_current_mirrors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output", action="store_true"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    with db.Session.begin() as session:
        mirrors.create_or_update_status(session, get_current_mirrors())


if __name__ == "__main__":
    main()
