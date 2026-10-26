import pytest

from routing.services.recommend import rank, recommend, summarize
from routing.services.risk import Level

L, M, H, S, N = Level.LOW, Level.MODERATE, Level.HIGH, Level.SEVERE, Level.NO_TRAVEL


def make(route_id, levels, duration_h=10, interval=25):
    miles = [i * interval for i in range(len(levels))]
    return summarize(route_id, miles[-1], duration_h * 3600, miles, levels)


def test_nearest_checkpoint_attribution():
    s = make("A", [L, S, L, L, L])  # 100 miles, checkpoints every 25
    assert s.severe_mi == pytest.approx(25)
    assert s.miles_by_level[L] == pytest.approx(75)
    assert s.avg_risk == pytest.approx(3 * 25 / 100)


def test_endpoints_cover_half_a_gap():
    s = make("A", [H, L, L, L, L])
    assert s.high_mi == pytest.approx(12.5)


def test_fewest_severe_beats_faster_route():
    fast = make("A", [L, S, L, L, L], duration_h=8)
    slow = make("B", [L, H, H, L, L], duration_h=12)
    assert [s.route_id for s in rank([fast, slow])] == ["B", "A"]


def test_no_travel_ranks_worse_than_severe():
    blocked = make("A", [L, N, L, L, L])
    severe = make("B", [L, S, S, L, L])
    assert rank([blocked, severe])[0].route_id == "B"


def test_high_miles_break_severe_tie():
    a = make("A", [L, H, H, L, L], duration_h=8)
    b = make("B", [L, H, L, L, L], duration_h=12)
    assert rank([a, b])[0].route_id == "B"


def test_average_risk_then_time():
    a = make("A", [M, M, M, M, M], duration_h=8)
    b = make("B", [L, L, L, L, L], duration_h=12)
    c = make("C", [L, L, L, L, L], duration_h=10)
    assert [s.route_id for s in rank([a, b, c])] == ["C", "B", "A"]


def test_recommendation_reason_and_warning():
    a = make("A", [L, N, L, L, L])
    b = make("B", [L, N, N, L, L])
    ranked, reason, warning = recommend([a, b])
    assert ranked[0].route_id == "A"
    assert "No Travel miles" in reason
    assert warning is not None
