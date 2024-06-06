import os


def must_get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise OSError(f"Please set the {key} environment variable")
    return value


class Settings:
    """Worker manager configuration"""

    pass
