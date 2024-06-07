import time

from mirrors_qa_worker import logger
from mirrors_qa_worker.settings import Settings


class WorkerManager:
    """Manager responsible for creating tasks"""

    def __init__(self, worker_id: str) -> None:

        self.worker_id = worker_id

    def fetch_tasks(self) -> None:
        logger.debug("Fetching tasks from backend API")

    def sleep(self) -> None:
        time.sleep(Settings.sleep_interval)

    def run(self) -> None:
        logger.info("Starting worker manager.")
        while True:
            self.fetch_tasks()
            self.sleep()
