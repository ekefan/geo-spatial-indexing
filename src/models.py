from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from locations import normalize_location


class PropertyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=250)
    location_name: str = Field(min_length=1, max_length=250)
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)
    price: int = Field(ge=0, le=9223372036854775807, strict=True)
    bedrooms: int = Field(ge=0, le=2147483647, strict=True)
    bathrooms: int = Field(ge=0, le=2147483647, strict=True)

    @field_validator("location_name")
    @classmethod
    def validate_location(cls, value: str) -> str:
        if not normalize_location(value):
            raise ValueError("Location must contain letters or numbers")
        return value


class PropertyRead(PropertyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bucket_id: UUID
    created_at: datetime
    updated_at: datetime


class PropertyPage(BaseModel):
    items: list[PropertyRead]
    total: int
    limit: int
    offset: int
