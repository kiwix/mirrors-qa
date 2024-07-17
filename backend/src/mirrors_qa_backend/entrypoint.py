import argparse
import logging
import sys

from humanfriendly import parse_timespan

from mirrors_qa_backend import logger
from mirrors_qa_backend.__about__ import __version__
from mirrors_qa_backend.cli.mirrors import update_mirrors
from mirrors_qa_backend.cli.scheduler import main as start_scheduler
from mirrors_qa_backend.cli.worker import create_worker, update_worker
from mirrors_qa_backend.settings.scheduler import SchedulerSettings

UPDATE_MIRRORS_CLI = "update-mirrors"
CREATE_WORKER_CLI = "create-worker"
UPDATE_WORKER_CLI = "update-worker"
SCHEDULER_CLI = "scheduler"


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
        "private_key_file",
        metavar="private-key-file",
        type=argparse.FileType("r", encoding="ascii"),
        nargs="?",
        default=sys.stdin,
        help="RSA private key file (default: stdin).",
    )

    subparsers.add_parser(
        UPDATE_WORKER_CLI, help="Update a worker", parents=[worker_parser]
    )

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.cli_name == UPDATE_MIRRORS_CLI:
        try:
            update_mirrors()
        except Exception as exc:
            logger.error(f"error while updating mirrors: {exc!s}")
            sys.exit(1)
    elif args.cli_name == SCHEDULER_CLI:
        start_scheduler(
            args.scheduler_sleep_seconds,
            args.expire_tests_since,
            args.workers_since,
        )
    elif args.cli_name == CREATE_WORKER_CLI:
        try:
            create_worker(
                args.worker_id,
                bytes(args.private_key_file.read(), encoding="ascii"),
                args.countries if args.countries else [],
            )
        except Exception as exc:
            logger.error(f"error while creating worker: {exc!s}")
            sys.exit(1)
    elif args.cli_name == UPDATE_WORKER_CLI:
        try:
            update_worker(
                args.worker_id,
                args.countries if args.countries else [],
            )
        except Exception as exc:
            logger.error(f"error while updating worker: {exc!s}")
            sys.exit(1)
    else:
        args.print_help()


if __name__ == "__main__":
    main()
