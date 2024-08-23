import base64
import datetime
from collections.abc import Generator
from typing import Any

import paramiko
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from faker import Faker
from faker.providers import DynamicProvider
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import schemas
from mirrors_qa_backend.cryptography import sign_message
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.country import create_country
from mirrors_qa_backend.db.models import Base, Country, Mirror, Region, Test, Worker
from mirrors_qa_backend.db.worker import update_worker_countries
from mirrors_qa_backend.enums import StatusEnum
from mirrors_qa_backend.serializer import serialize_mirror


@pytest.fixture(autouse=True)
def dbsession() -> Generator[OrmSession, None, None]:
    with Session.begin() as session:
        # Ensure we are starting with an empty database
        engine = session.get_bind()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield session
        session.rollback()


@pytest.fixture
def data_gen(faker: Faker) -> Faker:
    """Adds additional providers to faker.

    Registers test_country_code and test_status as providers.
    data_gen.test_status() returns a  status.
    data_gen.test_country_code() returns a country code.
    All other providers from Faker can be used accordingly.
    """
    test_status_provider = DynamicProvider(
        provider_name="test_status",
        elements=list(StatusEnum),
    )
    test_country_provider = DynamicProvider(
        provider_name="test_country_code",
        elements=[
            "ng",
            "fr",
            "us",
        ],
    )
    faker.add_provider(test_status_provider)
    faker.add_provider(test_country_provider)
    faker.seed_instance(123)

    return faker


@pytest.fixture
def tests(
    dbsession: OrmSession,
    data_gen: Faker,
    worker: Worker,
    request: Any,
) -> list[Test]:
    """Adds tests to the database using the num_test mark."""
    mark = request.node.get_closest_marker("num_tests")
    if mark and len(mark.args) > 0:
        num_tests = int(mark.args[0])
    else:
        num_tests = 10

    status = mark.kwargs.get("status", None)
    country_code = mark.kwargs.get("country_code", None)

    for _ in range(num_tests):
        test = Test(status=status if status else data_gen.test_status())
        selected_country_code = (
            country_code if country_code else data_gen.test_country_code()
        )
        test.country_code = selected_country_code
        test.worker = worker
        dbsession.add(test)

    dbsession.flush()

    return worker.tests


@pytest.fixture(scope="session")
def private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def public_key_data(private_key: RSAPrivateKey) -> bytes:
    """Serialize public key using PEM format."""
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


@pytest.fixture(scope="session")
def public_key(public_key_data: bytes) -> RSAPublicKey:
    """Create public key using PEM format."""
    return serialization.load_pem_public_key(  # pyright: ignore[reportReturnType]
        public_key_data
    )


@pytest.fixture
def worker(public_key: RSAPublicKey, dbsession: OrmSession) -> Worker:
    pubkey_pkcs8 = public_key.public_bytes(
        serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode(encoding="ascii")

    worker = Worker(
        id="test",
        pubkey_fingerprint=paramiko.RSAKey(key=public_key).fingerprint,  # type: ignore
        pubkey_pkcs8=pubkey_pkcs8,
    )
    dbsession.add(worker)

    country_data = {"fr": "France", "ca": "Canada"}
    for country_code, country_name in country_data.items():
        create_country(dbsession, country_code=country_code, country_name=country_name)
    update_worker_countries(dbsession, worker, list(country_data.keys()))

    return worker


@pytest.fixture
def auth_message(worker: Worker) -> str:
    return f"{worker.id}:{datetime.datetime.now(datetime.UTC).isoformat()}"


@pytest.fixture
def x_sshauth_signature(private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message(private_key, bytes(auth_message, encoding="ascii"))
    return base64.b64encode(signature).decode()


@pytest.fixture
def db_mirror(dbsession: OrmSession) -> Mirror:
    mirror = Mirror(
        id="mirror-sites-in.mblibrary.info",
        base_url="https://mirror-sites-in.mblibrary.info/mirror-sites/download.kiwix.org/",
        enabled=True,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
    )
    dbsession.add(mirror)
    return mirror


@pytest.fixture
def schema_mirror(db_mirror: Mirror) -> schemas.Mirror:
    return serialize_mirror(db_mirror)


@pytest.fixture
def new_schema_mirror() -> schemas.Mirror:
    return schemas.Mirror(
        id="mirrors.dotsrc.org",
        base_url="https://mirrors.dotsrc.org/kiwix/",
        enabled=True,
        region=None,
        asn=None,
        score=None,
        latitude=None,
        longitude=None,
        country_only=None,
        region_only=None,
        as_only=None,
        other_countries=None,
    )


@pytest.fixture
def africa_region(dbsession: OrmSession) -> Region:
    """Set up a region in Africa and add some default countries."""
    region = Region(code="af", name="Africa")
    countries = [
        Country(code="ng", name="Nigeria"),
    ]
    region.countries = countries
    dbsession.add(region)
    return region


@pytest.fixture
def europe_region(dbsession: OrmSession) -> Region:
    """Set up a region in Europe and add some default countries."""
    region = Region(code="eu", name="Europe")
    countries = [
        Country(code="fr", name="France"),
    ]
    region.countries = countries
    dbsession.add(region)
    return region


@pytest.fixture
def asia_region(dbsession: OrmSession) -> Region:
    """Set up a region in Asia and add some default countries."""
    region = Region(code="as", name="Asia")
    countries = [
        Country(code="jp", name="Japan"),
    ]
    region.countries = countries
    dbsession.add(region)
    return region
