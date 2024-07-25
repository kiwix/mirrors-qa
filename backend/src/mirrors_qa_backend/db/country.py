from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.models import Country


def get_countries(session: OrmSession, country_codes: list[str]) -> list[Country]:
    """Get countries with the provided country codes.

    Gets all available countries if no country codes are provided.
    """
    return list(
        session.scalars(
            select(Country).where(
                (Country.code.in_(country_codes)) | (country_codes == [])
            )
        ).all()
    )


def get_country_or_none(session: OrmSession, country_code: str) -> Country | None:
    return session.scalars(
        select(Country).where(Country.code == country_code)
    ).one_or_none()


def get_country(session: OrmSession, country_code: str) -> Country:
    if country := get_country_or_none(session, country_code):
        return country
    raise RecordDoesNotExistError(f"Country with code {country_code} does not exist.")


def create_country(
    session: OrmSession, *, country_code: str, country_name: str
) -> Country:
    """Creates a new country in the database."""
    session.execute(
        insert(Country)
        .values(code=country_code, name=country_name)
        .on_conflict_do_nothing(index_elements=["code"])
    )
    return get_country(session, country_code)


def update_countries(session: OrmSession, country_mapping: dict[str, str]) -> None:
    """Updates the list of countries in the database."""
    for country_code, country_name in country_mapping.items():
        create_country(session, country_code=country_code, country_name=country_name)
