import sys
from argparse import Namespace

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.mirrors import create_or_update_mirror_status
from mirrors_qa_backend.exceptions import MirrorsRequestError
from mirrors_qa_backend.extract import get_current_mirrors


def update_mirrors(args: Namespace) -> None:  # noqa: ARG001
    logger.info("Updating mirrors list.")
    try:
        with Session.begin() as session:
            results = create_or_update_mirror_status(session, get_current_mirrors())
    except MirrorsRequestError as exc:
        logger.info(f"error while updating mirrors: {exc}")
        sys.exit(1)
    logger.info(
        f"Updated mirrors list. Added {results.nb_mirrors_added} mirror(s), "
        f"disabled {results.nb_mirrors_disabled} mirror(s)"
    )
