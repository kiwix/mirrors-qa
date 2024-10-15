import base64
import binascii
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from mirrors_qa_backend import logger
from mirrors_qa_backend.cryptography import verify_signed_message
from mirrors_qa_backend.db import gen_dbsession
from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.worker import get_worker
from mirrors_qa_backend.exceptions import PEMPublicKeyLoadError
from mirrors_qa_backend.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
)
from mirrors_qa_backend.schemas import Token
from mirrors_qa_backend.settings.api import APISettings
from mirrors_qa_backend.tokens import generate_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/authenticate")
def authenticate_worker(
    session: Annotated[Session, Depends(gen_dbsession)],
    x_sshauth_message: Annotated[
        str,
        Header(description="message (format): worker_id:timestamp (UTC ISO)"),
    ],
    x_sshauth_signature: Annotated[
        str, Header(description="signature, base64-encoded")
    ],
) -> Token:
    """Authenticate using signed message and generate tokens."""
    try:
        signature = base64.standard_b64decode(x_sshauth_signature)
    except binascii.Error as exc:
        raise BadRequestError("Invalid signature format (not base64)") from exc

    try:
        # decode message: worker_id:timestamp(UTC ISO)
        worker_id, timestamp_str = x_sshauth_message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except ValueError as exc:
        raise BadRequestError("Invalid message format.") from exc

    # verify timestamp is less than MESSAGE_VALIDITY
    if (
        datetime.datetime.now(datetime.UTC) - timestamp
    ).total_seconds() > APISettings.MESSAGE_VALIDITY_SECONDS:
        raise UnauthorizedError(
            "Difference betweeen message time and server time is "
            f"greater than {APISettings.MESSAGE_VALIDITY_SECONDS}s"
        )

    # verify worker with worker_id exists in database
    try:
        db_worker = get_worker(session, worker_id)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    # verify signature of message with worker's public keys
    try:
        if not verify_signed_message(
            bytes(db_worker.pubkey_pkcs8, encoding="ascii"),
            signature,
            bytes(x_sshauth_message, encoding="ascii"),
        ):
            raise UnauthorizedError()
    except PEMPublicKeyLoadError as exc:
        logger.exception("error while verifying message using public key")
        raise ForbiddenError("Unable to load public_key") from exc

    # generate tokens
    access_token = generate_access_token(worker_id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=APISettings.TOKEN_EXPIRY_SECONDS,
    )
