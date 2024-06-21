from enum import Enum


class StatusEnum(Enum):
    """Status of a test in the database."""

    PENDING = "PENDING"
    MISSED = "MISSED"
    SUCCEEDED = "SUCCEEDED"
    ERRORED = "ERRORED"


class TestSortColumnEnum(Enum):
    """Fields for sorting tests from a database"""

    requested_on = "requested_on"
    started_on = "started_on"
    status = "status"
    worker_id = "worker_id"
    country_code = "country_code"
    city = "city"


class SortDirectionEnum(Enum):
    """Direction to sort list of results from a database"""

    asc = "asc"
    desc = "desc"
