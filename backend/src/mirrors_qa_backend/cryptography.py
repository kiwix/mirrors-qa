# pyright: strict, reportGeneralTypeIssues=false
import datetime

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from mirrors_qa_backend.exceptions import PEMPublicKeyLoadError
from mirrors_qa_backend.settings import Settings


def verify_signed_message(public_key: bytes, signature: bytes, message: bytes) -> bool:
    try:
        pem_public_key = serialization.load_pem_public_key(public_key)
    except Exception as exc:
        raise PEMPublicKeyLoadError from exc

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


def generate_access_token(worker_id: str) -> str:
    issue_time = datetime.datetime.now(datetime.UTC)
    expire_time = issue_time + datetime.timedelta(hours=Settings.TOKEN_EXPIRY)
    payload = {
        "iss": "mirrors-qa-backend",  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        # "jti": uuid.uuid4(),  # JWT ID
        "subject": worker_id,  # user payload (username, scope)
    }
    return jwt.encode(payload, key=Settings.JWT_SECRET, algorithm="HS256")
