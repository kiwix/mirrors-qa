import logging
from dataclasses import dataclass

from mirrors_qa_task.settings import Settings

logger = logging.getLogger("task")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if Settings.DEBUG else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)


@dataclass
class Metrics:
    started_on: str  # ISO formatted datetime
    status: str  # SUCCEEDED|ERRORED
    error: str | None  # error reason
    latency: float  # average ping result to netloc of URL
    download_size: int  # number of bytes of downloaded file
    duration: float  # number of seconds to complete download
    speed: float  # bytes per second of the download
