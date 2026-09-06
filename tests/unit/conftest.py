from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database.db import get_db
from main import app
from models import PropertyRead


@pytest.fixture
def mock_database():
    return MagicMock(spec=Session)


@pytest.fixture
def client(mock_database):
    app.dependency_overrides[get_db] = lambda: mock_database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def property_result(property_payload):
    return PropertyRead(
        **property_payload, id=uuid4(), bucket_id=uuid4(),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
