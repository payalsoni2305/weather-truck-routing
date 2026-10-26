from dataclasses import dataclass

from .risk import Level


@dataclass
class RouteSummary:
    route_id: str
    distance_mi: float
    duration_s: float
    miles_by_level: dict  # Level -> miles
    avg_risk: float
    max_level: Level

    @property
    def no_travel_mi(self):
        return self.miles_by_level[Level.NO_TRAVEL]

    @property
    def severe_mi(self):
        return self.miles_by_level[Level.SEVERE]

    @property
    def high_mi(self):
        return self.miles_by_level[Level.HIGH]

    def as_dict(self):
        return {
            "miles_by_level": {lvl.label: round(m, 1) for lvl, m in self.miles_by_level.items()},
            "avg_risk": round(self.avg_risk, 2),
            "max_level": int(self.max_level),
            "max_level_label": self.max_level.label,
        }


def summarize(route_id, distance_mi, duration_s, checkpoint_miles, levels):
    miles = {lvl: 0.0 for lvl in Level}
    n = len(checkpoint_miles)
    for i in range(n):
        start = 0.0 if i == 0 else (checkpoint_miles[i - 1] + checkpoint_miles[i]) / 2
        end = distance_mi if i == n - 1 else (checkpoint_miles[i] + checkpoint_miles[i + 1]) / 2
        miles[levels[i]] += max(0.0, end - start)

    total = sum(miles.values()) or 1.0
    avg = sum(int(lvl) * m for lvl, m in miles.items()) / total
    return RouteSummary(
        route_id=route_id,
        distance_mi=distance_mi,
        duration_s=duration_s,
        miles_by_level=miles,
        avg_risk=avg,
        max_level=max(levels),
    )


def _fmt_miles(v):
    return f"{v:.0f} mi"


def _fmt_duration(seconds):
    minutes = round(seconds / 60)
    return f"{minutes // 60}h {minutes % 60:02d}m"


CRITERIA = (
    ("No Travel miles", lambda s: round(s.no_travel_mi), lambda s: _fmt_miles(s.no_travel_mi)),
    ("Severe miles", lambda s: round(s.severe_mi), lambda s: _fmt_miles(s.severe_mi)),
    ("High miles", lambda s: round(s.high_mi), lambda s: _fmt_miles(s.high_mi)),
    ("average risk", lambda s: round(s.avg_risk, 1), lambda s: f"{s.avg_risk:.2f}"),
    ("travel time", lambda s: round(s.duration_s / 60), lambda s: _fmt_duration(s.duration_s)),
)


def rank_key(summary):
    return tuple(key(summary) for _, key, _ in CRITERIA)


def rank(summaries):
    return sorted(summaries, key=rank_key)


def compare(winner, other):
    for label, key, fmt in CRITERIA:
        if key(winner) != key(other):
            better = "shorter" if label == "travel time" else "lower" if label == "average risk" else "fewer"
            return f"{better} {label} ({fmt(winner)} vs {fmt(other)} on Route {other.route_id})"
    return None


def recommend(summaries):
    ranked = rank(summaries)
    best = ranked[0]
    if len(ranked) == 1:
        reason = f"Route {best.route_id} is the only available route."
    else:
        why = compare(best, ranked[1])
        reason = (
            f"Route {best.route_id}: {why}."
            if why
            else f"Route {best.route_id} ties with Route {ranked[1].route_id}; chosen as fastest."
        )

    warning = None
    if best.no_travel_mi > 0:
        warning = "Every route crosses No Travel conditions. Consider delaying departure."
    elif best.severe_mi > 0:
        warning = "Every route has Severe weather segments. Drive with extreme caution."
    return ranked, reason, warning
