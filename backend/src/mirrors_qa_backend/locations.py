import requests
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.country import get_country
from mirrors_qa_backend.db.location import create_or_get_location
from mirrors_qa_backend.db.models import Location
from mirrors_qa_backend.exceptions import LocationsRequestError
from mirrors_qa_backend.settings import Settings


def get_test_locations() -> list[schemas.Country]:
    url = Settings.TEST_LOCATIONS_URL
    try:
        resp = requests.get(url, timeout=Settings.REQUESTS_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LocationsRequestError(
            f"network error while fetching locations from url: {url}"
        ) from exc

    data = resp.json()["locations"]
    # The "locations" entry contains cities but we only need the names of the
    # countries, use a set to avoid duplicate country names
    country_names: set[str] = set()
    for entry in data.values():
        country_names.add(entry["country"])
    logger.debug(f"Found {len(country_names)} locations from {url}")

    locations: list[schemas.Country] = []
    for country_name in country_names:
        country = get_country(country_name)
        locations.append(
            schemas.Country(code=country.alpha_2.lower(), name=country.name)
        )

    return locations


def update_locations(session: OrmSession) -> list[Location]:
    available_locations = get_test_locations()
    locations: list[Location] = []
    for test_location in available_locations:
        location = create_or_get_location(
            session,
            country_code=test_location.code,
            country_name=test_location.name,
        )
        locations.append(location)
    return locations
