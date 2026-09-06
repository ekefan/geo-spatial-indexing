import os
from pathlib import Path
import subprocess
import sys

import pytest
import h3
from sqlalchemy import func, select

from database.models import GeoBucket, Property


pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]


def test_python_seed_is_repeatable_and_matches_h3(postgres_url, clean_database, client):
    environment = {**os.environ, "DATABASE_DSN": postgres_url}
    for expected in [5, 0]:
        result = subprocess.run(
            [sys.executable, str(ROOT / "seed.py")], env=environment, cwd=ROOT,
            capture_output=True, text=True, check=True, timeout=30,
        )
        assert f"inserted {expected} properties" in result.stdout
    with clean_database.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(Property)) == 5
        assert set(connection.execute(select(Property.currency, Property.currency_unit_multiplier)).all()) == {("NGN", 100)}
        rows = connection.execute(
            select(Property.lat, Property.lng, GeoBucket.h3_index)
            .join(GeoBucket, Property.bucket_id == GeoBucket.id)
        )
        for lat, lng, cell in rows:
            assert h3.latlng_to_cell(lat, lng, 8) == cell
    response = client.get("/api/properties/search?location=sangotedo")
    assert response.status_code == 200
    assert response.json()["total"] == 3
    for item in response.json()["items"]:
        assert "currency" not in item
        assert "currency_unit_multiplier" not in item
