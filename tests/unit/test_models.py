import pytest
from pydantic import ValidationError

from models import PropertyCreate


def test_currency_details_are_not_exposed(property_payload):
    model = PropertyCreate(**property_payload)
    assert "currency" not in model.model_dump()
    assert "currency_unit_multiplier" not in model.model_dump()
    assert "currency" not in PropertyCreate.model_json_schema()["properties"]


@pytest.mark.parametrize("changes", [
    {"lat": 91}, {"lng": -181}, {"lat": float("nan")}, {"price": -1},
    {"price": 1.5}, {"bedrooms": -1}, {"bathrooms": True}, {"title": " "},
    {"location_name": "!!!"}, {"currency": "NGN"}, {"currency_unit_multiplier": 100},
])
def test_invalid_property_rejected(property_payload, changes):
    with pytest.raises(ValidationError):
        PropertyCreate(**{**property_payload, **changes})
