from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import gen_dbsession
from mirrors_qa_backend.main import app


@pytest.fixture
def client(dbsession: OrmSession) -> TestClient:
    def test_dbsession() -> Generator[OrmSession, None, None]:
        yield dbsession

    # Replace the  database session with the test dbsession
    app.dependency_overrides[gen_dbsession] = test_dbsession

    return TestClient(app=app)
