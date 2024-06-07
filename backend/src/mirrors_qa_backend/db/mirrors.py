from typing import Any
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from mirrors_qa_backend import logger, schemas
from mirrors_qa_backend.db import models
from mirrors_qa_backend.settings import Settings


def create_mirrors(session: OrmSession, countries: list[schemas.Country]) -> None:
    for country in countries:
        c = models.Country(code=country.code, name=country.name)
        c.mirrors = [models.Mirror(**m.model_dump()) for m in country.mirrors]
        session.add(c)


def update_mirrors(session: OrmSession, countries: list[schemas.Country]) -> None:
    """
    Updates the status of mirrors in the database. Any mirrors in the database
    that do not exist in the current mirrors obtained from `countries` are
    marked as disabled. New mirrors are saved accordingly.
    """
    # If there are no countries, disable all mirrors
    if not countries:
        for mirror in session.scalars(select(models.Mirror)).all():
            mirror.enabled = False
            session.add(mirror)
        return

    query = select(models.Country).options(selectinload(models.Country.mirrors))
    # Map the country codes to each country from the database. To be used
    # to compare against the list of current countries
    db_countries: dict[str, models.Country] = {
        country.code: country for country in session.scalars(query).all()
    }
    # Map the country codes to each country from the current list of coutnries.
    # To be used in determining if a country is to be newly registered
    current_countries: dict[str, schemas.Country] = {
        country.code: country for country in countries
    }

    for country_code, country in current_countries.items():
        if country_code not in db_countries:
            # Register all of the country's mirrors as the country is
            # a new country
            logger.debug("Registering new mirrors for {country_code!r}")
            c = models.Country(code=country.code, name=country.name)
            c.mirrors = [models.Mirror(**m.model_dump()) for m in country.mirrors]
            session.add(c)

    for code, db_country in db_countries.items():
        if code in current_countries:
            # Even though the db_country is "current", ensure it's mirrors
            # are in sync with the current mirrors
            current_mirrors: dict[str, schemas.Mirror] = {
                m.id: m for m in current_countries[code].mirrors
            }
            db_mirrors: dict[str, models.Mirror] = {m.id: m for m in db_country.mirrors}

            for db_mirror in db_mirrors.values():
                if db_mirror.id not in current_mirrors:
                    logger.debug(f"Disabling mirror {db_mirror.id!r}")
                    db_mirror.enabled = False
                    session.add(db_mirror)

            for mirror_id, mirror in current_mirrors.items():
                if mirror_id not in db_mirrors:
                    logger.debug(
                        f"Registering new mirror {mirror.id!r} for "
                        "country: {db_country.name!r}"
                    )
                    db_country.mirrors.append(models.Mirror(**mirror.model_dump()))
                    session.add(db_country)
        else:
            # disable all of the country's mirrors as they have been removed
            for db_mirror in db_country.mirrors:
                logger.debug(f"Disabling mirror {db_mirror.id!r}")
                db_mirror.enabled = False
                session.add(db_mirror)


def get_current_mirror_countries() -> list[schemas.Country]:
    def find_country_rows(tag: Tag) -> bool:
        """
        Filters out table rows that do not contain mirror
        data from the table body.
        """
        return tag.name == "tr" and tag.findChild("td", class_="newregion") is None

    r = requests.get(Settings.mirrors_url, timeout=Settings.requests_timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, features="html.parser")
    body = soup.find("tbody")

    if body is None or isinstance(body, NavigableString):
        raise ValueError
    # Given a country might have more than one mirror, set up a dictionary
    # of country_code to the country's data. If it is the first time we
    # are seeing the country, we save it along with its mirror, else,
    # we simply update its mirrors list.
    countries: dict[str, schemas.Country] = {}
    rows = body.find_all(find_country_rows)
    for row in rows:
        country_name = row.find("img").next_sibling.text.strip()
        if country_name in Settings.mirrors_exclusion_list:
            continue
        country_code = row.find("img")["alt"]
        base_url = row.find("a", string="HTTP")["href"]
        hostname: Any = urlsplit(
            base_url
        ).netloc  # pyright: ignore [reportUnknownMemberType]

        if country_code not in countries:
            countries[country_code] = schemas.Country(
                code=country_code,
                name=country_name,
                mirrors=[
                    schemas.Mirror(
                        id=hostname,
                        base_url=base_url,
                        enabled=True,
                    )
                ],
            )
        else:
            countries[country_code].mirrors.append(
                schemas.Mirror(
                    id=hostname,
                    base_url=base_url,
                    enabled=True,
                )
            )
    return list(countries.values())
