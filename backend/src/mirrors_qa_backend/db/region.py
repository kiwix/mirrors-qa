from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.models import Country, Region


def get_countries(session: OrmSession, region_code: str) -> list[Country]:
    """Get countries belonging to the provided region."""

    return list(
        session.scalars(select(Country).where(Country.region_code == region_code)).all()
    )


def get_region_or_none(session: OrmSession, region_code: str) -> Region | None:
    return session.scalars(
        select(Region).where(Region.code == region_code)
    ).one_or_none()


def get_region(session: OrmSession, region_code: str) -> Region:
    if region := get_region_or_none(session, region_code):
        return region
    raise RecordDoesNotExistError(f"Region with code {region_code} does not exist.")


def create_region(session: OrmSession, *, region_code: str, region_name: str) -> Region:
    """Creates a new continental region in the database."""
    session.execute(
        insert(Region)
        .values(code=region_code, name=region_name)
        .on_conflict_do_nothing(index_elements=["code"])
    )
    return get_region(session, region_code)
