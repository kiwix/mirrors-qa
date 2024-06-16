from typing import Annotated

from fastapi import APIRouter, Query
from fastapi import status as status_codes
from pydantic import UUID4

from mirrors_qa_backend import db, schemas, serializer
from mirrors_qa_backend.enums import SortDirectionEnum, StatusEnum, TestSortColumnEnum
from mirrors_qa_backend.routes import CurrentWorker, DbSession, http_errors
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
    result = db.tests.list_tests(
        session,
        worker_id=worker_id,
        country=country,
        status=status,
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
def get_test(test_id: UUID4, session: DbSession) -> schemas.Test:
    test = db.tests.get_test(session, test_id)
    if test is None:
        raise http_errors.NotFoundError(f"Test with id '{test_id}' does not exist.")
    return serializer.serialize_test(test)


@router.patch(
    "/{test_id}",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {"description": "Update the details of a test."},
    },
)
def update_test(
    session: DbSession,
    worker: CurrentWorker,
    test_id: UUID4,
    update: schemas.UpdateTestModel,
) -> schemas.Test:
    data = update.model_dump(exclude_unset=True)
    body = schemas.UpdateTestModel().model_copy(update=data)
    # Ensure that the worker is the one who the test belongs to
    test = db.tests.get_test(session, test_id)
    if test is None:
        raise http_errors.NotFoundError(f"Test with id {test_id} does not exist.")

    if test.worker_id != worker.id:
        raise http_errors.UnauthorizedError("Insufficient privileges to update test.")

    updated_test = db.tests.create_or_update_test(
        session,
        test_id=test_id,
        worker_id=worker.id,
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

    return serializer.serialize_test(updated_test)
