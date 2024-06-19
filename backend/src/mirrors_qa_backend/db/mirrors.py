from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.db import models
from mirrors_qa_backend.db.exceptions import EmptyMirrorsError


@dataclass
class MirrorsUpdateResult:
    """Results of an update to the list of mirrors in the database"""

    nb_mirrors_added: int = 0
    nb_mirrors_disabled: int = 0


def create_mirrors(session: OrmSession, mirrors: list[schemas.Mirror]) -> int:
    """Number of mirrors created in the database.

    Assumes that each mirror does not exist on the database.
    """
    nb_created = 0
    for mirror in mirrors:
        db_mirror = models.Mirror(
            id=mirror.id,
            base_url=mirror.base_url,
            enabled=mirror.enabled,
            region=mirror.region,
            asn=mirror.asn,
            score=mirror.score,
            latitude=mirror.latitude,
            longitude=mirror.longitude,
            country_only=mirror.country_only,
            region_only=mirror.country_only,
            as_only=mirror.as_only,
            other_countries=mirror.other_countries,
        )
        # Ensure the country exists for the mirror
        country = session.scalars(
            select(models.Country).where(models.Country.code == mirror.country.code)
        ).one_or_none()

        if country is None:
            country = models.Country(code=mirror.country.code, name=mirror.country.name)
            session.add(country)

        db_mirror.country = country
        session.add(db_mirror)
        logger.debug(
            f"Registered new mirror: {db_mirror.id!r} for country: {country.name!r}"
        )
        nb_created += 1
    return nb_created


def create_or_update_status(
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
    query = select(models.Mirror).options(selectinload(models.Mirror.country))
    db_mirrors: dict[str, models.Mirror] = {
        mirror.id: mirror for mirror in session.scalars(query).all()
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
            logger.debug(
                f"Disabling mirror: {db_mirror.id!r} for "
                f"country: {db_mirror.country.name!r}"
            )
            db_mirror.enabled = False
            session.add(db_mirror)
            result.nb_mirrors_disabled += 1
        elif not db_mirror.enabled:  # re-enable mirror if it was disabled
            logger.debug(
                f"Re-enabling mirror: {db_mirror.id!r} for "
                f"country: {db_mirror.country.name!r}"
            )
            db_mirror.enabled = True
            session.add(db_mirror)
            result.nb_mirrors_added += 1
    return result
