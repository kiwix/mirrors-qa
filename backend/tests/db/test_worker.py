from pathlib import Path

from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import models, worker


def test_create_worker(dbsession: OrmSession, tmp_path: Path):
    worker_id = "test"
    countries = [
        models.Country(code="ng", name="Nigeria"),
        models.Country(code="fr", name="France"),
    ]
    dbsession.add_all(countries)

    private_key_filename = tmp_path / "key.pem"
    new_worker = worker.create_worker(
        dbsession,
        worker_id=worker_id,
        countries=[country.name for country in countries],
        private_key_filename=private_key_filename,
    )
    assert new_worker.id == worker_id
    assert new_worker.pubkey_fingerprint != ""
    assert len(new_worker.countries) == len(countries)
    assert "BEGIN PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert "END PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert private_key_filename.exists()
    contents = private_key_filename.read_text()
    assert "BEGIN PRIVATE KEY" in contents
    assert "END PRIVATE KEY" in contents
