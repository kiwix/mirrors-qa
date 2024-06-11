import os
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """Worker manager configuration"""

    # number of seconds between each poll
    sleep_interval = int(getenv("SLEEP_INTERVAL", default=180))
    debug = bool(getenv("DEBUG", default=False))
