import csv

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.country import create_country
from mirrors_qa_backend.db.region import create_region
from mirrors_qa_backend.schemas import Country, Region


def create_regions_and_countries(countries: list[Country]) -> None:
    """Create the region and associated countries in the database."""
    with Session.begin() as session:
        for country in countries:
            db_country = create_country(
                session,
                country_code=country.code,
                country_name=country.name,
            )
            if country.region:
                db_region = create_region(
                    session,
                    region_code=country.region.code,
                    region_name=country.region.name,
                )
                db_country.region = db_region
                session.add(db_country)


def extract_country_regions_from_csv(csv_data: list[str]) -> list[Country]:
    regions: list[Country] = []
    for row in csv.DictReader(csv_data):
        country_code = row["country_iso_code"]
        country_name = row["country_name"]
        region_code = row["continent_code"]
        region_name = row["continent_name"]
        if all([country_code, country_name, region_code, region_name]):
            regions.append(
                Country(
                    code=country_code.lower(),
                    name=country_name.title(),
                    region=Region(
                        code=region_code.lower(),
                        name=region_name.title(),
                    ),
                )
            )
        else:
            logger.critical(
                f"Skipping row with missing entries: country_code: {country_code}, "
                f"country_name: {country_name}, region_code: {region_code}, "
                f"region_name: {region_name}"
            )
    return regions
