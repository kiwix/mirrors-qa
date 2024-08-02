import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.models import Country, Worker
from mirrors_qa_backend.db.worker import create_worker, get_worker


def test_create_worker(dbsession: OrmSession, public_key: RSAPublicKey):
    worker_id = "test"
    countries = [
        Country(code="ng", name="Nigeria"),
        Country(code="fr", name="France"),
    ]
    dbsession.add_all(countries)

    new_worker = create_worker(
        dbsession,
        worker_id=worker_id,
        country_codes=[country.code for country in countries],
        public_key=public_key,
    )
    assert new_worker.id == worker_id
    assert new_worker.pubkey_fingerprint != ""
    assert len(new_worker.countries) == len(countries)
    assert "BEGIN PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert "END PUBLIC KEY" in new_worker.pubkey_pkcs8


def test_worker_does_not_exist(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_worker(dbsession, "does not exist")


def test_get_worker(dbsession: OrmSession, worker: Worker):
    assert get_worker(dbsession, worker.id).id == worker.id
