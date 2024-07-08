from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.locations import update_locations


def update_test_locations() -> None:
    with Session.begin() as session:
        locations = update_locations(session)
        logger.info(f"Updated list of locations, {len(locations)} locations in DB.")
