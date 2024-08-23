from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.mirrors import (
    create_or_update_mirror_status,
    get_mirror,
    update_mirror_countries_from_regions,
)
from mirrors_qa_backend.db.mirrors import (
    update_mirror_country as update_db_mirror_country,
)
from mirrors_qa_backend.db.mirrors import (
    update_mirror_region as update_db_mirror_region,
)
from mirrors_qa_backend.extract import get_current_mirrors


def update_mirrors() -> None:
    """Update the list of active mirrors in the DB."""
    logger.info("Updating mirrors list.")
    with Session.begin() as session:
        results = create_or_update_mirror_status(session, get_current_mirrors())
    logger.info(
        f"Updated mirrors list. Added {results.nb_mirrors_added} mirror(s), "
        f"disabled {results.nb_mirrors_disabled} mirror(s)"
    )


def update_mirror_other_countries(mirror_id: str, region_codes: set[str]) -> None:
    with Session.begin() as session:
        mirror = update_mirror_countries_from_regions(
            session, get_mirror(session, mirror_id), region_codes
        )

        logger.info(
            f"Set {len(mirror.other_countries)} countries "  # pyright: ignore[reportGeneralTypeIssues,reportArgumentType]
            f"for mirror {mirror.id}"
        )


def update_mirror_region(mirror_id: str, region_code: str) -> None:
    """Update the region the mirror server is located."""
    with Session.begin() as session:
        update_db_mirror_region(session, get_mirror(session, mirror_id), region_code)


def update_mirror_country(mirror_id: str, country_code: str) -> None:
    with Session.begin() as session:
        update_db_mirror_country(session, get_mirror(session, mirror_id), country_code)
