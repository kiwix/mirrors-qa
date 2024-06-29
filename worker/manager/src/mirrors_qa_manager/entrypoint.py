import argparse
import logging

from mirrors_qa_manager import logger
from mirrors_qa_manager.__about__ import __version__
from mirrors_qa_manager.worker import WorkerManager


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("id", help="Worker ID")
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output.", action="store_true"
    )
    parser.add_argument(
        "--version",
        help="Show version and exit.",
        action="version",
        version="%(prog)s " + __version__,
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    WorkerManager(worker_id=args.id).run()
