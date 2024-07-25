from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

from mirrors_qa_backend.cli.worker import create_worker


@pytest.mark.parametrize(
    ["worker_id", "country_codes", "expectation"],
    [
        ("test", ["ng", "ca", "fr"], does_not_raise()),
        ("test", ["invalid country code"], pytest.raises(ValueError)),
        ("test", ["zz", "vv"], pytest.raises(ValueError)),
    ],
)
def test_create_worker(
    private_key_data: bytes,
    worker_id: str,
    country_codes: list[str],
    expectation: Any,
):
    with expectation:
        create_worker(worker_id, private_key_data, country_codes)
