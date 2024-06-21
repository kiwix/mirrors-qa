from pathlib import Path

from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.models import Country
from mirrors_qa_backend.db.worker import create_worker


def test_create_worker(dbsession: OrmSession, tmp_path: Path, private_key_data: bytes):
    worker_id = "test"
    countries = [
        Country(code="ng", name="Nigeria"),
        Country(code="fr", name="France"),
    ]
    dbsession.add_all(countries)

    private_key_fpath = tmp_path / "key.pem"
    private_key_fpath.write_bytes(private_key_data)

    new_worker = create_worker(
        dbsession,
        worker_id=worker_id,
        country_codes=[country.code for country in countries],
        private_key_fpath=private_key_fpath,
    )
    assert new_worker.id == worker_id
    assert new_worker.pubkey_fingerprint != ""
    assert len(new_worker.countries) == len(countries)
    assert "BEGIN PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert "END PUBLIC KEY" in new_worker.pubkey_pkcs8
    assert private_key_fpath.exists()
    contents = private_key_fpath.read_text()
    assert "BEGIN PRIVATE KEY" in contents
    assert "END PRIVATE KEY" in contents
