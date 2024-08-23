from typing import Any
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag

from mirrors_qa_backend import schemas
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
        country_code = row.find("img")["alt"].lower()
        if hostname in Settings.MIRRORS_EXCLUSION_LIST:
            continue
        mirrors.append(
            schemas.Mirror(
                id=hostname,
                base_url=base_url,
                enabled=True,
                country_code=country_code,
            )
        )
    return mirrors
