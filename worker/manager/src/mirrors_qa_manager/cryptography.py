import base64
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import paramiko
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from mirrors_qa_manager import logger


@dataclass
class AuthMessage:
    body: str
    signature: str


def load_private_key_from_path(private_key_fpath: Path) -> RSAPrivateKey:
    with private_key_fpath.open("rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), password=None
        )  # pyright: ignore[reportReturnType, reportGeneralTypeIssues]

        fingerprint: Any = paramiko.RSAKey(  # pyright: ignore[reportUnknownMemberType]
            key=private_key  # pyright: ignore [reportGeneralTypeIssues, reportArgumentType]
        ).fingerprint  # pyright: ignore[reportGeneralTypeIssues]

        logger.info(
            f"Private key with fingerprint {fingerprint} is available and readable"
        )
        return (
            private_key  # pyright: ignore [reportGeneralTypeIssues, reportReturnType]
        )


def sign_message(private_key: RSAPrivateKey, message: bytes) -> bytes:
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def generate_auth_message(private_key: RSAPrivateKey, worker_id: str) -> AuthMessage:
    body = f"{worker_id}:{datetime.datetime.now(datetime.UTC).isoformat()}"
    signature = base64.b64encode(
        sign_message(private_key, bytes(body, encoding="ascii"))
    ).decode()

    return AuthMessage(body=body, signature=signature)
