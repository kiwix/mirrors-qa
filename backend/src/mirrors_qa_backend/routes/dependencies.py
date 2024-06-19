from typing import Annotated

import jwt
from fastapi import Depends, Header, Path
from jwt import exceptions as jwt_exceptions
from pydantic import UUID4
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from mirrors_qa_backend import schemas
from mirrors_qa_backend.db import gen_dbsession, models, tests, worker
from mirrors_qa_backend.routes import http_errors
from mirrors_qa_backend.settings import Settings

DbSession = Annotated[Session, Depends(gen_dbsession)]


def get_current_worker(
    session: DbSession,
    authorization: Annotated[str, Header()] = "",
) -> models.Worker:
    header_parts = authorization.split(" ")
    if len(header_parts) != 2 or header_parts[0] != "Bearer":  # noqa: PLR2004
        raise http_errors.UnauthorizedError()

    token = header_parts[1]
    try:
        jwt_claims = jwt.decode(token, Settings.JWT_SECRET, algorithms=["HS256"])
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise http_errors.UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise http_errors.UnauthorizedError from exc

    try:
        claims = schemas.JWTClaims(**jwt_claims)
    except PydanticValidationError as exc:
        raise http_errors.UnauthorizedError from exc

    # At this point, we know that the JWT is all OK and we can
    # trust the data in it. We extract the worker_id from the claims
    db_worker = worker.get_worker(session, claims.subject)
    if db_worker is None:
        raise http_errors.UnauthorizedError()
    return db_worker


CurrentWorker = Annotated[models.Worker, Depends(get_current_worker)]


def get_test(session: DbSession, test_id: Annotated[UUID4, Path()]) -> models.Test:
    """Fetches the test specified in the request."""
    test = tests.get_test(session, test_id)
    if test is None:
        raise http_errors.NotFoundError(f"Test with id {test_id} does not exist.")
    return test


GetTest = Annotated[models.Test, Depends(get_test)]


def verify_worker_owns_test(worker: CurrentWorker, test: GetTest):
    if test.worker_id != worker.id:
        raise http_errors.UnauthorizedError("Insufficient privileges to update test.")
