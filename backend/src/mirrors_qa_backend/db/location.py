from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.models import Location


def create_or_get_location(
    session: OrmSession, *, country_code: str, country_name: str
) -> Location:
    session.execute(
        insert(Location)
        .values(code=country_code, name=country_name)
        .on_conflict_do_nothing(index_elements=["code"])
    )
    return get_location(session, country_code)


def get_location(session: OrmSession, country_code: str) -> Location:
    location = session.scalars(
        select(Location).where(Location.code == country_code)
    ).one_or_none()
    if location is None:
        raise RecordDoesNotExistError(
            f"Location with country code {country_code} does not exist."
        )
    return location


def get_all_locations(session: OrmSession) -> list[Location]:
    return list(session.scalars(select(Location)).all())
