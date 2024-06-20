from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import status as status_codes

from mirrors_qa_backend import schemas
from mirrors_qa_backend.db.tests import create_or_update_test
from mirrors_qa_backend.db.tests import list_tests as db_list_tests
from mirrors_qa_backend.db.worker import update_worker_last_seen
from mirrors_qa_backend.enums import SortDirectionEnum, StatusEnum, TestSortColumnEnum
from mirrors_qa_backend.routes.dependencies import (
    CurrentWorker,
    DbSession,
    RetrievedTest,
    verify_worker_owns_test,
)
from mirrors_qa_backend.schemas import Test, TestsList, calculate_pagination_metadata
from mirrors_qa_backend.serializer import serialize_test
from mirrors_qa_backend.settings import Settings

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get(
    "",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {"description": "Returns the list of tests."},
    },
)
def list_tests(
    session: DbSession,
    worker_id: Annotated[str | None, Query()] = None,
    country_code: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    status: Annotated[list[StatusEnum] | None, Query()] = None,
    page_size: Annotated[
        int, Query(le=Settings.MAX_PAGE_SIZE, ge=1)
    ] = Settings.MAX_PAGE_SIZE,
    page_num: Annotated[int, Query(ge=1)] = 1,
    sort_by: Annotated[TestSortColumnEnum, Query()] = TestSortColumnEnum.requested_on,
    order: Annotated[SortDirectionEnum, Query()] = SortDirectionEnum.asc,
) -> TestsList:
    result = db_list_tests(
        session,
        worker_id=worker_id,
        country_code=country_code,
        statuses=status,
        page_size=page_size,
        page_num=page_num,
        sort_column=sort_by,
        sort_direction=order,
    )
    return schemas.TestsList(
        tests=[serialize_test(test) for test in result.tests],
        metadata=calculate_pagination_metadata(
            result.nb_tests, page_size=page_size, current_page=page_num
        ),
    )


@router.get(
    "/{test_id}",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {"description": "Returns the details of a test."},
        status_codes.HTTP_404_NOT_FOUND: {
            "description": "Test with id does not exist."
        },
    },
)
def get_test(test: RetrievedTest) -> Test:
    return serialize_test(test)


@router.patch(
    "/{test_id}",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {"description": "Update the details of a test."},
    },
    dependencies=[Depends(verify_worker_owns_test)],
)
def update_test(
    session: DbSession,
    current_worker: CurrentWorker,
    test: RetrievedTest,
    update: schemas.UpdateTestModel,
) -> Test:
    data = update.model_dump(exclude_unset=True)
    body = schemas.UpdateTestModel().model_copy(update=data)
    updated_test = create_or_update_test(
        session,
        test_id=test.id,
        worker_id=current_worker.id,
        status=body.status,
        error=body.error,
        ip_address=body.ip_address,
        asn=body.asn,
        country_code=body.country_code,
        location=body.location,
        latency=body.latency,
        download_size=body.download_size,
        duration=body.duration,
        speed=body.speed,
    )
    update_worker_last_seen(session, current_worker)
    return serialize_test(updated_test)
