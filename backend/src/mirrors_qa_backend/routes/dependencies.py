from typing import Annotated

import jwt
from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import exceptions as jwt_exceptions
from pydantic import UUID4
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from mirrors_qa_backend import schemas
from mirrors_qa_backend.db import gen_dbsession, models
from mirrors_qa_backend.db.tests import get_test as db_get_test
from mirrors_qa_backend.db.worker import get_worker
from mirrors_qa_backend.routes.http_errors import NotFoundError, UnauthorizedError
from mirrors_qa_backend.settings.api import APISettings

DbSession = Annotated[Session, Depends(gen_dbsession)]

security = HTTPBearer(description="Access Token")
AuthorizationCredentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def get_current_worker(
    session: DbSession,
    authorization: AuthorizationCredentials,
) -> models.Worker:
    token = authorization.credentials
    try:
        jwt_claims = jwt.decode(token, APISettings.JWT_SECRET, algorithms=["HS256"])
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise UnauthorizedError from exc

    try:
        claims = schemas.JWTClaims(**jwt_claims)
    except PydanticValidationError as exc:
        raise UnauthorizedError from exc

    # At this point, we know that the JWT is all OK and we can
    # trust the data in it. We extract the worker_id from the claims
    db_worker = get_worker(session, claims.subject)
    if db_worker is None:
        raise UnauthorizedError()
    return db_worker


CurrentWorker = Annotated[models.Worker, Depends(get_current_worker)]


def get_test(session: DbSession, test_id: Annotated[UUID4, Path()]) -> models.Test:
    """Fetches the test specified in the request."""
    test = db_get_test(session, test_id)
    if test is None:
        raise NotFoundError(f"Test with id {test_id} does not exist.")
    return test


RetrievedTest = Annotated[models.Test, Depends(get_test)]


def verify_worker_owns_test(worker: CurrentWorker, test: RetrievedTest):
    if test.worker_id != worker.id:
        raise UnauthorizedError("Insufficient privileges to update test.")
