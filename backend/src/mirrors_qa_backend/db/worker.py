from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import models


def get_worker(session: OrmSession, worker_id: str) -> models.Worker | None:
    return session.scalars(
        select(models.Worker).where(models.Worker.id == worker_id)
    ).one_or_none()
