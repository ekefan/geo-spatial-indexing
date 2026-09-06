from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from database.models import BucketAlias, GeoBucket, Property
from locations import bucket_geometry, location_aliases


def upsert_bucket(database: Session, lat: float, lng: float, location_name: str) -> UUID:
    """Return a bucket ID and register aliases within the caller's transaction."""
    cell, centroid, boundary = bucket_geometry(lat, lng)
    bucket_id = database.scalar(
        insert(GeoBucket).values(h3_index=cell, centroid=centroid, boundary=boundary)
        .on_conflict_do_nothing(index_elements=[GeoBucket.h3_index]).returning(GeoBucket.id)
    )
    if bucket_id is None:
        bucket_id = database.scalar(select(GeoBucket.id).where(GeoBucket.h3_index == cell))
    database.execute(
        insert(BucketAlias).values([
            {"bucket_id": bucket_id, "alias": alias}
            for alias in location_aliases(location_name)
        ]).on_conflict_do_nothing()
    )
    return bucket_id


def get_stats(database: Session, limit: int = 50, offset: int = 0) -> dict:
    counts = select(Property.bucket_id, func.count().label("property_count")).group_by(
        Property.bucket_id
    ).subquery()
    rows = database.execute(
        select(GeoBucket.id, GeoBucket.h3_index, func.coalesce(counts.c.property_count, 0).label("property_count"))
        .outerjoin(counts, counts.c.bucket_id == GeoBucket.id)
        .order_by(GeoBucket.h3_index).limit(limit).offset(offset)
    ).mappings().all()
    coverage = database.execute(text("""
        SELECT COALESCE(SUM(ST_Area(boundary)), 0) / 1000000 AS occupied_cell_area_km2
        FROM geo_buckets
        WHERE EXISTS (SELECT 1 FROM properties WHERE properties.bucket_id = geo_buckets.id)
    """)).scalar_one()
    bounds = database.execute(select(
        func.min(Property.lng).label("west"), func.min(Property.lat).label("south"),
        func.max(Property.lng).label("east"), func.max(Property.lat).label("north"),
    )).mappings().one()
    return {
        "total_buckets": database.scalar(select(func.count()).select_from(GeoBucket)),
        "total_properties": database.scalar(select(func.count()).select_from(Property)),
        "buckets": [dict(row) for row in rows],
        "coverage": {
            "occupied_cell_area_km2": coverage,
            "property_bounds": dict(bounds) if bounds["west"] is not None else None,
        },
        "limit": limit,
        "offset": offset,
    }
