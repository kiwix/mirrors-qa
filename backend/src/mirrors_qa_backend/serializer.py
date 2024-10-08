from mirrors_qa_backend import schemas
from mirrors_qa_backend.db import models


def serialize_test(test: models.Test) -> schemas.Test:
    return schemas.Test(
        id=test.id,
        requested_on=test.requested_on,
        started_on=test.started_on,
        status=test.status,
        error=test.error,
        isp=test.isp,
        ip_address=test.ip_address,
        asn=test.asn,
        country_code=test.country_code,
        city=test.city,
        latency=test.latency,
        download_size=test.download_size,
        duration=test.duration,
        speed=test.speed,
        mirror_url=test.mirror_url,
    )


def serialize_mirror(mirror: models.Mirror) -> schemas.Mirror:
    return schemas.Mirror(
        id=mirror.id,
        base_url=mirror.base_url,
        enabled=mirror.enabled,
        asn=mirror.asn,
        country_code=mirror.country_code if mirror.country_code else None,
        score=mirror.score,
        latitude=mirror.latitude,
        longitude=mirror.longitude,
        country_only=mirror.country_only,
        region_only=mirror.region_only,
        as_only=mirror.as_only,
        other_countries=mirror.other_countries,
    )


def serialize_country(country: models.Country) -> schemas.Country:
    return schemas.Country(code=country.code, name=country.name)
