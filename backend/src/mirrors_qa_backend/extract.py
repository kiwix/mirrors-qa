from typing import Any
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag
from pycountry.db import Country

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.country import get_country
from mirrors_qa_backend.exceptions import MirrorsExtractError, MirrorsRequestError
from mirrors_qa_backend.settings import Settings


def get_current_mirrors() -> list[schemas.Mirror]:
    """
    Current mirrors from the mirrors url.

    Raises:
        MirrorsExtractError: parser unable to extract the mirrors from the page.
            Page DOM has been updated and parser needs an update as well.
        MirrorsRequestError: a network error occured while fetching mirrors
    """

    def is_country_row(tag: Tag) -> bool:
        """
        Filters out table rows that do not contain mirror data.
        """
        return tag.name == "tr" and tag.findChild("td", class_="newregion") is None

    try:
        resp = requests.get(
            Settings.MIRRORS_URL, timeout=Settings.REQUESTS_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MirrorsRequestError(
            "network error while fetching mirrors from url"
        ) from exc

    soup = BeautifulSoup(resp.text, features="html.parser")
    body = soup.find("tbody")

    if body is None or isinstance(body, NavigableString | int):
        raise MirrorsExtractError(
            f"unable to parse mirrors information from {Settings.MIRRORS_URL}"
        )

    mirrors: list[schemas.Mirror] = []

    for row in body.find_all(is_country_row):
        base_url = row.find("a", string="HTTP")["href"]
        hostname: Any = urlsplit(
            base_url
        ).netloc  # pyright: ignore [reportUnknownMemberType]
        if hostname in Settings.MIRRORS_EXCLUSION_LIST:
            continue
        country_name = row.find("img").next_sibling.text.strip()
        try:
            country: Country = get_country(country_name)
        except ValueError:
            logger.error(f"Could not get information for country: {country_name}")
            continue
        else:
            mirrors.append(
                schemas.Mirror(
                    id=hostname,
                    base_url=base_url,
                    enabled=True,
                    country=schemas.Country(
                        code=country.alpha_2.lower(),
                        name=country.name,
                    ),
                )
            )
    return mirrors
