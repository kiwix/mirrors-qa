import pydantic
from pydantic import ConfigDict


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class Mirror(BaseModel):
    id: str  # hostname of a mirror URL
    base_url: str
    enabled: bool
    region: str | None = None
    asn: str | None = None
    score: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    country_only: bool | None = None
    region_only: bool | None = None
    as_only: bool | None = None
    other_countries: list[str] | None = None


class Country(BaseModel):
    code: str  # two-letter country codes as defined in ISO 3166-1
    name: str  # full name of country (in English)
    mirrors: list[Mirror]
