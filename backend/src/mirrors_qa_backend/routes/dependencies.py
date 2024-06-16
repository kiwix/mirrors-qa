from typing import Annotated

import jwt
from fastapi import Depends, Header
from jwt import exceptions as jwt_exceptions
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from mirrors_qa_backend import db, schemas
from mirrors_qa_backend.db import gen_dbsession, models
from mirrors_qa_backend.routes import http_errors
from mirrors_qa_backend.settings import Settings

DbSession = Annotated[Session, Depends(gen_dbsession)]


def verify_authorization_header(
    authorization: Annotated[str | None, Header()] = None
) -> schemas.JWTClaims | None:
    if authorization is None:
        return None

    header_parts = authorization.split(" ")
    if len(header_parts) != 2 or header_parts[0] != "Bearer":  # noqa
        raise http_errors.UnauthorizedError

    token = header_parts[1]
    try:
        claims = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
    except jwt_exceptions.ExpiredSignatureError:
        raise http_errors.UnauthorizedError("Token has expired.") from None
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
        raise http_errors.UnauthorizedError from None

    try:
        claims = schemas.JWTClaims(**claims)
    except PydanticValidationError:
        raise http_errors.UnauthorizedError from None
    return claims


def get_current_worker(
    session: DbSession,
    claims: Annotated[schemas.JWTClaims | None, Depends(verify_authorization_header)],
) -> models.Worker:
    if claims is None:
        raise http_errors.UnauthorizedError

    # At this point, we know that the JWT is all OK and we can
    # trust the data in it. We extract the worker_id from the claims
    worker = db.worker.get_worker(session, claims.subject)
    if worker is None:
        raise http_errors.UnauthorizedError
    return worker


CurrentWorker = Annotated[models.Worker, Depends(get_current_worker)]
