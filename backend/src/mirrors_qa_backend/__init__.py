import logging

from mirrors_qa_backend.settings import Settings

logger = logging.getLogger("backend")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if Settings.debug else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
