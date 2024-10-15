import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status as status_codes
from sqlalchemy import select
from sqlalchemy.orm import Session

from mirrors_qa_backend.db import count_from_stmt, gen_dbsession
from mirrors_qa_backend.db.models import Test
from mirrors_qa_backend.enums import StatusEnum
from mirrors_qa_backend.schemas import HealthStatus
from mirrors_qa_backend.settings.api import APISettings

router = APIRouter(prefix="/health-check", tags=["health-check"])


@router.get(
    "",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {
            "description": "Status of monitored parts of mirrors-qa"
        }
    },
)
def heatlh_status(session: Annotated[Session, Depends(gen_dbsession)]) -> HealthStatus:
    test_received_after = datetime.datetime.now() - datetime.timedelta(
        seconds=APISettings.UNHEALTHY_NO_TESTS_DURATION_SECONDS
    )

    nb_recent_tests_received = count_from_stmt(
        session,
        select(Test).where(
            Test.status == StatusEnum.SUCCEEDED,
            (Test.started_on >= test_received_after),
        ),
    )

    return HealthStatus(receiving_tests=nb_recent_tests_received > 0)
