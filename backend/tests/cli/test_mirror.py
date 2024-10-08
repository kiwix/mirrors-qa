from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import models
from mirrors_qa_backend.db.mirrors import (
    _update_mirror_country_and_region,  # pyright: ignore[reportPrivateUsage]
)


def test_update_mirror_country_and_region(
    dbsession: OrmSession, db_mirror: models.Mirror
):

    # Set up a country and region in the database.
    region = models.Region(code="eu", name="Europe")
    dbsession.add(region)

    country = models.Country(code="fr", name="France")
    country.region = region
    dbsession.add(country)

    db_mirror = _update_mirror_country_and_region(dbsession, country.code, db_mirror)
    assert db_mirror.country is not None
    assert db_mirror.country == country
    assert db_mirror.region == region
