import datetime
from ipaddress import IPv4Address

import pytest
from faker import Faker
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import models
from mirrors_qa_backend.db import tests as db_tests
from mirrors_qa_backend.enums import StatusEnum


@pytest.mark.num_tests(1)
def test_get_test(dbsession: OrmSession, tests: list[models.Test]):
    test = tests[0]
    result = db_tests.get_test(dbsession, test.id)
    assert result is not None
    assert result.id == test.id


@pytest.mark.parametrize(
    ["worker_id", "country", "statuses", "expected"],
    [
        (None, None, None, True),
        ("worker_id", None, None, False),
        (None, "country", [StatusEnum.PENDING], False),
        (None, None, list(StatusEnum), True),
        ("worker_id", "country", [StatusEnum.PENDING], False),
    ],
)
def test_basic_filter(
    *,
    dbsession: OrmSession,
    worker_id: str | None,
    country: str | None,
    statuses: list[StatusEnum] | None,
    expected: bool,
):
    test = db_tests.create_or_update_test(dbsession, status=StatusEnum.PENDING)
    assert (
        db_tests.filter_test(
            test, worker_id=worker_id, country=country, statuses=statuses
        )
        == expected
    )


@pytest.mark.num_tests
@pytest.mark.parametrize(
    ["worker_id", "country", "statuses"],
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
    statuses: list[StatusEnum] | None,
):
    filtered_tests = [
        test
        for test in tests
        if db_tests.filter_test(
            test, worker_id=worker_id, country=country, statuses=statuses
        )
    ]
    result = db_tests.list_tests(
        dbsession, worker_id=worker_id, country=country, statuses=statuses
    )
    assert len(filtered_tests) == result.nb_tests


@pytest.mark.num_tests(1)
def test_update_test(dbsession: OrmSession, tests: list[models.Test], data_gen: Faker):
    test_id = tests[0].id
    download_size = 1_000_000
    duration = 1_000
    latency = 100
    speed = download_size / duration
    update_values = {
        "status": data_gen.test_status(),
        "country": data_gen.test_country(),
        "download_size": download_size,
        "duration": duration,
        "speed": speed,
        "ip_address": IPv4Address(data_gen.ipv4()),
        "started_on": data_gen.date_time(datetime.UTC),
        "latency": latency,
    }
    updated_test = db_tests.create_or_update_test(dbsession, test_id, **update_values)  # type: ignore
    for key, value in update_values.items():
        if hasattr(updated_test, key):
            assert getattr(updated_test, key) == value


@pytest.mark.num_tests(10, status=StatusEnum.PENDING)
@pytest.mark.parametrize(
    ["interval", "expected_status"],
    [
        (datetime.timedelta(seconds=0), StatusEnum.MISSED),
        (datetime.timedelta(days=7), StatusEnum.PENDING),
    ],
)
def test_expire_tests(
    dbsession: OrmSession,
    tests: list[models.Test],
    interval: datetime.timedelta,
    expected_status: StatusEnum,
):
    for test in tests:
        assert test.status == StatusEnum.PENDING

    db_tests.expire_tests(dbsession, interval)
    for test in tests:
        assert test.status == expected_status
