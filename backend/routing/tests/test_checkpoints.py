import pytest

from routing.services.checkpoints import build_checkpoints
from routing.services.geo import haversine_mi
from routing.services.routing import Route
from routing.services.weather import HourlySeries


def straight_route(miles=103, mph=50):
    """A due-north route sampled every ~1 mile at constant speed."""
    deg_per_mile = 1 / 69.05
    points = [(40 + i * deg_per_mile, -100.0) for i in range(miles + 1)]
    cum_miles = [0.0]
    for a, b in zip(points, points[1:]):
        cum_miles.append(cum_miles[-1] + haversine_mi(a, b))
    cum_seconds = [m / mph * 3600 for m in cum_miles]
    return Route(points=points, cum_miles=cum_miles, cum_seconds=cum_seconds, id="A")


@pytest.mark.parametrize("interval", [10, 25, 50])
def test_checkpoint_spacing_and_destination(interval):
    route = straight_route()
    cps = build_checkpoints(route, interval)
    assert cps[0].mile == 0
    assert cps[-1].mile == pytest.approx(route.distance_mi)
    for a, b in zip(cps[:-2], cps[1:-1]):
        assert b.mile - a.mile == pytest.approx(interval)


def test_checkpoint_eta_matches_speed():
    route = straight_route(mph=50)
    cps = build_checkpoints(route, 25)
    assert cps[1].offset_s == pytest.approx(25 / 50 * 3600, rel=1e-3)


def test_hourly_series_interpolates_between_hours():
    vars_ = {
        "temperature_2m": [30, 40],
        "wind_speed_10m": [20, 40],
        "wind_gusts_10m": [30, 50],
        "rain": [0.0, 0.2],
        "showers": [0.0, 0.0],
        "snowfall": [None, None],
        "weather_code": [1, 61],
    }
    series = HourlySeries([0, 3600], vars_)
    sample = series.at(1800)
    assert sample.wind_mph == pytest.approx(30)
    assert sample.rain_in_hr == pytest.approx(0.1)
    assert sample.snow_in_hr == 0
    assert series.at(99_999).wind_mph == 40  # clamps past the end
