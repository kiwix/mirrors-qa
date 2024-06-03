from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT, INET
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.schema import MetaData

from backend.enums import StatusEnum


class Base(MappedAsDataclass, DeclarativeBase):
    # This map details the specific transformation of types between Python and
    # PostgreSQL. This is only needed for the case where a specific PostgreSQL
    # type has to be used.

    type_annotation_map = {  # noqa: RUF012
        str: CITEXT,  # use case-insensitive strings on PostgreSQL backend
        list[str]: ARRAY(
            item_type=CITEXT
        ),  # transform Python list[str] into PostgreSQL Array of strings
        datetime: DateTime(
            timezone=False
        ),  # transform Python datetime into PostgreSQL Datetime without timezone
        IPv4Address: INET,  # transform Python IPV4Address into PostgreSQL INET
    }

    # This metadata specifies some naming conventions that will be used by
    # alembic to generate constraints names (indexes, unique constraints, ...)
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    pass


class Country(Base):
    __tablename__ = "country"

    code: Mapped[str] = mapped_column(
        primary_key=True
    )  # two-letter country codes as defined in ISO 3166-1

    name: Mapped[str]  # full name of the country (in English)

    worker_id: Mapped[UUID | None] = mapped_column(ForeignKey("worker.id"), init=False)
    worker: Mapped[Worker | None] = relationship(back_populates="countries", init=False)
    mirrors: Mapped[list[Mirror]] = relationship(
        back_populates="country",
        init=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("name", "code"),)


class Mirror(Base):
    __tablename__ = "mirror"

    id: Mapped[str] = mapped_column(primary_key=True)  # hostname of a mirror URL
    base_url: Mapped[str]
    enabled: Mapped[bool]
    # metadata of a mirror from MirroBrain (https://mirrorbrain-docs.readthedocs.io/en/latest/mirrors.html#displaying-details-about-a-mirror)
    region: Mapped[str | None]
    asn: Mapped[str | None]
    score: Mapped[int | None]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    country_only: Mapped[bool | None]
    region_only: Mapped[bool | None]
    as_only: Mapped[bool | None]
    other_countries: Mapped[list[str] | None]

    country_code: Mapped[str] = mapped_column(
        ForeignKey("country.code"),
        init=False,
    )
    country: Mapped[Country] = relationship(back_populates="mirrors", init=False)


class Worker(Base):
    __tablename__ = "worker"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    # RSA public key for generating access tokens needed to make request to
    # the web server
    auth_info: Mapped[str]
    last_seen_on: Mapped[datetime | None]
    countries: Mapped[list[Country]] = relationship(back_populates="worker", init=False)


class Test(Base):
    __tablename__ = "test"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    requested_on: Mapped[datetime]
    started_on: Mapped[datetime | None]
    status: Mapped[StatusEnum | None] = mapped_column(
        Enum(
            native_enum=False,
            validate_strings=True,
            create_constraint=True,
            name="status",
        )
    )
    error: Mapped[str | None]
    isp: Mapped[str | None]
    ip_address: Mapped[IPv4Address | None]
    asn: Mapped[str | None]  # autonomous system based on IP
    country: Mapped[str | None]  # country based on IP
    location: Mapped[str | None]  # city based on IP
    latency: Mapped[int | None]  # milliseconds
    download_size: Mapped[int | None]  # bytes
    duration: Mapped[int | None]  # seconds
    speed: Mapped[float | None]  # bytes per second
