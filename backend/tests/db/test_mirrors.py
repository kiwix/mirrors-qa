# ruff: noqa: E712
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import db, schemas
from mirrors_qa_backend.db import mirrors, models


@pytest.fixture(scope="session")
def schema_mirror() -> schemas.Mirror:
    return schemas.Mirror(
        id="mirror-sites-in.mblibrary.info",
        base_url="https://mirror-sites-in.mblibrary.info/mirror-sites/download.kiwix.org/",
        enabled=True,
        region=None,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
        country=schemas.Country(
            code="in",
            name="India",
        ),
    )


@pytest.fixture
def db_mirror() -> models.Mirror:
    mirror = models.Mirror(
        id="mirror-sites-in.mblibrary.info",
        base_url="https://mirror-sites-in.mblibrary.info/mirror-sites/download.kiwix.org/",
        enabled=True,
        region=None,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
    )
    mirror.country = models.Country(code="in", name="India")
    return mirror


@pytest.fixture(scope="session")
def new_schema_mirror() -> schemas.Mirror:
    return schemas.Mirror(
        id="mirrors.dotsrc.org",
        base_url="https://mirrors.dotsrc.org/kiwix/",
        enabled=True,
        region=None,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
        country=schemas.Country(
            code="dk",
            name="Denmark",
        ),
    )


def test_db_empty(dbsession: OrmSession):
    assert db.count_from_stmt(dbsession, select(models.Country)) == 0


def test_create_no_mirrors(dbsession: OrmSession):
    assert mirrors.create_mirrors(dbsession, []) == 0


def test_create_mirrors(dbsession: OrmSession, schema_mirror: schemas.Mirror):
    assert mirrors.create_mirrors(dbsession, [schema_mirror]) == 1


def test_register_new_country_mirror(
    dbsession: OrmSession,
    schema_mirror: schemas.Mirror,
    db_mirror: models.Mirror,
    new_schema_mirror: schemas.Mirror,
):
    dbsession.add(db_mirror)
    result = mirrors.update_mirrors(dbsession, [schema_mirror, new_schema_mirror])
    assert result.nb_mirrors_added == 1


def test_disable_old_mirror(
    dbsession: OrmSession,
    db_mirror: models.Mirror,
    new_schema_mirror: schemas.Mirror,
):
    dbsession.add(db_mirror)
    result = mirrors.update_mirrors(dbsession, [new_schema_mirror])
    assert result.nb_mirrors_disabled == 1


def test_no_mirrors_disabled(
    dbsession: OrmSession, db_mirror: models.Mirror, schema_mirror: schemas.Mirror
):
    dbsession.add(db_mirror)
    result = mirrors.update_mirrors(dbsession, [schema_mirror])
    assert result.nb_mirrors_disabled == 0


def test_no_mirrors_added(
    dbsession: OrmSession, db_mirror: models.Mirror, schema_mirror: schemas.Mirror
):
    dbsession.add(db_mirror)
    result = mirrors.update_mirrors(dbsession, [schema_mirror])
    assert result.nb_mirrors_added == 0
