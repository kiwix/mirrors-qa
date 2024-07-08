import os
from typing import Any

from humanfriendly import parse_timespan


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable.")

    return value


class Settings:
    """Shared backend configuration"""

    DATABASE_URL: str = getenv("POSTGRES_URI", mandatory=True)
    DEBUG = bool(getenv("DEBUG", default=False))
    # number of seconds before requests time out
    REQUESTS_TIMEOUT_SECONDS = parse_timespan(
        getenv("REQUESTS_TIMEOUT_DURATION", default="10s")
    )
    # maximum number of items to return from a request/query
    MAX_PAGE_SIZE = int(getenv("PAGE_SIZE", default=20))
    # url to fetch the list of mirrors
    MIRRORS_URL: str = getenv(
        "MIRRORS_LIST_URL", default="https://download.kiwix.org/mirrors.html"
    )
    # comma-seperated list of mirror hostnames to exclude
    MIRRORS_EXCLUSION_LIST = getenv(
        "EXCLUDED_MIRRORS", default="mirror.isoc.org.il"
    ).split(",")

    TEST_LOCATIONS_URL = getenv(
        "TEST_LOCATIONS_URL", default="https://api.mullvad.net/app/v1/relays"
    )
