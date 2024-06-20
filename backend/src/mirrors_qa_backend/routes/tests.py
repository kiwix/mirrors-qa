from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import status as status_codes

from mirrors_qa_backend import schemas, serializer
from mirrors_qa_backend.db import tests, worker
from mirrors_qa_backend.enums import SortDirectionEnum, StatusEnum, TestSortColumnEnum
from mirrors_qa_backend.routes.dependencies import (
    CurrentWorker,
    DbSession,
    RetrievedTest,
    verify_worker_owns_test,
)
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
    country: Annotated[str | None, Query(min_length=3)] = None,
    status: Annotated[list[StatusEnum] | None, Query()] = None,
    page_size: Annotated[
        int, Query(le=Settings.MAX_PAGE_SIZE, ge=1)
    ] = Settings.MAX_PAGE_SIZE,
    page_num: Annotated[int, Query(ge=1)] = 1,
    sort_by: Annotated[TestSortColumnEnum, Query()] = TestSortColumnEnum.requested_on,
    order: Annotated[SortDirectionEnum, Query()] = SortDirectionEnum.asc,
) -> schemas.TestsList:
    result = tests.list_tests(
        session,
        worker_id=worker_id,
        country=country,
        statuses=status,
        page_size=page_size,
        page_num=page_num,
        sort_column=sort_by,
        sort_direction=order,
    )
    return schemas.TestsList(
        tests=[serializer.serialize_test(test) for test in result.tests],
        metadata=schemas.calculate_pagination_metadata(
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
def get_test(test: RetrievedTest) -> schemas.Test:
    return serializer.serialize_test(test)


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
) -> schemas.Test:
    data = update.model_dump(exclude_unset=True)
    body = schemas.UpdateTestModel().model_copy(update=data)
    updated_test = tests.create_or_update_test(
        session,
        test_id=test.id,
        worker_id=current_worker.id,
        status=body.status,
        error=body.error,
        ip_address=body.ip_address,
        asn=body.asn,
        country=body.country,
        location=body.location,
        latency=body.latency,
        download_size=body.download_size,
        duration=body.duration,
        speed=body.speed,
    )
    worker.update_worker_last_seen(session, current_worker)
    return serializer.serialize_test(updated_test)
