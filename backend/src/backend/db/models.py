from datetime import datetime
from ipaddress import IPv4Address
from typing import List, Optional
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
        str: CITEXT,  # transform Python str to PostgreSQL CITEXT
        List[str]: ARRAY(
            item_type=CITEXT
        ),  # transform Python List[str] into PostgreSQL Array of strings
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

    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

    worker_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("worker.id"), init=False
    )
    worker: Mapped[Optional["Worker"]] = relationship(
        back_populates="countries", init=False
    )
    mirrors: Mapped[List["Mirror"]] = relationship(
        back_populates="country",
        init=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("name", "code"),)


class Mirror(Base):
    __tablename__ = "mirror"

    base_url: Mapped[str] = mapped_column(primary_key=True)
    enabled: Mapped[bool]
    # metadata of a mirror from MirroBrain (https://mirrorbrain-docs.readthedocs.io/en/latest/mirrors.html#displaying-details-about-a-mirror)
    id: Mapped[Optional[str]]
    region: Mapped[Optional[str]]
    asn: Mapped[Optional[str]]
    score: Mapped[Optional[int]]
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    country_only: Mapped[Optional[bool]]
    region_only: Mapped[Optional[bool]]
    as_only: Mapped[Optional[bool]]
    other_countries: Mapped[Optional[List[str]]]

    country_code: Mapped[str] = mapped_column(
        ForeignKey("country.code"),
        init=False,
    )
    country: Mapped["Country"] = relationship(back_populates="mirrors", init=False)


class Worker(Base):
    __tablename__ = "worker"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    auth_info: Mapped[str]
    last_seen: Mapped[Optional[datetime]]
    countries: Mapped[List["Country"]] = relationship(
        back_populates="worker", init=False
    )


class Test(Base):
    __tablename__ = "test"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    requested_on: Mapped[datetime]
    started_on: Mapped[Optional[datetime]]
    status: Mapped[Optional[StatusEnum]] = mapped_column(
        Enum(
            native_enum=False,
            validate_strings=True,
            create_constraint=True,
            name="status",
        )
    )
    error: Mapped[Optional[str]]
    ip_address: Mapped[Optional[IPv4Address]]
    asn: Mapped[Optional[str]]
    isp: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    latency: Mapped[Optional[int]]  # milliseconds
    download_size: Mapped[Optional[int]]  # bytes
    duration: Mapped[Optional[int]]  # seconds
    speed: Mapped[Optional[float]]  # bytes per second
