import argparse
import logging
import sys

from mirrors_qa_manager import logger
from mirrors_qa_manager.__about__ import __version__
from mirrors_qa_manager.worker import WorkerManager


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("id", help="Worker ID")
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output.", action="store_true"
    )
    parser.add_argument("--version", help="Show version and exit.", action="store_true")

    args = parser.parse_args()

    if args.version:
        print(f"Mirrors QA Worker Manager: {__version__}")  # noqa: T201
        sys.exit(0)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    WorkerManager(worker_id=args.id).run()
