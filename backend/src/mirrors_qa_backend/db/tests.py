import datetime
from dataclasses import dataclass
from ipaddress import IPv4Address
from uuid import UUID

from sqlalchemy import UnaryExpression, asc, desc, func, select, update
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.models import Mirror, Test, Worker
from mirrors_qa_backend.enums import SortDirectionEnum, StatusEnum, TestSortColumnEnum
from mirrors_qa_backend.settings import Settings


@dataclass
class TestListResult:
    """Result of query to list tests from the database."""

    nb_tests: int
    tests: list[Test]


def filter_test(
    test: Test,
    *,
    worker_id: str | None = None,
    country_code: str | None = None,
    statuses: list[StatusEnum] | None = None,
) -> bool:
    """Checks if a test has the same attribute as the provided attribute.

    Base logic for filtering a test from a database.
    Used by test code to validate return values from list_tests.
    """
    if worker_id is not None and test.worker_id != worker_id:
        return False
    if country_code is not None and test.country_code != country_code:
        return False
    if statuses is not None and test.status not in statuses:
        return False
    return True


def get_test(session: OrmSession, test_id: UUID) -> Test:
    test = session.scalars(select(Test).where(Test.id == test_id)).one_or_none()
    if test is None:
        raise RecordDoesNotExistError(f"Test with id: {test_id} does not exist.")
    return test


def list_tests(
    session: OrmSession,
    *,
    worker_id: str | None = None,
    country_code: str | None = None,
    statuses: list[StatusEnum] | None = None,
    page_num: int = 1,
    page_size: int = Settings.MAX_PAGE_SIZE,
    sort_column: TestSortColumnEnum = TestSortColumnEnum.requested_on,
    sort_direction: SortDirectionEnum = SortDirectionEnum.asc,
) -> TestListResult:

    # If no status is provided, populate status with all the allowed values
    if statuses is None:
        statuses = list(StatusEnum)

    if sort_direction == SortDirectionEnum.asc:
        direction = asc
    else:
        direction = desc

    # By default, we want to sort tests on requested_on. However, if a client
    # provides a sort_column, we give their sort_column a higher priority
    order_by: tuple[UnaryExpression[str], ...]
    if sort_column != TestSortColumnEnum.requested_on:
        order_by = (
            direction(sort_column.name),
            asc(TestSortColumnEnum.requested_on.name),
        )
    else:
        order_by = (direction(sort_column.name),)

    # If a client provides an argument i.e it is not None, we compare the corresponding
    # model field against the argument, otherwise, we compare the argument to
    # its default in the database which translates to a SQL true i.e we don't
    # filter based on this argument.
    query = (
        select(func.count().over().label("total_records"), Test)
        .where(
            (Test.worker_id == worker_id) | (worker_id is None),
            (Test.country_code == country_code) | (country_code is None),
            (Test.status.in_(statuses)),
        )
        .order_by(*order_by)
        .offset((page_num - 1) * page_size)
        .limit(page_size)
    )

    result = TestListResult(nb_tests=0, tests=[])

    for total_records, test in session.execute(query).all():
        result.nb_tests = total_records
        result.tests.append(test)

    return result


def update_test(
    session: OrmSession,
    test_id: UUID,
    *,
    status: StatusEnum = StatusEnum.PENDING,
    error: str | None = None,
    ip_address: IPv4Address | None = None,
    asn: str | None = None,
    city: str | None = None,
    latency: float | None = None,
    download_size: int | None = None,
    duration: float | None = None,
    speed: float | None = None,
    started_on: datetime.datetime | None = None,
    isp: str | None = None,
) -> Test:
    test = get_test(session, test_id)
    # If a value is provided, it takes precedence over the default value of the model
    test.status = status
    test.error = error if error else test.error
    test.ip_address = ip_address if ip_address else test.ip_address
    test.asn = asn if asn else test.asn
    test.city = city if city else test.city
    test.latency = latency if latency else test.latency
    test.download_size = download_size if download_size else test.download_size
    test.duration = duration if duration else test.duration
    test.speed = speed if speed else test.speed
    test.started_on = started_on if started_on else test.started_on
    test.isp = isp if isp else test.isp

    session.add(test)
    session.flush()

    return test


def create_test(
    session: OrmSession,
    *,
    worker: Worker,
    mirror: Mirror,
    country_code: str,
) -> Test:
    test = Test(status=StatusEnum.PENDING, country_code=country_code)
    test.worker = worker
    test.mirror = mirror

    session.add(test)
    session.flush()
    return test


def expire_tests(session: OrmSession, interval: datetime.timedelta) -> list[Test]:
    """Change the status of PENDING tests created before the interval to MISSED"""
    end = datetime.datetime.now() - interval
    begin = datetime.datetime.fromtimestamp(0)
    return list(
        session.scalars(
            update(Test)
            .where(
                Test.requested_on.between(begin, end),
                Test.status == StatusEnum.PENDING,
            )
            .values(status=StatusEnum.MISSED)
            .returning(Test)
        ).all()
    )
