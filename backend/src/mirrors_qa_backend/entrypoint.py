import argparse
import logging
import sys

from mirrors_qa_backend import logger
from mirrors_qa_backend.cli.mirrors import update_mirrors
from mirrors_qa_backend.cli.scheduler import main as start_scheduler
from mirrors_qa_backend.cli.worker import create_worker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output", action="store_true"
    )
    subparsers = parser.add_subparsers(required=True)
    # Sub-command for updating mirrors
    update_mirrors_cmd = subparsers.add_parser(
        "update-mirrors", help="Update the list of mirrors"
    )
    # Register the function to handle the sub-command
    update_mirrors_cmd.set_defaults(func=update_mirrors)

    # Sub-command for starting the scheduler
    scheduler_cmd = subparsers.add_parser(
        "scheduler",
        help="Start the scheduler",
    )
    # Register the function to handle the sub-command
    scheduler_cmd.set_defaults(func=start_scheduler)

    # Sub-command for creating a worker
    create_worker_cmd = subparsers.add_parser(
        "create-worker", help="Create a new worker"
    )
    create_worker_cmd.add_argument(
        "worker_id", help="ID of the worker", metavar="worker-id"
    )
    create_worker_cmd.add_argument(
        "--countries",
        help="Comma-seperated country codes each in ISO 3166-1 alpha-2 format",
        type=lambda s: s.split(","),
    )
    create_worker_cmd.add_argument(
        "private_key_file",
        metavar="private-key-file",
        type=argparse.FileType("r", encoding="ascii"),
        nargs="?",
        default=sys.stdin,
        help="RSA private key file (default: stdin)",
    )
    # Register the function to handle the sub-command
    create_worker_cmd.set_defaults(func=create_worker)

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    args.func(args)


if __name__ == "__main__":
    main()
