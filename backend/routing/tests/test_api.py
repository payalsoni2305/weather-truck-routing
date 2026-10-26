from datetime import datetime, timedelta, timezone
from unittest import mock

from rest_framework.test import APIClient


def future(hours=2):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def payload(**overrides):
    body = {
        "origin": "Denver, CO",
        "destination": "Chicago, IL",
        "departure": future(),
        "load_weight_lb": 35000,
        "interval_miles": 25,
    }
    body.update(overrides)
    return body


def test_plan_rejects_bad_interval():
    resp = APIClient().post("/api/plan", payload(interval_miles=30), format="json")
    assert resp.status_code == 400
    assert "interval_miles" in resp.json()


def test_plan_rejects_far_future_departure():
    resp = APIClient().post("/api/plan", payload(departure=future(24 * 10)), format="json")
    assert resp.status_code == 400
    assert "departure" in resp.json()


def test_plan_passes_validated_request_to_planner():
    with mock.patch("routing.views.plan_trip", return_value={"ok": True}) as plan:
        resp = APIClient().post("/api/plan", payload(), format="json")
    assert resp.status_code == 200
    req = plan.call_args.args[0]
    assert req.load_weight_lb == 35000 and req.interval_miles == 25


def test_upstream_failure_is_502():
    from routing.services.routing import RoutingError

    with mock.patch("routing.views.plan_trip", side_effect=RoutingError("down")):
        resp = APIClient().post("/api/plan", payload(), format="json")
    assert resp.status_code == 502
    assert resp.json()["detail"] == "down"
