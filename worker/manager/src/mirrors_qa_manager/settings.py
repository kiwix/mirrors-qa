import os
from pathlib import Path
from typing import Any

from humanfriendly import parse_timespan


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """Worker manager configuration"""

    # number of seconds between each poll to the Backend API
    SLEEP_SECONDS = parse_timespan(getenv("SLEEP_DURATION", default="1h"))
    DEBUG = bool(getenv("DEBUG", default=False))
    BACKEND_API_URI = getenv("BACKEND_API_URI", mandatory=True)
    # in-container directory for worker manager
    WORKDIR_FPATH = Path(getenv("WORKDIR", default="/data"))
    DOCKER_SOCKET = Path(getenv("DOCKER_SOCKET", default="/var/run/docker.sock"))
    PRIVATE_KEY_FPATH = Path(getenv("PRIVATE_KEY_FILE", default="/etc/ssh/keys/id_rsa"))
    DOCKER_CLIENT_TIMEOUT_SECONDS = parse_timespan(
        getenv("DOCKER_CLIENT_TIMEOUT_DURATION", default="1m")
    )
    # number of times to retry a call to the Docker daemon
    DOCKER_API_RETRIES = int(getenv("DOCKER_API_RETRIES", default=3))
    DOCKER_API_RETRY_SECONDS = parse_timespan(
        getenv("DOCKER_API_RETRY_DURATION", default="5s")
    )
    # Wireguar container settings
    WIREGUARD_IMAGE = getenv(
        "WIREGUARD_IMAGE", default="lscr.io/linuxserver/wireguard:1.0.20210914"
    )
    WIREGUARD_CONTAINER_NAME = getenv(
        "WIREGUARD_CONTAINER_NAME", default="mirrors-qa-wireguard"
    )
    # Optional path for loading kernel modules for wireguard container
    WIREGUARD_KERNEL_MODULES_FPATH = Path(
        getenv("WIREGUARD_KERNEL_MODULES", default="/lib/modules")
    )
    # The Docker Python SDK expects healthcheck units to be in nanoseconds.
    # https://docker-py.readthedocs.io/en/stable/containers.html
    # Convert the provided healthcheck time parameters from seconds to nanoseconds
    WIREGUARD_HEALTHCHECK_NANOSECONDS = int(
        getenv("WIREGUARD_HEALTHCHECK_INTERVAL_SECONDS", default=10) * 1e9
    )
    WIREGUARD_HEALTHCHECK_TIMEOUT_NANOSECONDS = int(
        getenv("WIREGUARD_HEALTHCHECK_TIMEOUT_SECONDS", default=5) * 1e9
    )
    WIREGUARD_HEALTHCHECK_RETRIES = int(
        getenv("WIREGUARD_HEALTHCHECK_RETRIES", default=3)
    )
    TASK_WORKER_IMAGE = getenv("TASK_WORKER_IMAGE", mandatory=True)
