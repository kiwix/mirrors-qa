import argparse
import logging

from mirrors_qa_backend import Settings, db, logger
from mirrors_qa_backend.db import mirrors
from mirrors_qa_backend.extract import get_current_mirrors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-mirrors",
        action="store_true",
        help=f"Update the list of mirrors from {Settings.mirrors_url}",
    )
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output", action="store_true"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.update_mirrors:
        with db.Session.begin() as session:
            mirrors.update_mirrors(session, get_current_mirrors())


if __name__ == "__main__":
    main()
