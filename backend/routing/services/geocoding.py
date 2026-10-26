
import hashlib
import re
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache

_COORDS = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


class GeocodingError(Exception):
    pass


@dataclass(frozen=True)
class Place:
    lat: float
    lon: float
    label: str

    @property
    def point(self):
        return (self.lat, self.lon)


def geocode(query):
    query = query.strip()
    match = _COORDS.match(query)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise GeocodingError(f"Coordinates out of range: {query}")
        return Place(lat, lon, f"{lat:.4f}, {lon:.4f}")

    cache_key = "geocode:" + hashlib.sha1(query.lower().encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(
            settings.NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": settings.HTTP_USER_AGENT},
            timeout=settings.HTTP_TIMEOUT_S,
        )
        resp.raise_for_status()
        results = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise GeocodingError(f"Geocoding service unavailable: {exc}") from exc

    if not results:
        raise GeocodingError(f'Could not find "{query}".')
    top = results[0]
    place = Place(float(top["lat"]), float(top["lon"]), top.get("display_name", query))
    cache.set(cache_key, place, 24 * 3600)
    return place
