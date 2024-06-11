from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db import Session, models


@pytest.fixture
def dbsession() -> Generator[OrmSession, None, None]:
    """
    Returns a session to an empty database.
    """
    with Session.begin() as session:
        # Ensure we are starting with an empty database
        models.Base.metadata.drop_all(bind=session.get_bind())
        models.Base.metadata.create_all(bind=session.get_bind())
        yield session
        session.rollback()
