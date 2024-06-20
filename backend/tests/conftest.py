import base64
import datetime
from collections.abc import Generator
from typing import Any

import paramiko
import pycountry
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from faker import Faker
from faker.providers import DynamicProvider
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.cryptography import sign_message
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.country import get_country_or_none
from mirrors_qa_backend.db.models import Base, Country, Test, Worker
from mirrors_qa_backend.enums import StatusEnum


@pytest.fixture
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
    dbsession: OrmSession, data_gen: Faker, worker: Worker, request: Any
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
        if country := get_country_or_none(dbsession, selected_country_code):
            test.country = country
        else:
            country = Country(
                code=selected_country_code.lower(),
                name=pycountry.countries.get(
                    alpha_2=selected_country_code
                ).name,  # pyright: ignore [reportOptionalMemberAccess]
            )
            dbsession.add(country)
            test.country = country

        test.worker = worker
        dbsession.add(test)

    dbsession.flush()

    return worker.tests


@pytest.fixture(scope="session")
def private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def public_key(private_key: RSAPrivateKey) -> RSAPublicKey:
    return private_key.public_key()


@pytest.fixture(scope="session")
def private_key_bytes(private_key: RSAPrivateKey) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
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
    return worker


@pytest.fixture
def auth_message(worker: Worker) -> str:
    return f"{worker.id}:{datetime.datetime.now(datetime.UTC).isoformat()}"


@pytest.fixture
def x_sshauth_signature(private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message(private_key, bytes(auth_message, encoding="ascii"))
    return base64.b64encode(signature).decode()
