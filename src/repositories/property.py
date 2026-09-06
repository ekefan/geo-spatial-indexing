from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from database.models import BucketAlias, Property
from locations import normalize_location
from models import PropertyCreate, PropertyPage, PropertyRead
from repositories.geo_bucket import upsert_bucket
from locations import location_aliases


def create_property(database: Session, payload: PropertyCreate) -> PropertyRead:
    """Create the bucket, aliases, and property atomically using a fresh session."""
    with database.begin():
        bucket_id = upsert_bucket(database, payload.lat, payload.lng, payload.location_name)
        record = Property(bucket_id=bucket_id, **payload.model_dump())
        database.add(record)
        database.flush()
        result = PropertyRead.model_validate(record)
    return result


def search_properties(database: Session, location: str, limit: int = 50, offset: int = 0) -> PropertyPage:
    normalized = normalize_location(location)
    if not normalized:
        raise ValueError("Location must contain letters or numbers")
    aliases = location_aliases(location)
    predicate = BucketAlias.alias.in_(aliases)
    has_exact = database.scalar(select(select(BucketAlias.bucket_id).where(predicate).exists()))
    if not has_exact and len(normalized) >= 3:
        database.execute(text("SELECT set_config('pg_trgm.similarity_threshold', '0.3', true)"))
        predicate = BucketAlias.alias.bool_op("%")(
            min(aliases, key=len)
        )
    bucket_ids = select(BucketAlias.bucket_id).where(predicate)
    selection = select(Property).where(Property.bucket_id.in_(bucket_ids))
    total = database.scalar(select(func.count()).select_from(selection.subquery()))
    items = database.scalars(
        selection.order_by(Property.created_at.desc(), Property.id.desc()).limit(limit).offset(offset)
    ).all()
    return PropertyPage(items=items, total=total, limit=limit, offset=offset)
