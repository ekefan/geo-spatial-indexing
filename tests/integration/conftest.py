import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from database.db import get_db
from main import app


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def postgres_url():
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer("postgis/postgis:18-3.6-alpine", driver="psycopg2") as container:
        url = container.get_connection_url()
        environment = {**os.environ, "DATABASE_DSN": url}
        for arguments in [("upgrade", "head"), ("check",)]:
            subprocess.run(
                [sys.executable, "-m", "alembic", *arguments],
                cwd=ROOT, env=environment, check=True, timeout=60,
            )
        yield url


@pytest.fixture(scope="session")
def database_engine(postgres_url):
    engine = create_engine(postgres_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def clean_database(database_engine):
    with database_engine.begin() as connection:
        connection.execute(text("TRUNCATE properties, bucket_aliases, geo_buckets"))
    try:
        yield database_engine
    finally:
        with database_engine.begin() as connection:
            connection.execute(text("TRUNCATE properties, bucket_aliases, geo_buckets"))


@pytest.fixture
def database_session(clean_database):
    with Session(clean_database) as session:
        yield session


@pytest.fixture
def client(clean_database):
    def override_database():
        with Session(clean_database) as session:
            yield session

    app.dependency_overrides[get_db] = override_database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def populated_client(client, sangotedo_payloads, property_payload):
    identifiers = set()
    for payload in sangotedo_payloads:
        response = client.post("/api/properties", json=payload)
        assert response.status_code == 201, response.text
        identifiers.add(response.json()["id"])
    unrelated = client.post("/api/properties", json={
        **property_payload, "location_name": "Ikeja", "lat": 6.6018, "lng": 3.3515,
    })
    assert unrelated.status_code == 201, unrelated.text
    return client, identifiers
