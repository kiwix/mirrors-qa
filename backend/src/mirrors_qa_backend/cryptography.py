# pyright: strict, reportGeneralTypeIssues=false
import datetime

import jwt
import paramiko
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from mirrors_qa_backend.exceptions import PEMPublicKeyLoadError
from mirrors_qa_backend.settings import Settings


def verify_signed_message(public_key: bytes, signature: bytes, message: bytes) -> bool:
    try:
        pem_public_key = serialization.load_pem_public_key(public_key)
    except Exception as exc:
        raise PEMPublicKeyLoadError("Unable to load public key") from exc

    try:
        pem_public_key.verify(  # pyright: ignore
            signature,
            message,
            padding.PSS(  # pyright: ignore
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),  # pyright: ignore
        )
    except InvalidSignature:
        return False
    return True


def sign_message(private_key: RSAPrivateKey, message: bytes) -> bytes:
    # TODO: Move to worker codebase. Needed for testing purposes here only
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def generate_private_key(key_size: int = 2048) -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=key_size)


def serialize_private_key(private_key: RSAPrivateKey) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def generate_public_key(private_key: RSAPrivateKey) -> RSAPublicKey:
    return private_key.public_key()


def serialize_public_key(public_key: RSAPublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_public_key_fingerprint(public_key: RSAPublicKey) -> str:
    """Compute the SHA256 fingerprint of the public key"""
    return paramiko.RSAKey(
        key=public_key
    ).fingerprint  # pyright: ignore[reportUnknownMemberType, UnknownVariableType]


def generate_access_token(worker_id: str) -> str:
    issue_time = datetime.datetime.now(datetime.UTC)
    expire_time = issue_time + datetime.timedelta(hours=Settings.TOKEN_EXPIRY)
    payload = {
        "iss": "mirrors-qa-backend",  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": worker_id,
    }
    return jwt.encode(payload, key=Settings.JWT_SECRET, algorithm="HS256")
