from unittest.mock import patch

import pytest


def test_create_returns_serialized_property(client, mock_database, property_payload, property_result):
    with patch("property.property_repository.create_property", return_value=property_result) as save:
        response = client.post("/api/properties", json=property_payload)
    assert response.status_code == 201
    assert response.json() == property_result.model_dump(mode="json")
    assert save.call_args.args[0] is mock_database
    assert save.call_args.args[1].location_name == property_payload["location_name"]
    mock_database.begin.assert_not_called()


@pytest.mark.parametrize("changes", [{"lat": 91}, {"price": -1}, {"location_name": "!!!"}])
def test_invalid_creation_does_not_write(client, property_payload, changes):
    with patch("property.property_repository.create_property") as save:
        response = client.post("/api/properties", json={**property_payload, **changes})
    assert response.status_code == 422
    save.assert_not_called()


def test_search_serialization_and_pagination(client, mock_database, property_result):
    result = {"items": [property_result], "total": 3, "limit": 1, "offset": 1}
    with patch("property.property_repository.search_properties", return_value=result) as search:
        response = client.get("/api/properties/search", params={"location": "SANGOTEDO", "limit": 1, "offset": 1})
    search.assert_called_once_with(mock_database, "SANGOTEDO", 1, 1)
    assert response.status_code == 200
    assert response.json() == {
        "items": [property_result.model_dump(mode="json")], "total": 3, "limit": 1, "offset": 1,
    }


def test_empty_search_response(client, mock_database):
    result = {
        "items": [], "total": 0, "limit": 50, "offset": 0,
    }
    with patch("property.property_repository.search_properties", return_value=result):
        assert client.get("/api/properties/search?location=unknown").json() == result


@pytest.mark.parametrize("params", [{}, {"location": "!!!"}, {"location": "ikeja", "limit": 101}, {"location": "ikeja", "offset": -1}])
def test_invalid_search_does_not_query(client, mock_database, params):
    with patch("property.property_repository.search_properties") as search:
        assert client.get("/api/properties/search", params=params).status_code == 422
    search.assert_not_called()
