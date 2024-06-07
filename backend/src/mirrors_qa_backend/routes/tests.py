from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Returns the list of tests."},
    },
)
def list_tests() -> Response:
    return JSONResponse(
        content={
            "tests": [],
            "metadata": {
                "currentPage": None,
                "pageSize": 10,
                "firstPage": None,
                "lastPage": None,
                "nextPage": None,
                "totalRecords": 20,
            },
        },
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/{test_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Returns the details of a test."},
        status.HTTP_404_NOT_FOUND: {"description": "Test with id does not exist."},
    },
)
def get_test(test_id: str) -> Response:
    return JSONResponse(
        content={"id": test_id},
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/{test_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Update the details of a test."},
    },
)
def update_test(test_id: str) -> Response:
    return JSONResponse(
        content={"id": test_id},
        status_code=status.HTTP_200_OK,
    )
