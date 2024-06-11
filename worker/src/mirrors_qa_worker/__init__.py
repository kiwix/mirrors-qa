import logging

from mirrors_qa_worker.settings import Settings

logger = logging.getLogger("worker")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if Settings.debug else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
