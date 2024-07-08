import pytest
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.location import (
    create_or_get_location,
    get_location,
)
from mirrors_qa_backend.db.models import Location


@pytest.fixture
def location(dbsession: OrmSession) -> Location:
    location = Location(code="ng", name="Nigeria")
    dbsession.add(location)
    return location


def test_location_does_not_exist(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_location(dbsession, "location does not exist")


def test_get_location(dbsession: OrmSession, location: Location):
    db_location = get_location(dbsession, location.code)
    assert db_location.code == location.code
    assert db_location.name == location.name


def test_no_error_on_create_duplicate_location(
    dbsession: OrmSession, location: Location
):
    db_location = create_or_get_location(
        dbsession, country_code=location.code, country_name=location.name
    )
    assert db_location.code == location.code
    assert db_location.name == location.name
