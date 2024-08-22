from sqlalchemy.orm import Session as OrmSession

from mirrors_qa_backend.cli.country import (
    create_regions_and_countries,
    extract_country_regions_from_csv,
)
from mirrors_qa_backend.db.country import get_country
from mirrors_qa_backend.db.region import get_region


def test_create_regions_and_countries(dbsession: OrmSession):
    csv_data = [
        "country_iso_code,country_name,continent_code,continent_name",
        "ng,Nigeria,af,Africa",
        "fr,France,eu,Europe",
    ]

    countries = extract_country_regions_from_csv(csv_data)
    create_regions_and_countries(countries)

    for country in countries:
        assert country.region is not None
        db_country = get_country(dbsession, country.code)
        assert db_country.code == country.code
        assert db_country.name == country.name
        db_region = get_region(dbsession, country.region.code)
        assert db_region.code == country.region.code
        assert db_region.name == country.region.name
        assert db_country.region == db_region
