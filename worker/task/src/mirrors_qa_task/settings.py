import os
from pathlib import Path
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """Worker task configuration"""

    REQUESTS_TIMEOUT_SECONDS = int(getenv("REQUESTS_TIMEOUT", default=60))
    DEBUG = bool(getenv("DEBUG", default=False))
    WORKDIR = Path(getenv("WORKDIR", default="/data")).resolve()
