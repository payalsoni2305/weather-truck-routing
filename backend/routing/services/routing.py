import bisect
import math
from dataclasses import dataclass

import requests
from django.conf import settings

from .geo import approx_distance_mi, decimate, haversine_mi, lerp_point

ROUTE_IDS = "ABCDE"
MAX_DETOUR_RATIO = 1.6 
MAX_OVERLAP = 0.8 
VIA_OFFSETS = (0.15, -0.15, 0.3, -0.3)

class RoutingError(Exception):
    pass


@dataclass
class Route:
    points: list  
    cum_miles: list  
    cum_seconds: list 
    id: str = ""

    @property
    def distance_mi(self):
        return self.cum_miles[-1]

    @property
    def duration_s(self):
        return self.cum_seconds[-1]

    def locate(self, mile):
        mile = min(max(mile, 0.0), self.distance_mi)
        i = min(bisect.bisect_right(self.cum_miles, mile) - 1, len(self.points) - 2)
        seg = self.cum_miles[i + 1] - self.cum_miles[i]
        f = (mile - self.cum_miles[i]) / seg if seg > 0 else 0.0
        lat, lon = lerp_point(self.points[i], self.points[i + 1], f)
        t = self.cum_seconds[i] + (self.cum_seconds[i + 1] - self.cum_seconds[i]) * f
        return lat, lon, t


def fetch_routes(origin, destination, count=3):
    routes = _request([origin, destination], alternatives=count)
    if not routes:
        raise RoutingError("No route found between these locations.")

    fastest = min(r.duration_s for r in routes)
    for via in _via_points(origin, destination):
        if len(routes) >= count:
            break
        try:
            candidates = _request([origin, via, destination], alternatives=0)
        except RoutingError:
            continue
        for candidate in candidates:
            if candidate.duration_s <= fastest * MAX_DETOUR_RATIO and _is_distinct(
                candidate, routes
            ):
                routes.append(candidate)

    routes = sorted(routes[:count], key=lambda r: r.duration_s)
    for route, route_id in zip(routes, ROUTE_IDS):
        route.id = route_id
    return routes


def _request(coords, alternatives):
    path = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    params = {
        "overview": "full",
        "geometries": "geojson",
        "annotations": "duration",
        "steps": "false",
        "alternatives": str(alternatives) if alternatives else "false",
    }
    try:
        resp = requests.get(
            f"{settings.OSRM_BASE_URL}/route/v1/driving/{path}",
            params=params,
            headers={"User-Agent": settings.HTTP_USER_AGENT},
            timeout=settings.HTTP_TIMEOUT_S,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise RoutingError(f"Routing service unavailable: {exc}") from exc
    if data.get("code") != "Ok":
        raise RoutingError(data.get("message") or f"Routing failed ({data.get('code')}).")
    return [_parse(raw) for raw in data["routes"]]


def _parse(raw):
    points = [(lat, lon) for lon, lat in raw["geometry"]["coordinates"]]
    seg_miles = [haversine_mi(a, b) for a, b in zip(points, points[1:])]

    seg_seconds = [d for leg in raw["legs"] for d in leg.get("annotation", {}).get("duration", [])]
    if len(seg_seconds) != len(seg_miles):
        total = sum(seg_miles) or 1.0
        seg_seconds = [raw["duration"] * m / total for m in seg_miles]

    factor = settings.TRUCK_DURATION_FACTOR
    cum_miles, cum_seconds = [0.0], [0.0]
    for miles, seconds in zip(seg_miles, seg_seconds):
        cum_miles.append(cum_miles[-1] + miles)
        cum_seconds.append(cum_seconds[-1] + seconds * factor)
    return Route(points=points, cum_miles=cum_miles, cum_seconds=cum_seconds)


def _via_points(origin, destination):
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    kx = math.cos(math.radians(mid_lat))
    dx = (destination[1] - origin[1]) * kx
    dy = destination[0] - origin[0]
    length = math.hypot(dx, dy)
    if length == 0:
        return []
    px, py = -dy / length, dx / length
    return [
        (mid_lat + py * frac * length, mid_lon + px * frac * length / kx)
        for frac in VIA_OFFSETS
    ]


def _overlap(base, other):
    """Fraction of `other`'s path that runs along `base`."""
    base_pts = decimate(base.points, 600)
    tolerance = max(0.5, base.distance_mi / len(base_pts))
    sample = decimate(other.points, 120)
    near = 0
    for p in sample:
        if any(
            abs(p[0] - q[0]) < 0.1 and approx_distance_mi(p, q) <= tolerance for q in base_pts
        ):
            near += 1
    return near / len(sample)


def _is_distinct(candidate, routes):
    return all(_overlap(r, candidate) < MAX_OVERLAP for r in routes)
