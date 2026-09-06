from __future__ import annotations

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class GeoBucket(Base):
    __tablename__ = "geo_buckets"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    h3_index: Mapped[str] = mapped_column(String(15), unique=True)
    centroid: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True)
    )
    boundary: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POLYGON", srid=4326, spatial_index=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    properties: Mapped[list[Property]] = relationship(
        back_populates="bucket", passive_deletes="all"
    )
    aliases: Mapped[list[BucketAlias]] = relationship(
        back_populates="bucket", cascade="all, delete-orphan", passive_deletes=True
    )


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint("lat >= -90 AND lat <= 90", name="ck_properties_lat"),
        CheckConstraint("lng >= -180 AND lng <= 180", name="ck_properties_lng"),
        CheckConstraint("price >= 0", name="ck_properties_price"),
        CheckConstraint("bedrooms >= 0", name="ck_properties_bedrooms"),
        CheckConstraint("bathrooms >= 0", name="ck_properties_bathrooms"),
        CheckConstraint(
            "currency_unit_multiplier > 0", name="ck_properties_currency_multiplier"
        ),
        Index("ix_properties_bucket_created_id", "bucket_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    bucket_id: Mapped[UUID] = mapped_column(
        ForeignKey("geo_buckets.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(Text)
    location_name: Mapped[str] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Double)
    lng: Mapped[float] = mapped_column(Double)
    price: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(Text, default="NGN")
    currency_unit_multiplier: Mapped[int] = mapped_column(Integer, default=100)
    bedrooms: Mapped[int] = mapped_column(Integer)
    bathrooms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bucket: Mapped[GeoBucket] = relationship(back_populates="properties")


class BucketAlias(Base):
    __tablename__ = "bucket_aliases"
    __table_args__ = (
        Index("ix_bucket_aliases_alias", "alias"),
        Index(
            "ix_bucket_aliases_alias_trgm",
            "alias",
            postgresql_using="gin",
            postgresql_ops={"alias": "gin_trgm_ops"},
        ),
    )

    bucket_id: Mapped[UUID] = mapped_column(
        ForeignKey("geo_buckets.id", ondelete="CASCADE"), primary_key=True
    )
    alias: Mapped[str] = mapped_column(Text, primary_key=True)

    bucket: Mapped[GeoBucket] = relationship(back_populates="aliases")
