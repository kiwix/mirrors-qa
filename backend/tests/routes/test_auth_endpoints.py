import base64
import datetime

import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from fastapi import status
from fastapi.testclient import TestClient

from mirrors_qa_backend.cryptography import sign_message
from mirrors_qa_backend.db import models


@pytest.mark.parametrize(
    ["datetime_str", "expected_status", "expected_response_contents"],
    [
        (
            datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC).isoformat(),
            status.HTTP_401_UNAUTHORIZED,
            [],
        ),
        (
            "hello",
            status.HTTP_400_BAD_REQUEST,
            [],
        ),
        (
            datetime.datetime.now(datetime.UTC).isoformat(),
            status.HTTP_200_OK,
            ["access_token", "token_type", "expires_in"],
        ),
    ],
)
def test_authenticate_worker(
    client: TestClient,
    worker: models.Worker,
    private_key: RSAPrivateKey,
    datetime_str: str,
    expected_status: int,
    expected_response_contents: list[str],
):
    message = f"{worker.id}:{datetime_str}"
    signature = sign_message(private_key, bytes(message, encoding="ascii"))
    x_sshauth_signature = base64.b64encode(signature).decode()
    response = client.post(
        "/auth/authenticate",
        headers={
            "Content-type": "application/json",
            "X-SSHAuth-Message": message,
            "X-SSHAuth-Signature": x_sshauth_signature,
        },
    )
    assert response.status_code == expected_status
    data = response.text
    for content in expected_response_contents:
        assert content in data
