from typing import Annotated

import pycountry
from fastapi import APIRouter, Depends
from fastapi import status as status_codes
from sqlalchemy.orm import Session

from mirrors_qa_backend.db import gen_dbsession
from mirrors_qa_backend.db.country import update_countries as update_db_countries
from mirrors_qa_backend.db.exceptions import RecordDoesNotExistError
from mirrors_qa_backend.db.worker import get_worker as get_db_worker
from mirrors_qa_backend.db.worker import update_worker as update_db_worker
from mirrors_qa_backend.routes.dependencies import CurrentWorker
from mirrors_qa_backend.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)
from mirrors_qa_backend.schemas import UpdateWorkerCountries, WorkerCountries
from mirrors_qa_backend.serializer import serialize_country

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get(
    "/{worker_id}/countries",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {
            "description": "Return the list of countries the worker is assigned to."
        }
    },
)
def list_countries(
    session: Annotated[Session, Depends(gen_dbsession)], worker_id: str
) -> WorkerCountries:
    try:
        worker = get_db_worker(session, worker_id)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(str(exc)) from exc

    return WorkerCountries(
        countries=[serialize_country(country) for country in worker.countries]
    )


@router.put(
    "/{worker_id}/countries",
    status_code=status_codes.HTTP_200_OK,
    responses={
        status_codes.HTTP_200_OK: {
            "description": "Return the updated list of countries the worker is assigned"
        }
    },
)
def update_countries(
    session: Annotated[Session, Depends(gen_dbsession)],
    worker_id: str,
    current_worker: CurrentWorker,
    data: UpdateWorkerCountries,
) -> WorkerCountries:
    if current_worker.id != worker_id:
        raise UnauthorizedError(
            "You do not have the required permissions to access this endpoint."
        )
    # Ensure all the country codes are valid country codes
    country_mapping: dict[str, str] = {}
    for country_code in data.country_codes:
        if country := pycountry.countries.get(alpha_2=country_code):
            country_mapping[country_code.lower()] = country.name
        else:
            raise BadRequestError(f"{country_code} is not a valid country code.")
    update_db_countries(session, country_mapping)
    updated_worker = update_db_worker(session, worker_id, list(country_mapping.keys()))

    return WorkerCountries(
        countries=[serialize_country(country) for country in updated_worker.countries]
    )
