# ruff: noqa: E712
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import db, schemas
from mirrors_qa_backend.db import mirrors, models


@pytest.fixture(scope="session")
def schema_country() -> schemas.Country:
    return schemas.Country(
        code="in",
        name="India",
        mirrors=[
            schemas.Mirror(
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
        ],
    )


@pytest.fixture(scope="session")
def new_schema_country() -> schemas.Country:
    return schemas.Country(
        code="dk",
        name="Denmark",
        mirrors=[
            schemas.Mirror(
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
            )
        ],
    )


@pytest.fixture
def db_mirror_country() -> models.Country:
    c = models.Country(code="in", name="India")
    c.mirrors = [
        models.Mirror(
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
    ]
    return c


def test_db_empty(dbsession: OrmSession):
    count = db.count_from_stmt(dbsession, select(models.Country))
    assert count == 0


def test_create_mirrors(dbsession: OrmSession, schema_country: schemas.Country):
    mirrors.create_mirrors(dbsession, [schema_country])
    assert db.count_from_stmt(dbsession, select(models.Country)) == 1


def test_all_mirrors_disabled(dbsession: OrmSession, db_mirror_country: models.Country):
    dbsession.add(db_mirror_country)
    mirrors.update_mirrors(dbsession, [])
    assert (
        db.count_from_stmt(
            dbsession, select(models.Mirror).where(models.Mirror.enabled == True)
        )
        == 0
    )


def test_register_new_country_mirror(
    dbsession: OrmSession,
    schema_country: schemas.Country,
    db_mirror_country: models.Country,
    new_schema_country: schemas.Country,
):
    dbsession.add(db_mirror_country)
    mirrors.update_mirrors(dbsession, [schema_country, new_schema_country])
    assert db.count_from_stmt(dbsession, select(models.Mirror)) == 2


def test_disable_old_mirror(
    dbsession: OrmSession,
    db_mirror_country: models.Country,
    new_schema_country: schemas.Country,
):
    dbsession.add(db_mirror_country)
    mirrors.update_mirrors(dbsession, [new_schema_country])
    assert (
        db.count_from_stmt(
            dbsession, select(models.Mirror).where(models.Mirror.enabled == True)
        )
        == 1
    )
