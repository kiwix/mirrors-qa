import pytest
from fastapi import status as status_codes
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.db.models import Worker
from mirrors_qa_backend.db.worker import get_worker


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Content-type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def test_list_worker_countries(worker: Worker, client: TestClient) -> None:
    response = client.get(f"/workers/{worker.id}/countries")
    assert response.status_code == status_codes.HTTP_200_OK

    data = response.json()
    assert "countries" in data

    countries = data["countries"]
    assert len(worker.countries) == len(countries)

    worker_country_codes = [country.code for country in worker.countries]
    for country in countries:
        assert country["code"] in worker_country_codes


def test_update_worker_with_non_existent_country_code(
    worker: Worker, auth_headers: dict[str, str], client: TestClient
):
    # mixture of invalid country codes and valid country codes
    country_codes = ["us", "fr", "ca", "jj", "xx"]
    response = client.put(
        f"/workers/{worker.id}/countries",
        headers=auth_headers,
        json={"country_codes": country_codes},
    )

    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    ["country_codes"],
    [
        (["nz", "us", "ng", "fr", "ca", "be", "bg", "md"],),
        (["ng"],),
        ([],),
    ],
)
def test_update_worker_countries(
    dbsession: OrmSession,
    worker: Worker,
    country_codes: list[str],
    auth_headers: dict[str, str],
    client: TestClient,
) -> None:
    response = client.put(
        f"/workers/{worker.id}/countries",
        headers=auth_headers,
        json={"country_codes": country_codes},
    )

    assert response.status_code == status_codes.HTTP_200_OK

    data = response.json()
    assert "countries" in data

    # reload the worker with the updated countries
    worker = get_worker(dbsession, worker.id)
    countries = data["countries"]
    assert len(worker.countries) == len(countries)

    worker_country_codes = [country.code for country in worker.countries]
    for country in countries:
        assert country["code"] in worker_country_codes
