
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .checkpoints import build_checkpoints
from .geo import decimate
from .geocoding import geocode
from .recommend import compare, recommend, summarize
from .risk import assess
from .routing import fetch_routes
from .weather import fetch_hourly

MAX_GEOMETRY_POINTS = 1500


@dataclass(frozen=True)
class TripRequest:
    origin: str
    destination: str
    departure: datetime
    load_weight_lb: int
    interval_miles: int


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def plan_trip(req):
    origin = geocode(req.origin)
    destination = geocode(req.destination)
    routes = fetch_routes(origin.point, destination.point)
    dep_ts = req.departure.timestamp()

    checkpoints = {r.id: build_checkpoints(r, req.interval_miles) for r in routes}
    flat = [cp for r in routes for cp in checkpoints[r.id]]
    longest = max(r.duration_s for r in routes)
    series = iter(fetch_hourly([(cp.lat, cp.lon) for cp in flat], dep_ts, dep_ts + longest))

    payloads, summaries = {}, []
    for route in routes:
        cp_payload, levels = [], []
        for cp in checkpoints[route.id]:
            eta = dep_ts + cp.offset_s
            weather = next(series).at(eta)
            risk = assess(weather.wind_mph, weather.rain_in_hr, weather.snow_in_hr, req.load_weight_lb)
            levels.append(risk.level)
            cp_payload.append(
                {
                    "mile": round(cp.mile, 1),
                    "lat": round(cp.lat, 5),
                    "lon": round(cp.lon, 5),
                    "eta": _iso(eta),
                    "weather": weather.as_dict(),
                    "level": int(risk.level),
                    "level_label": risk.level.label,
                    "score": risk.score,
                    "reasons": risk.reasons,
                }
            )

        summary = summarize(
            route.id,
            route.distance_mi,
            route.duration_s,
            [cp.mile for cp in checkpoints[route.id]],
            levels,
        )
        summaries.append(summary)
        geometry = decimate(zip(route.points, route.cum_seconds), MAX_GEOMETRY_POINTS)
        payloads[route.id] = {
            "id": route.id,
            "distance_mi": round(route.distance_mi, 1),
            "duration_s": round(route.duration_s),
            "departure": _iso(dep_ts),
            "arrival": _iso(dep_ts + route.duration_s),
            "geometry": [[round(lat, 5), round(lon, 5), round(t)] for (lat, lon), t in geometry],
            "checkpoints": cp_payload,
            "summary": summary.as_dict(),
        }

    ranked, reason, warning = recommend(summaries)
    best = ranked[0]
    result_routes = []
    for position, summary in enumerate(ranked, start=1):
        payload = payloads[summary.route_id]
        payload["rank"] = position
        payload["recommended"] = summary is best
        payload["comparison"] = None if summary is best else compare(best, summary)
        result_routes.append(payload)
    result_routes.sort(key=lambda p: p["id"])

    return {
        "origin": {"lat": origin.lat, "lon": origin.lon, "label": origin.label},
        "destination": {"lat": destination.lat, "lon": destination.lon, "label": destination.label},
        "departure": _iso(dep_ts),
        "load_weight_lb": req.load_weight_lb,
        "interval_miles": req.interval_miles,
        "routes": result_routes,
        "recommendation": {"route_id": best.route_id, "reason": reason, "warning": warning},
    }


def departure_window():
    now = datetime.now(timezone.utc)
    return now - timedelta(hours=1), now + timedelta(days=7)
