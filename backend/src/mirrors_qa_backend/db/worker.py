import datetime

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.cryptography import (
    get_public_key_fingerprint,
    serialize_public_key,
)
from mirrors_qa_backend.db.country import get_countries
from mirrors_qa_backend.db.exceptions import (
    DuplicatePrimaryKeyError,
    RecordDoesNotExistError,
)
from mirrors_qa_backend.db.models import Worker


def get_worker_or_none(session: OrmSession, worker_id: str) -> Worker | None:
    return session.scalars(select(Worker).where(Worker.id == worker_id)).one_or_none()


def get_worker(session: OrmSession, worker_id: str) -> Worker:
    if worker := get_worker_or_none(session, worker_id):
        return worker
    raise RecordDoesNotExistError(f"Worker with id: {worker_id} does not exist.")


def create_worker(
    session: OrmSession,
    worker_id: str,
    country_codes: list[str],
    public_key: RSAPublicKey,
) -> Worker:
    """Creates a worker using RSA public key."""
    if get_worker_or_none(session, worker_id) is not None:
        raise DuplicatePrimaryKeyError(f"A worker with id {worker_id} already exists.")

    public_key_pkcs8 = serialize_public_key(public_key).decode(encoding="ascii")
    worker = Worker(
        id=worker_id,
        pubkey_pkcs8=public_key_pkcs8,
        pubkey_fingerprint=get_public_key_fingerprint(public_key),
    )

    update_worker_countries(session, worker, country_codes)

    return worker


def update_worker_countries(
    session: OrmSession, worker: Worker, country_codes: list[str]
) -> Worker:
    worker.countries = get_countries(session, country_codes)
    session.add(worker)
    return worker


def update_worker(
    session: OrmSession, worker_id: str, country_codes: list[str]
) -> Worker:
    worker = get_worker(session, worker_id)
    return update_worker_countries(session, worker, country_codes)


def get_workers_last_seen_in_range(
    session: OrmSession, begin: datetime.datetime, end: datetime.datetime
) -> list[Worker]:
    """Get workers whose last_seen_on falls between begin and end dates"""
    return list(
        session.scalars(
            select(Worker).where(
                Worker.last_seen_on.between(begin, end),
            )
        ).all()
    )


def get_idle_workers(session: OrmSession, interval: datetime.timedelta) -> list[Worker]:
    end = datetime.datetime.now() - interval
    begin = datetime.datetime.fromtimestamp(0)
    return get_workers_last_seen_in_range(session, begin, end)


def get_active_workers(
    session: OrmSession, interval: datetime.timedelta
) -> list[Worker]:
    end = datetime.datetime.now()
    begin = end - interval
    return get_workers_last_seen_in_range(session, begin, end)


def update_worker_last_seen(session: OrmSession, worker: Worker) -> Worker:
    worker.last_seen_on = datetime.datetime.now()
    session.add(worker)
    return worker
