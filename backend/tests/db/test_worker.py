from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.models import Country
from mirrors_qa_backend.db.worker import create_worker


def test_create_worker(dbsession: OrmSession, private_key: RSAPrivateKey):
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
        private_key=private_key,
    )
    assert new_worker.id == worker_id
    assert new_worker.pubkey_fingerprint != ""
    assert len(new_worker.countries) == len(countries)
    assert "BEGIN PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert "END PUBLIC KEY" in new_worker.pubkey_pkcs8
