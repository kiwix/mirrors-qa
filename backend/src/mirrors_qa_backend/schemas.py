import datetime
import math
from ipaddress import IPv4Address
from typing import Annotated

import pydantic
from pydantic import UUID4, ConfigDict, Field

from mirrors_qa_backend.enums import StatusEnum


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


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


class UpdateTestModel(BaseModel):
    started_on: datetime.datetime | None = None
    error: str | None = None
    isp: str | None = None
    ip_address: IPv4Address | None = None
    asn: str | None = None
    city: str | None = None
    latency: float | None = None
    download_size: int | None = None
    duration: float | None = None
    speed: float | None = None
    status: StatusEnum = StatusEnum.PENDING


class Test(UpdateTestModel):
    id: UUID4
    requested_on: datetime.datetime
    country_code: str | None = None  # country to run the test from
    mirror_url: str | None  # base url of the mirror to run the test


class Paginator(BaseModel):
    total_records: int
    page_size: int
    current_page: int | None = None
    first_page: int | None = None
    last_page: int | None = None


ISOCountryCode = Annotated[str, Field(min_length=2, max_length=2)]


class Country(BaseModel):
    code: ISOCountryCode  # two-letter country code as defined in ISO 3166-1
    name: str  # full name of the country (in English)


class WorkerCountries(BaseModel):
    countries: list[Country]


class UpdateWorkerCountries(BaseModel):
    country_codes: list[ISOCountryCode]


class TestsList(BaseModel):
    tests: list[Test]
    metadata: Paginator


def calculate_pagination_metadata(
    total_records: int, page_size: int, current_page: int
) -> Paginator:
    if total_records == 0:
        return Paginator(total_records=0, page_size=0)
    return Paginator(
        total_records=total_records,
        first_page=1,
        page_size=min(page_size, total_records),
        current_page=current_page,
        last_page=math.ceil(total_records / page_size),
    )


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: float


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    subject: str
