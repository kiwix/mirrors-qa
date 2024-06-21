import subprocess
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import SelectBase, create_engine, func, select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import models
from mirrors_qa_backend.db.mirrors import create_or_update_mirror_status
from mirrors_qa_backend.extract import get_current_mirrors
from mirrors_qa_backend.settings import Settings

Session = sessionmaker(
    bind=create_engine(url=Settings.DATABASE_URL, echo=False),
    expire_on_commit=False,
)


def gen_dbsession() -> Generator[OrmSession, None, None]:
    """FastAPI's Depends() compatible helper to provide a begin DB Session"""
    with Session.begin() as session:
        yield session


def upgrade_db_schema():
    """Checks if Alembic schema has been applied to the DB"""
    src_dir = Path(__file__).parent.parent
    logger.info(f"Upgrading database schema with config in {src_dir}")
    subprocess.check_output(args=["alembic", "upgrade", "head"], cwd=src_dir)


def count_from_stmt(session: OrmSession, stmt: SelectBase) -> int:
    """Count all records returned by any statement `stmt` passed as parameter"""
    return session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()


def initialize_mirrors() -> None:
    with Session.begin() as session:
        current_mirrors = get_current_mirrors()
        nb_mirrors = count_from_stmt(session, select(models.Mirror))
        if nb_mirrors == 0:
            logger.info("No mirrors exist in database.")
            if not current_mirrors:
                logger.info(f"No mirrors were found on {Settings.MIRRORS_URL}")
                return
            result = create_or_update_mirror_status(session, current_mirrors)
            logger.info(
                f"Registered {result.nb_mirrors_added} mirrors "
                f"from {Settings.MIRRORS_URL}"
            )
        else:
            logger.info(f"Found {nb_mirrors} mirrors in database.")
            result = create_or_update_mirror_status(session, current_mirrors)
            logger.info(
                f"Added {result.nb_mirrors_added} mirrors. "
                f"Disabled {result.nb_mirrors_disabled} mirrors."
            )
