# pyright: strict, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportOptionalSubscript=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from docker import DockerClient
from docker.errors import APIError, ImageNotFound, NotFound
from docker.models.containers import Container, ExecResult
from docker.models.images import Image

from mirrors_qa_manager import logger
from mirrors_qa_manager.settings import Settings


def retry(
    func: Callable[..., Any] | None = None,
    *,
    retries: int = Settings.DOCKER_API_RETRIES,
    interval: float = Settings.DOCKER_API_RETRY_SECONDS,
) -> Any:
    """Retry API calls to the Docker daemon on failure."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                # most 404 errors would be from incorrect image/tag name but
                # we still want to avoid crashing on 404 due to temporary
                # docker-hub issues
                except (ImageNotFound, APIError) as exc:
                    if attempt <= retries:
                        logger.error(
                            f"docker api error for {func.__name__} "
                            f"(attempt {attempt}): {exc}"
                        )
                        time.sleep(interval * attempt)
                        continue
                    raise exc

        return wrapped

    if func:
        return decorator(func)

    return decorator


def get_running_container_name() -> str:
    """Determine the name of this container."""
    return (Path("/etc/hostname").read_text()).strip()


def get_container(client: DockerClient, container_name: str) -> Container:
    container = client.containers.get(container_name)
    container.reload()
    return container  # pyright: ignore [reportGeneralTypeIssues,reportReturnType]


@retry
def get_docker_client() -> DockerClient:
    logger.info(f"Connecting to Docker API on {Settings.DOCKER_SOCKET}")
    client = DockerClient(
        base_url=f"unix://{Settings.DOCKER_SOCKET}",
        timeout=Settings.DOCKER_CLIENT_TIMEOUT_SECONDS,
    )
    client.ping()
    logger.info("Connected to Docker API successfully")
    return client


@retry
def remove_container(
    client: DockerClient,
    container_id: str,
    *,
    remove_volumes: bool = False,
    force: bool = False,
    not_found_ok: bool = False,
) -> None:
    try:
        container = get_container(client, container_id)
    except NotFound as exc:
        if not_found_ok:
            return
        raise exc
    else:
        container.remove(  # pyright: ignore [reportGeneralTypeIssues]
            v=remove_volumes, force=force
        )


@retry
def get_or_pull_image(client: DockerClient, name: str) -> Image:
    logger.debug(f"Getting image {name}")
    # task worker is always pulled to ensure we can update our code
    if ":" not in name:
        # consider missing :tag info as a local image for tests
        return client.images.get(
            name
        )  # pyright: ignore[reportGeneralTypeIssues,reportReturnType]

    return client.images.pull(
        name
    )  # pyright: ignore[reportGeneralTypeIssues,reportReturnType]


def run_container(client: DockerClient, image_name: str, **kwargs: Any) -> Container:
    image = get_or_pull_image(client, image_name)
    return client.containers.run(
        image, **kwargs
    )  # pyright: ignore[reportGeneralTypeIssues, reportReturnType]


def query_host_mounts(client: DockerClient, keys: list[Path]) -> dict[Path, Path]:
    return query_container_mounts(client, get_running_container_name(), keys)


def query_container_mounts(
    client: DockerClient, container_name: str, keys: list[Path]
) -> dict[Path, Path]:
    container = get_container(client, container_name)
    mounts = {}
    for mount in container.attrs["Mounts"]:
        dest = Path(mount["Destination"])
        if dest in keys:
            key = keys[keys.index(dest)]
            mounts[key] = Path(mount["Source"])
    return mounts


@retry
def exec_command(
    client: DockerClient, container_name: str, cmd: list[str]
) -> ExecResult:
    container = get_container(client, container_name)
    result = container.exec_run(cmd)
    if result.exit_code != 0:
        raise APIError(
            f"Unable to execute command {cmd} in {container.name}, "
            f"result: {result.output}, status: {result.exit_code}"
        )
    return result  # pyright: ignore[reportReturnType]
