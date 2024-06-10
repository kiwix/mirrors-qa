from typing import Any
from urllib.parse import urlsplit

import pycountry
import requests
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.exceptions import MirrorsExtractError
from mirrors_qa_backend.settings import Settings


def get_current_mirrors() -> list[schemas.Mirror]:
    """
    Returns list of current mirrors from the mrirors url.

    Raises MirrorsExtractError if the parser is unable to extract the mirrors
    from the page. This is most likely as a result of the page being updated
    indicating that the parsing logic should be updated
    """

    def find_country_rows(tag: Tag) -> bool:
        """
        Filters out table rows that do not contain mirror
        data from the table body.
        """
        return tag.name == "tr" and tag.findChild("td", class_="newregion") is None

    resp = requests.get(Settings.mirrors_url, timeout=Settings.requests_timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, features="html.parser")
    body = soup.find("tbody")

    if body is None or isinstance(body, NavigableString | int):
        raise MirrorsExtractError(
            f"unable to parse mirrors information from {Settings.mirrors_url!r}"
        )

    mirrors: list[schemas.Mirror] = []

    for row in body.find_all(find_country_rows):
        base_url = row.find("a", string="HTTP")["href"]
        hostname: Any = urlsplit(
            base_url
        ).netloc  # pyright: ignore [reportUnknownMemberType]
        if hostname in Settings.mirrors_exclusion_list:
            continue
        country_name = row.find("img").next_sibling.text.strip()
        try:
            country: Any = pycountry.countries.search_fuzzy(country_name)[0]
        except LookupError:
            logger.warning(f"Could not get information for country: {country_name!r}")
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
