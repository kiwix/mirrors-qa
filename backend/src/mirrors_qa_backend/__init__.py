import logging
import os

logger = logging.getLogger("backend")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if bool(os.getenv("DEBUG")) else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
