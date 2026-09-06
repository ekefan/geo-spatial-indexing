import h3
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from database.models import BucketAlias, GeoBucket, Property
from models import PropertyCreate
from repositories.property import create_property


pytestmark = pytest.mark.integration


@pytest.mark.parametrize("query", ["sangotedo", "SANGOTEDO", "Sangotedo, Ajah", "sangotedo lagos", "sangotdeo"])
def test_three_addresses_match_and_exclude_ikeja(populated_client, query):
    client, identifiers = populated_client
    response = client.get("/api/properties/search", params={"location": query})
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert {item["id"] for item in response.json()["items"]} == identifiers


def test_no_match_and_pagination(populated_client):
    client, identifiers = populated_client
    assert client.get("/api/properties/search?location=zzzzzzzz").json()["total"] == 0
    pages = [client.get("/api/properties/search", params={"location": "sangotedo", "limit": 1, "offset": offset}).json()
             for offset in range(3)]
    assert all(page["total"] == 3 and len(page["items"]) == 1 for page in pages)
    assert {page["items"][0]["id"] for page in pages} == identifiers


def test_shared_alias_across_adjacent_cells(client, property_payload):
    cell = h3.latlng_to_cell(6.4698, 3.6285, 8)
    neighbour = next(candidate for candidate in h3.grid_disk(cell, 1) if candidate != cell)
    for candidate in [cell, neighbour]:
        lat, lng = h3.cell_to_latlng(candidate)
        assert client.post("/api/properties", json={**property_payload, "lat": lat, "lng": lng}).status_code == 201
    assert client.get("/api/properties/search?location=sangotedo").json()["total"] == 2


def test_bucket_and_alias_upsert(client, database_session, property_payload):
    for unused in range(2):
        assert client.post("/api/properties", json=property_payload).status_code == 201
    assert database_session.scalar(select(func.count()).select_from(Property)) == 2
    assert database_session.scalar(select(func.count()).select_from(GeoBucket)) == 1
    assert database_session.scalar(select(func.count()).select_from(BucketAlias)) == 1
    for record in database_session.scalars(select(Property)):
        assert record.currency == "NGN"
        assert record.currency_unit_multiplier == 100


def test_actual_constraint_failure_rolls_back_ingestion(database_session, property_payload):
    payload = PropertyCreate.model_construct(**{**property_payload, "price": -1})
    with pytest.raises(IntegrityError):
        create_property(database_session, payload)
    for model in [Property, BucketAlias, GeoBucket]:
        assert database_session.scalar(select(func.count()).select_from(model)) == 0
