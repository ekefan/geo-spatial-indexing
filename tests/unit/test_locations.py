import h3
import pytest

from locations import bucket_geometry, location_aliases, normalize_location


@pytest.mark.parametrize("label", ["Sangotedo", "Sangotedo, Ajah", "sangotedo lagos", " SANGOTEDO, Ajah Lagos "])
def test_neighbourhood_alias(label):
    assert "sangotedo" in location_aliases(label)


def test_multiword_name_is_preserved():
    assert location_aliases("Victoria Island") == ["victoria island"]


def test_unicode_and_punctuation():
    assert normalize_location(" ＳＡＮＧＯＴＥＤＯ,  Lagos! ") == "sangotedo lagos"
    assert location_aliases("!!!") == []


def test_bucket_uses_cell_centre_and_closed_boundary():
    cell, centroid, boundary = bucket_geometry(6.4698, 3.6285)
    latitude, longitude = h3.cell_to_latlng(cell)
    assert h3.get_resolution(cell) == 8
    assert centroid == f"SRID=4326;POINT({longitude} {latitude})"
    points = boundary.removeprefix("SRID=4326;POLYGON((").removesuffix("))").split(", ")
    assert points[0] == points[-1]
