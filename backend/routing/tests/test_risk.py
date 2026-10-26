import pytest

from routing.services.risk import RAIN, SNOW, WIND, Level, assess

L, M, H, S, N = Level.LOW, Level.MODERATE, Level.HIGH, Level.SEVERE, Level.NO_TRAVEL


@pytest.mark.parametrize(
    "mph, expected",
    [(0, L), (24.9, L), (25, M), (34.9, M), (35, H), (44.9, H), (45, S), (54.9, S), (55, N), (80, N)],
)
def test_wind_thresholds(mph, expected):
    assert WIND.level(mph) == expected


@pytest.mark.parametrize(
    "inches, expected",
    [(0, L), (0.09, L), (0.10, M), (0.24, M), (0.25, H), (0.49, H), (0.50, S), (1.00, S), (1.01, N)],
)
def test_rain_thresholds(inches, expected):
    assert RAIN.level(inches) == expected


@pytest.mark.parametrize(
    "inches, expected",
    [(0, L), (0.49, L), (0.5, M), (1.0, H), (2.0, S), (3.0, S), (3.1, N)],
)
def test_snow_thresholds(inches, expected):
    assert SNOW.level(inches) == expected


def test_worst_condition_wins():
    result = assess(wind_mph=10, rain_in_hr=0.3, snow_in_hr=2.5, load_lb=10_000)
    assert result.level == S
    assert len(result.reasons) == 2


def test_wind_55_is_no_travel_for_any_load():
    assert assess(55, 0, 0, load_lb=1).level == N


@pytest.mark.parametrize("load, expected", [(30_000, S), (30_001, N)])
def test_strong_wind_heavy_load_no_travel(load, expected):
    assert assess(48, 0, 0, load).level == expected


@pytest.mark.parametrize("load, expected", [(40_000, H), (40_001, S)])
def test_high_wind_heavy_load_severe(load, expected):
    assert assess(38, 0, 0, load).level == expected


def test_load_rule_does_not_lower_risk():
    # 38 mph + heavy load is Severe, but heavy snow already makes it No Travel.
    assert assess(38, 0, 3.5, 45_000).level == N


@pytest.mark.parametrize("wind", [0, 12, 25, 30, 40, 50, 60])
def test_score_is_consistent_with_level(wind):
    result = assess(wind, 0.2, 0.7, 35_000)
    assert int(result.level) <= result.score < int(result.level) + 1
