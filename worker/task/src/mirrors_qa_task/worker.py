import datetime
import time
from pathlib import Path
from urllib.parse import urlsplit

import humanfriendly
import requests
from requests.exceptions import RequestException

from mirrors_qa_task import Metrics, logger
from mirrors_qa_task.settings import Settings


def fmt(size: float) -> str:
    return humanfriendly.format_size(size, binary=True)


def get_download_metrics(
    url: str,
    *,
    timeout: int = Settings.REQUESTS_TIMEOUT_SECONDS,
    chunk_size: int = Settings.CHUNK_SIZE,
    retries: int = Settings.REQUESTS_MAX_RETRIES,
    interval: float = Settings.REQUESTS_RETRY_SECONDS,
) -> Metrics:
    attempt = 0
    url_components = urlsplit(url)
    filename = Path(url_components.path).name
    logger.info(f"Downloading {filename} from {url_components.netloc}")

    while True:
        attempt += 1
        started_on = datetime.datetime.now(datetime.UTC).isoformat()
        try:
            start = time.perf_counter()

            resp = requests.get(
                url=url,
                timeout=timeout,
                stream=True,
                headers={"User-Agent": Settings.USER_AGENT},
            )
            resp.raise_for_status()

            latency = resp.elapsed.total_seconds()
            size = int(resp.headers.get("Content-Length", "0"))
            downloaded = 0

            for data in resp.iter_content(chunk_size=chunk_size):
                downloaded += len(data)
                percentage = downloaded * 100 / size
                print(  # noqa: T201
                    f"\r{filename}: {percentage:.2f}%: "
                    f"{fmt(downloaded)}/{fmt(size)}",
                    flush=True,
                    end="",
                )
            print("\n")  # noqa: T201

            duration = time.perf_counter() - start
            speed = size / duration
            logger.info(
                f"Downloaded {fmt(size)} in {duration:.2f} seconds, "
                f"speed: {fmt(speed)}/s"
            )

            return Metrics(
                started_on=started_on,
                status="SUCCEEDED",
                error=None,
                latency=latency,
                download_size=size,
                duration=duration,
                speed=speed,
            )
        except RequestException as exc:
            if attempt <= retries:
                logger.warning(
                    "error while getting download metrics "
                    f"(attempt: {attempt}): {exc!s}"
                )
                time.sleep(interval * attempt)
                continue
            return Metrics(
                started_on=started_on,
                status="ERRORED",
                error=str(exc),
                latency=0.0,
                download_size=0,
                duration=0,
                speed=0.0,
            )
