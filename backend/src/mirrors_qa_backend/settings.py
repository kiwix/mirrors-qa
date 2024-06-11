import os
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable.")

    return value


class Settings:
    """Shared backend configuration"""

    database_url: str = getenv("POSTGRES_URI", mandatory=True)
    # url to fetch the list of mirrors
    mirrors_url: str = getenv(
        "MIRRORS_LIST_URL", default="https://download.kiwix.org/mirrors.html"
    )
    # comma-seperated list of mirror hostnames to exclude
    mirrors_exclusion_list = getenv(
        "EXCLUDED_MIRRORS", default="mirror.isoc.org.il"
    ).split(",")
    debug = bool(getenv("DEBUG", default=False))
    # number of seconds before requests time out
    requests_timeout = int(getenv("REQUESTS_TIMEOUT", default=5))
