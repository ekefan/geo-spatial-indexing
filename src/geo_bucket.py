from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.db import get_db
from repositories import geo_bucket as bucket_repository


router = APIRouter(prefix="/geo-buckets", tags=["Geo buckets"])


@router.get("/stats")
def bucket_stats(
    database: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return bucket_repository.get_stats(database, limit, offset)
