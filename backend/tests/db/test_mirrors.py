import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import schemas
from mirrors_qa_backend.db import count_from_stmt
from mirrors_qa_backend.db.exceptions import EmptyMirrorsError
from mirrors_qa_backend.db.mirrors import (
    create_mirrors,
    create_or_update_mirror_status,
    update_mirror_countries_from_regions,
    update_mirror_country,
    update_mirror_region,
)
from mirrors_qa_backend.db.models import Country, Mirror, Region
from mirrors_qa_backend.serializer import serialize_mirror


def test_db_empty(dbsession: OrmSession):
    assert count_from_stmt(dbsession, select(Country)) == 0


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
    db_mirror: Mirror,  # noqa: ARG001 [pytest fixture that saves a mirror]
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
    db_mirror = Mirror(
        id="mirrors.dotsrc.org",
        base_url="https://mirrors.dotsrc.org/kiwix/",
        enabled=False,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
    )
    dbsession.add(db_mirror)

    # Update the status of the mirror
    schema_mirror = serialize_mirror(db_mirror)
    schema_mirror.enabled = True

    result = create_or_update_mirror_status(dbsession, [schema_mirror])
    assert result.nb_mirrors_added == 1


def test_update_mirror_region(
    dbsession: OrmSession, db_mirror: Mirror, africa_region: Region
):
    update_mirror_region(dbsession, db_mirror, africa_region.code)
    assert db_mirror.region == africa_region


def test_update_mirror_country(dbsession: OrmSession, db_mirror: Mirror):
    country = Country(code="fr", name="France")
    dbsession.add(country)

    update_mirror_country(dbsession, db_mirror, country.code)
    assert db_mirror.country == country


def test_update_mirror_countries_from_empty_region(
    dbsession: OrmSession, db_mirror: Mirror, africa_region: Region
):

    db_mirror.region = africa_region
    db_mirror.country = africa_region.countries[0]
    db_mirror.other_countries = ["us", "fr"]
    dbsession.add(db_mirror)

    update_mirror_countries_from_regions(dbsession, db_mirror, set())
    assert db_mirror.other_countries == []


def test_update_mirror_countries_from_regions(
    dbsession: OrmSession,
    db_mirror: Mirror,
    africa_region: Region,
    europe_region: Region,
    asia_region: Region,
):

    regions = [asia_region, africa_region, europe_region]
    expected_country_codes = set()
    region_codes = set()

    for region in regions:
        region_codes.add(region.code)
        for country in region.countries:
            expected_country_codes.add(country.code)

    if db_mirror.country:
        expected_country_codes.add(db_mirror.country_code)

    db_mirror = update_mirror_countries_from_regions(dbsession, db_mirror, region_codes)

    assert db_mirror.other_countries is not None
    assert len(expected_country_codes) == len(db_mirror.other_countries)

    for country_code in expected_country_codes:
        assert country_code in db_mirror.other_countries
