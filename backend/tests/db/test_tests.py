import datetime
from ipaddress import IPv4Address

import pytest
from faker import Faker
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import db
from mirrors_qa_backend.db import models
from mirrors_qa_backend.enums import StatusEnum


@pytest.mark.num_tests(1)
def test_get_test(dbsession: OrmSession, tests: list[models.Test]):
    test = tests[0]
    result = db.tests.get_test(dbsession, test.id)
    assert result is not None
    assert result.id == test.id


@pytest.mark.parametrize(
    ["worker_id", "country", "status", "expect"],
    [
        (None, None, None, True),
        ("worker_id", None, None, False),
        (None, "country", [StatusEnum.PENDING], False),
        (None, None, list(StatusEnum), True),
        ("worker_id", "country", [StatusEnum.PENDING], False),
    ],
)
def test_basic_filter(
    dbsession: OrmSession,
    worker_id: str | None,
    country: str | None,
    status: list[StatusEnum] | None,
    expect: bool,  # noqa
):
    test = db.tests.create_or_update_test(dbsession, status=StatusEnum.PENDING)
    assert (
        db.tests.filter_test(test, worker_id=worker_id, country=country, status=status)
        == expect
    )


@pytest.mark.num_tests
@pytest.mark.parametrize(
    ["worker_id", "country", "status"],
    [
        (None, None, None),
        (None, "Nigeria", None),
        (None, "Nigeria", [StatusEnum.PENDING]),
        (None, None, [StatusEnum.PENDING, StatusEnum.MISSED]),
    ],
)
def test_list_tests(
    dbsession: OrmSession,
    tests: list[models.Test],
    worker_id: str | None,
    country: str | None,
    status: list[StatusEnum] | None,
):
    filtered_tests = [
        test
        for test in tests
        if db.tests.filter_test(
            test, worker_id=worker_id, country=country, status=status
        )
    ]
    result = db.tests.list_tests(
        dbsession, worker_id=worker_id, country=country, status=status
    )
    assert len(filtered_tests) == result.nb_tests


@pytest.mark.num_tests(1)
def test_update_test(dbsession: OrmSession, tests: list[models.Test], fake_data: Faker):
    test_id = tests[0].id
    download_size = 1_000_000
    duration = 1_000
    latency = 100
    speed = download_size / duration
    update_values = {
        "status": fake_data.test_status(),
        "country": fake_data.test_country(),
        "download_size": download_size,
        "duration": duration,
        "speed": speed,
        "ip_address": IPv4Address(fake_data.ipv4()),
        "started_on": fake_data.date_time(datetime.UTC),
        "latency": latency,
    }
    updated_test = db.tests.create_or_update_test(dbsession, test_id, **update_values)  # type: ignore
    for key, value in update_values.items():
        if hasattr(updated_test, key):
            assert getattr(updated_test, key) == value
