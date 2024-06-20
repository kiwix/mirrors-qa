# ruff: noqa: DTZ005, DTZ001
import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import cryptography
from mirrors_qa_backend.db import country, models
from mirrors_qa_backend.db.exceptions import DuplicatePrimaryKeyError


def get_worker(session: OrmSession, worker_id: str) -> models.Worker | None:
    return session.scalars(
        select(models.Worker).where(models.Worker.id == worker_id)
    ).one_or_none()


def create_worker(
    session: OrmSession,
    worker_id: str,
    countries: list[str],
    private_key_filename: str | Path | None = None,
) -> models.Worker:
    """Creates a worker and writes private key contents to private_key_filename.

    If no private_key_filename is provided, defaults to {worker_id}.pem.
    """
    if get_worker(session, worker_id) is not None:
        raise DuplicatePrimaryKeyError(
            f"A worker with id {worker_id!r} already exists."
        )

    if private_key_filename is None:
        private_key_filename = f"{worker_id}.pem"

    private_key = cryptography.generate_private_key()
    public_key = cryptography.generate_public_key(private_key)
    public_key_pkcs8 = cryptography.serialize_public_key(public_key).decode(
        encoding="ascii"
    )
    with open(private_key_filename, "wb") as fp:
        fp.write(cryptography.serialize_private_key(private_key))

    worker = models.Worker(
        id=worker_id,
        pubkey_pkcs8=public_key_pkcs8,
        pubkey_fingerprint=cryptography.get_public_key_fingerprint(public_key),
    )
    session.add(worker)

    for db_country in country.get_countries_by_name(session, *countries):
        db_country.worker_id = worker_id
        session.add(db_country)

    return worker


def get_workers_last_seen_in_range(
    session: OrmSession, begin: datetime.datetime, end: datetime.datetime
) -> list[models.Worker]:
    """Get workers whose last_seen_on falls between begin and end dates"""
    return list(
        session.scalars(
            select(models.Worker).where(
                models.Worker.last_seen_on.between(begin, end),
            )
        ).all()
    )


def get_idle_workers(
    session: OrmSession, interval: datetime.timedelta
) -> list[models.Worker]:
    end = datetime.datetime.now() - interval
    begin = datetime.datetime(1970, 1, 1)
    return get_workers_last_seen_in_range(session, begin, end)


def get_active_workers(
    session: OrmSession, interval: datetime.timedelta
) -> list[models.Worker]:
    end = datetime.datetime.now()
    begin = end - interval
    return get_workers_last_seen_in_range(session, begin, end)


def update_worker_last_seen(
    session: OrmSession, worker: models.Worker
) -> models.Worker:
    worker.last_seen_on = datetime.datetime.now()
    session.add(worker)
    return worker
