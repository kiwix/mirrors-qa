from dataclasses import dataclass
from itertools import chain

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.db.country import get_country, get_country_or_none
from mirrors_qa_backend.db.exceptions import EmptyMirrorsError, RecordDoesNotExistError
from mirrors_qa_backend.db.models import Mirror
from mirrors_qa_backend.db.region import (
    get_countries_for,
    get_region,
    get_region_or_none,
)


@dataclass
class MirrorsUpdateResult:
    """Results of an update to the list of mirrors in the database"""

    nb_mirrors_added: int = 0
    nb_mirrors_disabled: int = 0


def _update_mirror_country_and_region(
    session: OrmSession, country_code: str, mirror: Mirror
) -> Mirror:
    """Update the mirror country and region using the country code if they exist.

    Used during mirror list update to set region and country as these fields
    were missing in old DB schema.
    """
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
            _update_mirror_country_and_region(session, mirror.country_code, db_mirror)

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
                _update_mirror_country_and_region(session, country_code, db_mirror)
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


def update_mirror_countries_from_regions(
    session: OrmSession, mirror: Mirror, region_codes: set[str]
) -> Mirror:
    """Update the list of other countries for a mirror with countries from region codes.

    Sets the list of other countries to empty if no regions are provided.

    Because otherCountries overrides the mirror region and country choice as per
    MirroBrain configuration, the list of countries in this mirror's region is
    added to the list.
    """
    if not region_codes:
        mirror.other_countries = []
        session.add(mirror)
        return mirror

    if mirror.region_code:
        region_codes.add(mirror.region_code)

    country_codes = [
        country.code
        for country in chain.from_iterable(
            get_countries_for(session, region_code) for region_code in region_codes
        )
    ]
    if not country_codes:
        raise ValueError("No countries found in provided regions.")

    mirror.other_countries = country_codes
    session.add(mirror)
    return mirror


def update_mirror_region(
    session: OrmSession, mirror: Mirror, region_code: str
) -> Mirror:
    """Updates the region the mirror server is located.

    Assumes the region exists in the DB.
    This does not update the country the mirror is located in.
    """
    mirror.region = get_region(session, region_code)
    session.add(mirror)
    return mirror


def update_mirror_country(
    session: OrmSession, mirror: Mirror, country_code: str
) -> Mirror:
    """Update the country the mirror server is located.

    Assumes the country exists in the DB.
    This does not update the region the mirror is located in.
    """
    mirror.country = get_country(session, country_code)
    session.add(mirror)
    return mirror
