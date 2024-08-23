import argparse
import logging
import sys

from humanfriendly import parse_timespan

from mirrors_qa_backend import logger
from mirrors_qa_backend.__about__ import __version__
from mirrors_qa_backend.cli.country import (
    create_regions_and_countries,
    extract_country_regions_from_csv,
)
from mirrors_qa_backend.cli.mirrors import update_mirrors
from mirrors_qa_backend.cli.scheduler import main as start_scheduler
from mirrors_qa_backend.cli.worker import create_worker, update_worker
from mirrors_qa_backend.settings.scheduler import SchedulerSettings

UPDATE_MIRRORS_CLI = "update-mirrors"
CREATE_WORKER_CLI = "create-worker"
UPDATE_WORKER_CLI = "update-worker"
SCHEDULER_CLI = "scheduler"
CREATE_COUNTRY_REGIONS_CLI = "create-countries"


def main():
    # The program is split into a number of sub-commands with each sub-command
    # performing different function and requring different different kinds of
    # command line arguments
    parser = argparse.ArgumentParser()
    # Define the command-line arguments that are used by all the sub-commands
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output.", action="store_true"
    )
    parser.add_argument(
        "--version",
        help="Show version and exit.",
        action="version",
        version="%(prog)s: " + __version__,
    )

    subparsers = parser.add_subparsers(required=True, dest="cli_name")

    subparsers.add_parser(UPDATE_MIRRORS_CLI, help="Update the list of mirrors")

    scheduler_cli = subparsers.add_parser(
        SCHEDULER_CLI,
        help="Start the scheduler.",
    )
    scheduler_cli.add_argument(
        "--sleep",
        help="Duration to sleep after creating tests",
        type=parse_timespan,
        dest="scheduler_sleep_seconds",
        default=SchedulerSettings.SLEEP_SECONDS,
        metavar="duration",
    )
    scheduler_cli.add_argument(
        "--workers-since",
        help="Create tests for workers last seen in duration.",
        type=parse_timespan,
        dest="workers_since",
        default=SchedulerSettings.IDLE_WORKER_SECONDS,
        metavar="duration",
    )
    scheduler_cli.add_argument(
        "--expire-tests-since",
        help="Expire tests whose results have not arrived since duration",
        type=parse_timespan,
        dest="expire_tests_since",
        default=SchedulerSettings.EXPIRE_TEST_SECONDS,
        metavar="duration",
    )

    # Parser for holding shared arguments for worker sub-commands
    worker_parser = argparse.ArgumentParser(add_help=False)
    worker_parser.add_argument(
        "worker_id", help="ID of the worker.", metavar="worker-id"
    )
    worker_parser.add_argument(
        "--countries",
        help="Comma-seperated country codes each in ISO 3166-1 alpha-2 format.",
        type=lambda countries: countries.split(","),
        dest="countries",
        metavar="codes",
    )

    create_worker_cli = subparsers.add_parser(
        CREATE_WORKER_CLI, help="Create a new worker.", parents=[worker_parser]
    )
    create_worker_cli.add_argument(
        "public_key_file",
        metavar="public-key-file",
        type=argparse.FileType("r", encoding="ascii"),
        nargs="?",
        default=sys.stdin,
        help="RSA public key file (default: stdin).",
    )

    subparsers.add_parser(
        UPDATE_WORKER_CLI, help="Update a worker", parents=[worker_parser]
    )

    create_country_regions_cli = subparsers.add_parser(
        CREATE_COUNTRY_REGIONS_CLI, help="Create countries and associated regions."
    )
    create_country_regions_cli.add_argument(
        "country_region_csv_file",
        metavar="csv-file",
        type=argparse.FileType("r", encoding="utf-8"),
        nargs="?",
        default=sys.stdin,
        help=(
            "CSV file containing countries and associated regions "
            "(format: Maxmind's GeoIPLite Country Locations csv) (default: stdin)."
        ),
    )

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.cli_name == UPDATE_MIRRORS_CLI:
        try:
            logger.debug("Updating list of mirrors...")
            update_mirrors()
        except Exception as exc:
            logger.error(f"error while updating mirrors: {exc!s}")
            sys.exit(1)
        logger.info("Updated list of mirrors on database.")
    elif args.cli_name == SCHEDULER_CLI:
        logger.debug("Starting scheduler task...")
        start_scheduler(
            args.scheduler_sleep_seconds,
            args.expire_tests_since,
            args.workers_since,
        )
    elif args.cli_name == CREATE_WORKER_CLI:
        try:
            logger.debug(f"Creating worker {args.worker_id!r}...")
            create_worker(
                args.worker_id,
                bytes(args.public_key_file.read(), encoding="ascii"),
                args.countries if args.countries else [],
            )
        except Exception as exc:
            logger.error(f"error while creating worker: {exc!s}")
            sys.exit(1)
        logger.info(f"Saved worker {args.worker_id!r} to database.")
    elif args.cli_name == UPDATE_WORKER_CLI:
        try:
            logger.debug(f"Updating list of mirrors for {args.worker_id!r}")
            update_worker(
                args.worker_id,
                args.countries if args.countries else [],
            )
        except Exception as exc:
            logger.error(f"error while updating worker: {exc!s}")
            sys.exit(1)
        logger.info(f"Updated countries for worker {args.worker_id!r}")
    elif args.cli_name == CREATE_COUNTRY_REGIONS_CLI:
        try:
            logger.debug("Creating regions and associated countries.")

            create_regions_and_countries(
                extract_country_regions_from_csv(
                    args.country_region_csv_file.readlines()
                )
            )
        except Exception as exc:
            logger.error(f"error while creating regions: {exc!s}")
            sys.exit(1)
        logger.info("Created regions and associated countries.")
    else:
        args.print_help()


if __name__ == "__main__":
    main()
