import os
from pathlib import Path
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """Worker manager configuration"""

    # number of seconds between each poll to the Backend API
    SLEEP_TIMEOUT = int(getenv("SLEEP_TIMEOUT", default=180))
    DEBUG = bool(getenv("DEBUG", default=False))
    BACKEND_API_URI = getenv("BACKEND_API_URI", mandatory=True)
    # in-container directory for worker manager
    WORKDIR_FPATH = Path(getenv("WORKDIR", default="/data"))
    DOCKER_SOCKET = Path(getenv("DOCKER_SOCKET", default="/var/run/docker.sock"))
    PRIVATE_KEY_FPATH = Path(getenv("PRIVATE_KEY_FILE", default="/etc/ssh/keys/id_rsa"))
    DOCKER_CLIENT_TIMEOUT = int(getenv("DOCKER_CLIENT_TIMEOUT", default=180))
    # number of times to retry a call to the Docker daemon
    DOCKER_API_RETRIES = int(getenv("DOCKER_API_RETRIES", default=3))
    DOCKER_API_RETRY_SECONDS = int(getenv("DOCKER_API_RETRY_SECONDS", default=5))
    # Wireguar container settings
    WIREGUARD_IMAGE = getenv(
        "WIREGUARD_IMAGE", default="lscr.io/linuxserver/wireguard:latest"
    )
    WIREGUARD_CONTAINER_NAME = getenv("WIREGUARD_CONTAINER_NAME", default="wireguard")
    # Optional path for loading kernel modules for wireguard
    WIREGUARD_KERNEL_MODULES_FPATH = Path(
        getenv("WIREGUARD_KERNEL_MODULES", default="/lib/modules")
    )
    # The Docker SDK expects healthcheck units to be in nanoseconds.Convert
    # the provided healthcheck time parameters from seconds to nanoseconds
    WIREGUARD_HEALTHCHECK_INTERVAL = int(
        getenv("WIREGUARD_HEALTHCHECK_INTERVAL", default=10) * 1e9
    )
    WIREGUARD_HEALTHCHECK_TIMEOUT = int(
        getenv("WIREGUARD_HEALTHCHECK_TIMEOUT", default=5) * 1e9
    )
    WIREGUARD_HEALTHCHECK_RETRIES = int(
        getenv("WIREGUARD_HEALTHCHECK_RETRIES", default=3)
    )
    TASK_WORKER_IMAGE = getenv("TASK_WORKER_IMAGE", mandatory=True)
