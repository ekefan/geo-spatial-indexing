from pathlib import Path
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from database.db import SessionLocal
from database.models import BucketAlias, GeoBucket, Property
from locations import bucket_geometry, location_aliases
from models import PropertyCreate


LOCATIONS = [
    ("Sangotedo", 6.4698, 3.6285),
    ("Sangotedo, Ajah", 6.4720, 3.6301),
    ("sangotedo lagos", 6.4705, 3.6290),
    ("Ikeja", 6.6018, 3.3515),
    ("Victoria Island", 6.4281, 3.4219),
]


def seed() -> int:
    inserted = 0
    with SessionLocal.begin() as database:
        for number, (name, lat, lng) in enumerate(LOCATIONS, start=1):
            payload = PropertyCreate(
                title=f"{name} sample apartment", location_name=name,
                lat=lat, lng=lng, price=150000000, bedrooms=2, bathrooms=2,
            )
            cell, centroid, boundary = bucket_geometry(lat, lng)
            database.execute(
                insert(GeoBucket).values(h3_index=cell, centroid=centroid, boundary=boundary)
                .on_conflict_do_nothing(index_elements=[GeoBucket.h3_index])
            )
            bucket_id = database.scalar(select(GeoBucket.id).where(GeoBucket.h3_index == cell))
            database.execute(
                insert(BucketAlias).values([
                    {"bucket_id": bucket_id, "alias": alias}
                    for alias in location_aliases(name)
                ]).on_conflict_do_nothing()
            )
            property_id = UUID(f"11111111-1111-4111-8111-{number:012d}")
            created_id = database.scalar(
                insert(Property).values(id=property_id, bucket_id=bucket_id, **payload.model_dump())
                .on_conflict_do_nothing(index_elements=[Property.id]).returning(Property.id)
            )
            inserted += created_id is not None
    return inserted


if __name__ == "__main__":
    print(f"Seed complete: inserted {seed()} properties; existing seed records were preserved.")
