from enum import Enum


class StatusEnum(Enum):
    PENDING = 0
    MISSED = 1
    SUCCEEDED = 2
    ERRORED = 3
