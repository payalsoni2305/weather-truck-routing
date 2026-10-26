

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.core.cache import cache

HOURLY_VARS = (
    "temperature_2m",
    "wind_speed_10m",
    "wind_gusts_10m",
    "rain",
    "showers",
    "snowfall",
    "weather_code",
)
SNAP_DEG = 0.05
CHUNK_SIZE = 100
MAX_WORKERS = 4


class WeatherError(Exception):
    pass


@dataclass(frozen=True)
class WeatherSample:
    temp_f: float
    wind_mph: float
    gust_mph: float
    rain_in_hr: float  
    snow_in_hr: float
    weather_code: int | None

    def as_dict(self):
        return {
            "temp_f": round(self.temp_f, 1),
            "wind_mph": round(self.wind_mph, 1),
            "gust_mph": round(self.gust_mph, 1),
            "rain_in_hr": round(self.rain_in_hr, 3),
            "snow_in_hr": round(self.snow_in_hr, 3),
            "weather_code": self.weather_code,
        }


class HourlySeries:
    def __init__(self, times, values):
        self.times = times 
        self.values = values 

    def _value(self, var, i):
        v = self.values[var][i]
        return 0.0 if v is None else float(v)

    def at(self, ts):
        times = self.times
        if ts <= times[0]:
            i, f = 0, 0.0
        elif ts >= times[-1]:
            i, f = len(times) - 1, 0.0
        else:
            i = int((ts - times[0]) // 3600)
            i = min(i, len(times) - 2)
            f = (ts - times[i]) / (times[i + 1] - times[i])

        def interp(var):
            a = self._value(var, i)
            b = self._value(var, i + 1) if f > 0 else a
            return a + (b - a) * f

        code = self.values["weather_code"][i + 1 if f >= 0.5 else i]
        return WeatherSample(
            temp_f=interp("temperature_2m"),
            wind_mph=interp("wind_speed_10m"),
            gust_mph=interp("wind_gusts_10m"),
            rain_in_hr=interp("rain") + interp("showers"),
            snow_in_hr=interp("snowfall"),
            weather_code=None if code is None else int(code),
        )


def _snap(point):
    return (round(point[0] / SNAP_DEG) * SNAP_DEG, round(point[1] / SNAP_DEG) * SNAP_DEG)


def _floor_hour(ts):
    return int(ts // 3600 * 3600)


def _ceil_hour(ts):
    return int(math.ceil(ts / 3600) * 3600)


def fetch_hourly(points, start_ts, end_ts):
    start, end = _floor_hour(start_ts), _ceil_hour(end_ts) + 3600
    keys = [_snap(p) for p in points]
    results, missing = {}, []
    for key in dict.fromkeys(keys):
        cached = cache.get(_cache_key(key, start, end))
        if cached is not None:
            results[key] = cached
        else:
            missing.append(key)

    chunks = [missing[i : i + CHUNK_SIZE] for i in range(0, len(missing), CHUNK_SIZE)]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for chunk, series_list in zip(chunks, pool.map(lambda c: _request(c, start, end), chunks)):
            for key, series in zip(chunk, series_list):
                results[key] = series
                cache.set(_cache_key(key, start, end), series)
    return [results[k] for k in keys]


def _cache_key(key, start, end):
    return f"wx:{key[0]:.2f}:{key[1]:.2f}:{start}:{end}"


def _iso_hour(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")


def _request(locations, start, end):
    params = {
        "latitude": ",".join(f"{lat:.2f}" for lat, _ in locations),
        "longitude": ",".join(f"{lon:.2f}" for _, lon in locations),
        "hourly": ",".join(HOURLY_VARS),
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "temperature_unit": "fahrenheit",
        "timezone": "GMT",
        "timeformat": "unixtime",
        "start_hour": _iso_hour(start),
        "end_hour": _iso_hour(end),
    }
    try:
        resp = requests.get(
            settings.OPEN_METEO_URL,
            params=params,
            headers={"User-Agent": settings.HTTP_USER_AGENT},
            timeout=settings.HTTP_TIMEOUT_S,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherError(f"Weather service unavailable: {exc}") from exc
    if resp.status_code != 200 or (isinstance(data, dict) and data.get("error")):
        reason = data.get("reason") if isinstance(data, dict) else resp.status_code
        raise WeatherError(f"Weather request failed: {reason}")

    items = data if isinstance(data, list) else [data]
    return [
        HourlySeries(item["hourly"]["time"], {v: item["hourly"][v] for v in HOURLY_VARS})
        for item in items
    ]
