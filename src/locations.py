import re
import unicodedata

import h3


def normalize_location(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w\s]|_", " ", normalized).split())


def location_aliases(value: str) -> list[str]:
    full = normalize_location(value)
    words = full.split()
    while len(words) > 1 and words[-1] in {"lagos", "ajah"}:
        words.pop()
    return sorted({full, " ".join(words)} - {""})



def bucket_geometry(lat: float, lng: float) -> tuple[str, str, str]:
    cell = h3.latlng_to_cell(lat, lng, 8)
    centre_lat, centre_lng = h3.cell_to_latlng(cell)
    boundary = list(h3.cell_to_boundary(cell))
    boundary.append(boundary[0])
    coordinates = ", ".join(f"{longitude} {latitude}" for latitude, longitude in boundary)
    return (
        cell,
        f"SRID=4326;POINT({centre_lng} {centre_lat})",
        f"SRID=4326;POLYGON(({coordinates}))",
    )
