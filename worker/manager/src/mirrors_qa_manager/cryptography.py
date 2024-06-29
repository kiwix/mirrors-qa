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
    private_key = serialization.load_pem_private_key(
        private_key_fpath.read_bytes(), password=None
    )  # pyright: ignore[reportReturnType, reportGeneralTypeIssues]

    fingerprint: Any = paramiko.RSAKey(  # pyright: ignore[reportUnknownMemberType]
        key=private_key  # pyright: ignore [reportGeneralTypeIssues, reportArgumentType]
    ).fingerprint  # pyright: ignore[reportGeneralTypeIssues]

    logger.info(f"Private key with fingerprint {fingerprint} is available and readable")
    return private_key  # pyright: ignore [reportGeneralTypeIssues, reportReturnType]


def get_signature(message: str, private_key: RSAPrivateKey) -> str:
    signed_message = private_key.sign(
        bytes(message, encoding="ascii"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signed_message).decode()


def generate_auth_message(worker_id: str, private_key: RSAPrivateKey) -> AuthMessage:
    body = f"{worker_id}:{datetime.datetime.now(datetime.UTC).isoformat()}"
    return AuthMessage(body=body, signature=get_signature(body, private_key))
