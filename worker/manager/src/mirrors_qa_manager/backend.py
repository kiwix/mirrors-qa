import datetime
from dataclasses import dataclass
from typing import Any

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from mirrors_qa_manager import logger
from mirrors_qa_manager.cryptography import generate_auth_message
from mirrors_qa_manager.settings import Settings


@dataclass
class AuthCredentials:
    access_token: str
    expires_in: datetime.datetime


def authenticate(private_key: RSAPrivateKey, worker_id: str) -> AuthCredentials:
    logger.info("Authenticating with Backend API")
    auth_message = generate_auth_message(private_key, worker_id)
    data = query_api(
        "/auth/authenticate",
        "POST",
        headers={
            "Content-Type": "application/json",
            "X-SSHAuth-Message": auth_message.body,
            "X-SSHAuth-Signature": auth_message.signature,
        },
    )
    return AuthCredentials(
        access_token=data["access_token"],
        expires_in=datetime.datetime.fromtimestamp(data["expires_in"]),
    )


def query_api(
    endpoint: str,
    method: str = "get",
    *,
    headers: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    req_headers = {}

    req_headers.update(  # pyright: ignore[reportUnknownMemberType]
        headers if headers else {}
    )
    if endpoint:
        url = f"{Settings.BACKEND_API_URI}/{endpoint}"
    else:
        url = Settings.BACKEND_API_URI

    resp: Any = getattr(  # pyright: ignore[reportCallIssue]
        requests, method.lower(), "get"
    )(  # pyright: ignore[reportGeneralTypeIssues]
        url, headers=req_headers, json=payload
    )
    resp.raise_for_status()
    return resp.json()
