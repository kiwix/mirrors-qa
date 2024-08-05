import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from mirrors_qa_backend.db import models


def test_test_not_found(client: TestClient):
    test_id = str(uuid.uuid4())
    resp = client.get(f"/tests/{test_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.num_tests(1)
def test_tests_get(client: TestClient, tests: list[models.Test]):

    test = tests[0]
    response = client.get(f"/tests/{test.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test.id)
    assert data["status"] == test.status.name


@pytest.mark.num_tests(100)
def test_tests_list(client: TestClient, tests: list[models.Test]):
    response = client.get("/tests")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "metadata" in data
    assert "tests" in data
    metadata = data["metadata"]
    assert metadata["total_records"] == len(tests)


@pytest.mark.num_tests(1)
@pytest.mark.parametrize(
    ["with_auth", "expected_status"],
    [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_test_patch(
    *,
    tests: list[models.Test],
    client: TestClient,
    access_token: str,
    with_auth: bool,
    expected_status: int,
):
    test = tests[0]
    headers = {"Content-type": "application/json"}
    if with_auth:
        headers["Authorization"] = f"Bearer {access_token}"

    response = client.patch(
        f"/tests/{test.id}", headers=headers, json={"status": test.status.name}
    )
    assert response.status_code == expected_status
