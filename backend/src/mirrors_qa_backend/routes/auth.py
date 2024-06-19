import base64
import binascii
import datetime
from typing import Annotated

from fastapi import APIRouter, Header

from mirrors_qa_backend import cryptography, logger, schemas
from mirrors_qa_backend.db import worker
from mirrors_qa_backend.exceptions import PEMPublicKeyLoadError
from mirrors_qa_backend.routes import http_errors
from mirrors_qa_backend.routes.dependencies import DbSession
from mirrors_qa_backend.settings import Settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/authenticate")
def authenticate_worker(
    session: DbSession,
    x_sshauth_message: Annotated[
        str,
        Header(description="message (format): worker_id:timestamp (UTC ISO)"),
    ],
    x_sshauth_signature: Annotated[
        str, Header(description="signature, base64-encoded")
    ],
) -> schemas.Token:
    """Authenticate using signed message and generate tokens."""
    try:
        signature = base64.standard_b64decode(x_sshauth_signature)
    except binascii.Error as exc:
        raise http_errors.BadRequestError(
            "Invalid signature format (not base64)"
        ) from exc

    try:
        # decode message: worker_id:timestamp(UTC ISO)
        worker_id, timestamp_str = x_sshauth_message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except ValueError as exc:
        raise http_errors.BadRequestError("Invalid message format.") from exc

    # verify timestamp is less than MESSAGE_VALIDITY
    if (
        datetime.datetime.now(datetime.UTC) - timestamp
    ).total_seconds() > Settings.MESSAGE_VALIDITY:
        raise http_errors.UnauthorizedError(
            "Difference betweeen message time and server time is "
            f"greater than {Settings.MESSAGE_VALIDITY}s"
        )

    # verify worker with worker_id exists in database
    db_worker = worker.get_worker(session, worker_id)
    if db_worker is None:
        raise http_errors.UnauthorizedError()

    # verify signature of message with worker's public keys
    try:
        if not cryptography.verify_signed_message(
            bytes(db_worker.pubkey_pkcs8, encoding="ascii"),
            signature,
            bytes(x_sshauth_message, encoding="ascii"),
        ):
            raise http_errors.UnauthorizedError()
    except PEMPublicKeyLoadError as exc:
        logger.exception("error while verifying message using public key")
        raise http_errors.ForbiddenError("Unable to load public_key") from exc

    # generate tokens
    access_token = cryptography.generate_access_token(worker_id)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=datetime.timedelta(hours=Settings.TOKEN_EXPIRY).total_seconds(),
    )
