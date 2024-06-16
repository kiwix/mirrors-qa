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
        country=test.country,
        location=test.location,
        latency=test.latency,
        download_size=test.download_size,
        duration=test.duration,
        speed=test.speed,
    )


def serialize_mirror(mirror: models.Mirror) -> schemas.Mirror:
    return schemas.Mirror(
        id=mirror.id,
        base_url=mirror.base_url,
        enabled=mirror.enabled,
        region=mirror.region,
        asn=mirror.asn,
        score=mirror.score,
        latitude=mirror.latitude,
        longitude=mirror.longitude,
        country_only=mirror.country_only,
        region_only=mirror.region_only,
        as_only=mirror.as_only,
        other_countries=mirror.other_countries,
        country=schemas.Country(code=mirror.country.code, name=mirror.country.name),
    )
