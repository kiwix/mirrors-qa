import base64
import binascii
import datetime
from typing import Annotated

from fastapi import APIRouter, Header

from mirrors_qa_backend import cryptography, db, logger, schemas
from mirrors_qa_backend.routes import DbSession, http_errors
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
        str, Header(description="bas64 string of signature")
    ],
) -> schemas.Token:
    """Authenticate using signed message and generate tokens."""
    try:
        signature = base64.standard_b64decode(x_sshauth_signature)
    except binascii.Error:
        raise http_errors.BadRequestError(
            "Invalid signature format (not base64)"
        ) from None

    try:
        # decode message: worker_id:timestamp(UTC ISO)
        worker_id, timestamp_str = x_sshauth_message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except ValueError:
        raise http_errors.BadRequestError("Invalid message format.") from None

    # verify timestamp is less than MESSAGE_VALIDITY
    if (
        datetime.datetime.now(datetime.UTC) - timestamp
    ).total_seconds() > Settings.MESSAGE_VALIDITY:
        raise http_errors.UnauthorizedError(
            "Difference betweeen message time and server time is "
            f"greater than {Settings.MESSAGE_VALIDITY}s"
        )

    # verify worker with worker_id exists in database
    worker = db.worker.get_worker(session, worker_id)
    if worker is None:
        raise http_errors.UnauthorizedError

    # verify signature of message with worker's public keys
    try:
        cryptography.verify_signed_message(
            bytes(worker.pubkey_pkcs8, encoding="ascii"),
            signature,
            bytes(x_sshauth_message, encoding="ascii"),
        )
    except Exception:
        logger.exception("error while verifying message using public key")
        raise http_errors.ServerError from None

    # generate tokens
    access_token = cryptography.generate_access_token(worker_id)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=datetime.timedelta(hours=Settings.TOKEN_EXPIRY).total_seconds(),
    )
