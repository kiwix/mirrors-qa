from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import models


def get_countries_by_name(session: OrmSession, *countries: str) -> list[models.Country]:
    return list(
        session.scalars(
            select(models.Country).where(models.Country.name.in_(countries))
        ).all()
    )
