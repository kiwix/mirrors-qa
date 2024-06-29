import argparse
import logging
import sys

import requests

from mirrors_qa_task import logger
from mirrors_qa_task.__about__ import __version__
from mirrors_qa_task.settings import Settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", "-O", help="Name of file to write results", default="output.json"
    )
    parser.add_argument("--version", help="Show version and exit", action="store_true")
    parser.add_argument(
        "-v", "--verbose", help="Show verbose output", action="store_true"
    )
    args = parser.parse_args()
    if args.version:
        logger.setLevel(logging.DEBUG)

    if args.version:
        print(f"Mirrors QA Worker Task: {__version__}")  # noqa: T201
        sys.exit(0)

    resp = requests.get(
        "https://am.i.mullvad.net/json",
        timeout=Settings.REQUESTS_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    (Settings.WORKDIR / args.output).write_bytes(resp.content)
    logger.info(f"Saved data to {args.output}")
