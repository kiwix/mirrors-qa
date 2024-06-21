from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.models import Country


def get_countries(session: OrmSession, *country_codes: str) -> list[Country]:
    return list(
        session.scalars(select(Country).where(Country.code.in_(country_codes))).all()
    )


def get_country_or_none(session: OrmSession, country_code: str) -> Country | None:
    return session.scalars(
        select(Country).where(Country.code == country_code)
    ).one_or_none()
