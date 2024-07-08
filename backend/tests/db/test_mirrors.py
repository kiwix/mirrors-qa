import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import schemas
from mirrors_qa_backend.db import count_from_stmt, models
from mirrors_qa_backend.db.exceptions import EmptyMirrorsError
from mirrors_qa_backend.db.mirrors import create_mirrors, create_or_update_mirror_status
from mirrors_qa_backend.serializer import serialize_mirror


def test_db_empty(dbsession: OrmSession):
    assert count_from_stmt(dbsession, select(models.Country)) == 0


def test_create_no_mirrors(dbsession: OrmSession):
    assert create_mirrors(dbsession, []) == 0


def test_create_mirrors(dbsession: OrmSession, schema_mirror: schemas.Mirror):
    assert create_mirrors(dbsession, [schema_mirror]) == 1


def test_raises_empty_mirrors_error(dbsession: OrmSession):
    with pytest.raises(EmptyMirrorsError):
        create_or_update_mirror_status(dbsession, [])


def test_register_new_mirror(
    dbsession: OrmSession,
    schema_mirror: schemas.Mirror,
    new_schema_mirror: schemas.Mirror,
):
    result = create_or_update_mirror_status(
        dbsession, [schema_mirror, new_schema_mirror]
    )
    assert result.nb_mirrors_added == 1


def test_disable_old_mirror(
    dbsession: OrmSession,
    db_mirror: models.Mirror,  # noqa: ARG001 [pytest fixture that saves a mirror]
    new_schema_mirror: schemas.Mirror,
):
    result = create_or_update_mirror_status(dbsession, [new_schema_mirror])
    assert result.nb_mirrors_disabled == 1


def test_no_mirrors_disabled(dbsession: OrmSession, schema_mirror: schemas.Mirror):
    result = create_or_update_mirror_status(dbsession, [schema_mirror])
    assert result.nb_mirrors_disabled == 0


def test_no_mirrors_added(dbsession: OrmSession, schema_mirror: schemas.Mirror):
    result = create_or_update_mirror_status(dbsession, [schema_mirror])
    assert result.nb_mirrors_added == 0


def test_re_enable_existing_mirror(
    dbsession: OrmSession,
):
    # Create a mirror in the database with enabled set to False
    db_mirror = models.Mirror(
        id="mirrors.dotsrc.org",
        base_url="https://mirrors.dotsrc.org/kiwix/",
        enabled=False,
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
    db_mirror.country = models.Country(code="dk", name="Denmark")
    dbsession.add(db_mirror)

    # Update the status of the mirror
    schema_mirror = serialize_mirror(db_mirror)
    schema_mirror.enabled = True

    result = create_or_update_mirror_status(dbsession, [schema_mirror])
    assert result.nb_mirrors_added == 1
