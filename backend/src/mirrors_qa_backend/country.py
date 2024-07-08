from typing import Any

import pycountry
from pycountry.db import Country


def get_country(country_name: str) -> Country:
    try:
        country: Any = pycountry.countries.search_fuzzy(country_name)[0]
    except LookupError as exc:
        raise ValueError(
            f"Could not get information for country: {country_name}"
        ) from exc
    return country
