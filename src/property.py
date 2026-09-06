from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.db import get_db
from locations import normalize_location
from models import PropertyCreate, PropertyPage, PropertyRead
from repositories import property as property_repository


router = APIRouter(prefix="/properties", tags=["Properties"])
Database = Annotated[Session, Depends(get_db)]


@router.post("", response_model=PropertyRead, status_code=201)
def create_property(payload: PropertyCreate, database: Database):
    return property_repository.create_property(database, payload)


@router.get("/search", response_model=PropertyPage)
def search_properties(
    database: Database,
    location: Annotated[str, Query(min_length=1, max_length=250)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if not normalize_location(location):
        raise HTTPException(status_code=422, detail="Location must contain letters or numbers")
    return property_repository.search_properties(database, location, limit, offset)
