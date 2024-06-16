import os
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable.")

    return value


class Settings:
    """Shared backend configuration"""

    DATABASE_URL: str = getenv("POSTGRES_URI", mandatory=True)
    # url to fetch the list of mirrors
    MIRRORS_URL: str = getenv(
        "MIRRORS_LIST_URL", default="https://download.kiwix.org/mirrors.html"
    )
    # comma-seperated list of mirror hostnames to exclude
    MIRRORS_EXCLUSION_LIST = getenv(
        "EXCLUDED_MIRRORS", default="mirror.isoc.org.il"
    ).split(",")
    DEBUG = bool(getenv("DEBUG", default=False))
    # number of seconds before requests time out
    REQUESTS_TIMEOUT = int(getenv("REQUESTS_TIMEOUT", default=5))
    # maximum number of items to return from a request
    MAX_PAGE_SIZE = int(getenv("PAGE_SIZE", default=20))
    # number of seconds before a message expire
    MESSAGE_VALIDITY = int(getenv("MESSAGE_VALIDITY", default=60))
    # number of hours before access tokens expire
    TOKEN_EXPIRY = int(getenv("TOKEN_EXPIRY", default=24))
    JWT_SECRET: str = getenv("JWT_SECRET", mandatory=True)
