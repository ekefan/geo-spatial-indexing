from unittest.mock import patch


def test_stats_response(client, mock_database):
    result = {
        "total_properties": 3, "total_buckets": 1,
        "buckets": [{"id": "bucket", "h3_index": "cell", "property_count": 3}],
        "coverage": {"occupied_cell_area_km2": 0.73, "property_bounds": None},
        "limit": 50, "offset": 0,
    }
    with patch("geo_bucket.bucket_repository.get_stats", return_value=result) as stats:
        response = client.get("/api/geo-buckets/stats")
    assert response.status_code == 200
    assert response.json() == result
    stats.assert_called_once_with(mock_database, 50, 0)


def test_invalid_page_does_not_query(client):
    with patch("geo_bucket.bucket_repository.get_stats") as stats:
        assert client.get("/api/geo-buckets/stats?limit=0").status_code == 422
    stats.assert_not_called()
