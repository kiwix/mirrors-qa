import argparse
import json
import logging
from dataclasses import asdict

from mirrors_qa_task import logger
from mirrors_qa_task.__about__ import __version__
from mirrors_qa_task.settings import Settings
from mirrors_qa_task.worker import get_download_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", "-O", help="Name of file to write results", default="output.json"
    )
    parser.add_argument(
        "-v", "--verbose", help="Show verbose output", action="store_true"
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

    metrics = asdict(get_download_metrics(Settings.TEST_FILE_URL))
    (Settings.WORKDIR / args.output).write_text(json.dumps(metrics))

    logger.info(f"Saved data to {args.output}")
