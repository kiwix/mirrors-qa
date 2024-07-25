import pycountry
from cryptography.hazmat.primitives import serialization

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.country import update_countries as update_db_countries
from mirrors_qa_backend.db.worker import create_worker as create_db_worker
from mirrors_qa_backend.db.worker import update_worker as update_db_worker


def get_country_mapping(country_codes: list[str]) -> dict[str, str]:
    """Fetch the country names from the country codes.

    Maps the country code to the country name.
    """
    country_mapping: dict[str, str] = {}
    # Ensure all the countries are valid country codes
    for country_code in country_codes:
        if len(country_code) != 2:  # noqa: PLR2004
            raise ValueError(
                f"Country code '{country_code}' must be two characters long"
            )

        if country := pycountry.countries.get(alpha_2=country_code):
            country_mapping[country_code] = country.name
        else:
            raise ValueError(f"'{country_code}' is not valid country code")
    return country_mapping


def create_worker(
    worker_id: str, private_key_data: bytes, initial_country_codes: list[str]
):
    """Create a worker in the DB.

    Assigns the countries for a worker to run tests from.
    """
    country_mapping = get_country_mapping(initial_country_codes)
    private_key = serialization.load_pem_private_key(
        private_key_data, password=None
    )  # pyright: ignore[reportReturnType]

    with Session.begin() as session:
        # Update the database with the countries in case those countries don't
        # exist yet.
        update_db_countries(session, country_mapping)
        create_db_worker(
            session,
            worker_id,
            initial_country_codes,
            private_key,  # pyright: ignore [reportGeneralTypeIssues, reportArgumentType]
        )

    logger.info(f"Created worker {worker_id} successfully")


def update_worker(worker_id: str, country_codes: list[str]):
    """Update worker's data.

    Updates the ountries for a worker to run tests from.
    """
    country_mapping = get_country_mapping(country_codes)
    with Session.begin() as session:
        update_db_countries(session, country_mapping)
        update_db_worker(session, worker_id, country_codes)
