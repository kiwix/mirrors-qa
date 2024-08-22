from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.db.country import get_country_or_none
from mirrors_qa_backend.db.exceptions import EmptyMirrorsError, RecordDoesNotExistError
from mirrors_qa_backend.db.models import Mirror
from mirrors_qa_backend.db.region import get_region_or_none


@dataclass
class MirrorsUpdateResult:
    """Results of an update to the list of mirrors in the database"""

    nb_mirrors_added: int = 0
    nb_mirrors_disabled: int = 0


def update_mirror_country(
    session: OrmSession, country_code: str, mirror: Mirror
) -> Mirror:
    logger.debug("Updating mirror country information.")
    mirror.country = get_country_or_none(session, country_code)
    if mirror.country and mirror.country.region_code:
        mirror.region = get_region_or_none(session, mirror.country.region_code)
    session.add(mirror)
    return mirror


def create_mirrors(session: OrmSession, mirrors: list[schemas.Mirror]) -> int:
    """Number of mirrors created in the database.

    Assumes that each mirror does not exist on the database.
    """
    nb_created = 0
    for mirror in mirrors:
        db_mirror = Mirror(
            id=mirror.id,
            base_url=mirror.base_url,
            enabled=mirror.enabled,
            asn=mirror.asn,
            score=mirror.score,
            latitude=mirror.latitude,
            longitude=mirror.longitude,
            country_only=mirror.country_only,
            region_only=mirror.country_only,
            as_only=mirror.as_only,
            other_countries=mirror.other_countries,
        )

        session.add(db_mirror)

        if mirror.country_code:
            update_mirror_country(session, mirror.country_code, db_mirror)

        logger.debug(f"Registered new mirror: {db_mirror.id}.")
        nb_created += 1
    return nb_created


def create_or_update_mirror_status(
    session: OrmSession, mirrors: list[schemas.Mirror]
) -> MirrorsUpdateResult:
    """Updates the status of mirrors in the database and creates any new mirrors.

    Raises:
        EmptyMirrorsError if the provided list of mirrors is empty.

    """
    if not mirrors:
        raise EmptyMirrorsError("mirrors list must not be empty")

    result = MirrorsUpdateResult()
    # Map the id (hostname) of each mirror from the mirrors list for comparison
    # against the id of mirrors from the database. To be used in determining
    # if this mirror is a new mirror, in which case it should be added
    current_mirrors: dict[str, schemas.Mirror] = {
        mirror.id: mirror for mirror in mirrors
    }

    # Map the id (hostname) of each mirror from the database for comparison
    # against the id of mirrors in current_mirrors. To be used in determining
    # if this mirror should be disabled
    db_mirrors: dict[str, Mirror] = {
        mirror.id: mirror for mirror in session.scalars(select(Mirror)).all()
    }

    # Create any mirror that doesn't exist on the database
    for mirror_id, mirror in current_mirrors.items():
        if mirror_id not in db_mirrors:
            # Create the mirror as it doesn't exist on the database.
            result.nb_mirrors_added += create_mirrors(session, [mirror])

    # Disable any mirror in the database that doesn't exist on the current
    # list of mirrors. However, if a mirror is disabled in the database and
    # exists in the list, re-enable it
    for db_mirror_id, db_mirror in db_mirrors.items():
        if db_mirror_id not in current_mirrors:
            logger.debug(f"Disabling mirror: {db_mirror.id}")
            db_mirror.enabled = False
            session.add(db_mirror)
            result.nb_mirrors_disabled += 1
        elif not db_mirror.enabled:  # re-enable mirror if it was disabled
            logger.debug(f"Re-enabling mirror: {db_mirror.id}")
            db_mirror.enabled = True
            session.add(db_mirror)
            result.nb_mirrors_added += 1

        # New mirrors DB model contain country data. As such, we update the
        # country information regardless of the status update.
        if db_mirror_id in current_mirrors:
            country_code = current_mirrors[db_mirror_id].country_code
            if country_code:
                update_mirror_country(session, country_code, db_mirror)
    return result


def get_mirror(session: OrmSession, mirror_id: str) -> Mirror:
    """Get a mirror from the DB."""
    mirror = session.scalars(select(Mirror).where(Mirror.id == mirror_id)).one_or_none()
    if mirror is None:
        raise RecordDoesNotExistError(f"Mirror with id: {mirror_id} does not exist.")
    return mirror


def get_enabled_mirrors(session: OrmSession) -> list[Mirror]:
    """Get all the enabled mirrors from the DB"""
    return list(
        session.scalars(
            select(Mirror).where(Mirror.enabled == True)  # noqa: E712
        ).all()
    )
