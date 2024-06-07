from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from mirrors_qa_backend.db import gen_dbsession

DbSession = Annotated[Session, Depends(gen_dbsession)]
