import os
from pathlib import Path
from typing import Any

from humanfriendly import parse_size, parse_timespan


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """Task worker configuration"""

    REQUESTS_TIMEOUT_SECONDS = int(getenv("REQUESTS_TIMEOUT_SECONDS", default=10))
    REQUESTS_MAX_RETRIES = int(getenv("REQUESTS_MAX_RETRIES", default=3))
    REQUESTS_RETRY_SECONDS = parse_timespan(
        getenv("REQUESTS_RETRY_DURATION", default="3s")
    )
    DEBUG = bool(getenv("DEBUG", default=False))
    WORKDIR = Path(getenv("WORKDIR", default="/data")).resolve()
    USER_AGENT = getenv("USER_AGENT", default="speedtester/robot")
    CHUNK_SIZE = parse_size(getenv("CHUNK_SIZE", default="10MiB"))
