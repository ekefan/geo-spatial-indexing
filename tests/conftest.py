import os

import pytest


os.environ["DATABASE_DSN"] = "postgresql+psycopg://unused:unused@127.0.0.1:1/unused"


@pytest.fixture
def property_payload():
    return {
        "title": "Test apartment", "location_name": "Sangotedo",
        "lat": 6.4698, "lng": 3.6285, "price": 150000000,
        "bedrooms": 2, "bathrooms": 2,
    }


@pytest.fixture
def sangotedo_payloads(property_payload):
    return [
        {**property_payload, "location_name": name, "lat": lat, "lng": lng}
        for name, lat, lng in [
            ("Sangotedo", 6.4698, 3.6285),
            ("Sangotedo, Ajah", 6.4720, 3.6301),
            ("sangotedo lagos", 6.4705, 3.6290),
        ]
    ]
