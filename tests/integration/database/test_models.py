from uuid import uuid4

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from database.models import BucketAlias, GeoBucket
from locations import bucket_geometry


pytestmark = pytest.mark.integration



def test_alias_cannot_reference_missing_bucket(database_session):
    with pytest.raises(IntegrityError):
        with database_session.begin():
            database_session.add(BucketAlias(bucket_id=uuid4(), alias="sangotedo"))
            database_session.flush()


def test_bucket_geometry_is_valid_geography(database_session):
    cell, centroid, boundary = bucket_geometry(6.4698, 3.6285)
    with database_session.begin():
        database_session.add(GeoBucket(h3_index=cell, centroid=centroid, boundary=boundary))
    result = database_session.execute(text(
        "SELECT ST_IsValid(boundary::geometry), ST_Covers(boundary::geometry, centroid::geometry), "
        "ST_Area(boundary) FROM geo_buckets"
    )).one()
    assert result[0] and result[1]
    assert result[2] > 0
