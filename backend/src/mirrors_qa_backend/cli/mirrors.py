from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.mirrors import create_or_update_mirror_status
from mirrors_qa_backend.extract import get_current_mirrors


def update_mirrors() -> None:
    logger.info("Updating mirrors list.")
    with Session.begin() as session:
        results = create_or_update_mirror_status(session, get_current_mirrors())
    logger.info(
        f"Updated mirrors list. Added {results.nb_mirrors_added} mirror(s), "
        f"disabled {results.nb_mirrors_disabled} mirror(s)"
    )
