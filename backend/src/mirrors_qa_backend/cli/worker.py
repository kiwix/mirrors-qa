import sys
from argparse import Namespace

import pycountry
from cryptography.hazmat.primitives import serialization

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.worker import create_worker as create_db_worker


def create_worker(args: Namespace):
    # Ensure all the countries are valid country codes
    country_codes: list[str] = args.countries if args.countries else []
    for country_code in country_codes:
        if len(country_code) != 2:  # noqa: PLR2004
            logger.info(f"Country code '{country_code}' must be two characters long")
            sys.exit(1)

        if not pycountry.countries.get(alpha_2=country_code):
            logger.info(f"'{country_code}' is not valid country code")
            sys.exit(1)

    try:
        with args.private_key_file as fp:
            private_key = serialization.load_pem_private_key(
                bytes(fp.read(), encoding="ascii"), password=None
            )  # pyright: ignore[reportReturnType]
    except Exception as exc:
        logger.info(f"Unable to load private key: {exc}")
        sys.exit(1)

    try:
        with Session.begin() as session:
            create_db_worker(
                session,
                args.worker_id,
                country_codes,
                private_key,  # pyright: ignore [reportGeneralTypeIssues, reportArgumentType]
            )
    except Exception as exc:
        logger.info(f"error while creating worker: {exc}")
        sys.exit(1)

    logger.info(f"Created worker {args.worker_id} successfully")
