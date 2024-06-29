import logging

from mirrors_qa_task.settings import Settings

logger = logging.getLogger("task")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if Settings.DEBUG else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
