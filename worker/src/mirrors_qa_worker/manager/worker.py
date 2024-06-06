import os
import time

from mirrors_qa_worker import logger


class WorkerManager:
    """Manager responsible for creating tasks"""

    # number of seconds between each poll
    sleep_interval = int(os.getenv("SLEEP_INTERVAL", 180))  # noqa

    def __init__(self, worker_id: str) -> None:

        self.worker_id = worker_id

    def fetch_tasks(self) -> None:
        logger.debug("Fetching tasks from backend API")

    def sleep(self) -> None:
        time.sleep(self.sleep_interval)

    def run(self) -> None:
        logger.info("Starting worker manager.")
        while True:
            self.fetch_tasks()
            self.sleep()
