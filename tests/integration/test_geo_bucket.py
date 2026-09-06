import pytest


pytestmark = pytest.mark.integration


def test_empty_coverage(client):
    response = client.get("/api/geo-buckets/stats")
    assert response.status_code == 200
    assert response.json()["total_properties"] == 0
    assert response.json()["total_buckets"] == 0
    assert response.json()["coverage"] == {"occupied_cell_area_km2": 0, "property_bounds": None}


def test_counts_area_and_pagination(populated_client):
    client, identifiers = populated_client
    result = client.get("/api/geo-buckets/stats").json()
    assert result["total_properties"] == len(identifiers) + 1
    assert sum(bucket["property_count"] for bucket in result["buckets"]) == 4
    assert result["total_buckets"] == len(result["buckets"])
    assert result["coverage"]["occupied_cell_area_km2"] > 0
    assert result["coverage"]["property_bounds"] == {"west": 3.3515, "south": 6.4698, "east": 3.6301, "north": 6.6018}
    page = client.get("/api/geo-buckets/stats?limit=1").json()
    assert len(page["buckets"]) == 1
    assert page["total_properties"] == 4
