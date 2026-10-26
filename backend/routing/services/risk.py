from dataclasses import dataclass, field
from enum import IntEnum


class Level(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

    @property
    def label(self):
        return _LABELS[self]


_LABELS = {
    Level.LOW: "Low",
    Level.MODERATE: "Moderate",
    Level.HIGH: "High",
    Level.SEVERE: "Severe",
    Level.NO_TRAVEL: "No Travel",
}


@dataclass(frozen=True)
class Scale:
    name: str
    unit: str
    thresholds: tuple
    strict_top: bool

    def level(self, value):
        t = self.thresholds
        if value > t[3] or (value == t[3] and not self.strict_top):
            return Level.NO_TRAVEL
        for level in (Level.SEVERE, Level.HIGH, Level.MODERATE):
            if value >= t[level - 1]:
                return level
        return Level.LOW

    def score(self, value):
        knots = (0.0, *self.thresholds)
        if value >= knots[-1]:
            return 4.0
        for i in range(4):
            lo, hi = knots[i], knots[i + 1]
            if value < hi:
                return i + max(0.0, value - lo) / (hi - lo)
        return 4.0


WIND = Scale("Wind", "mph", (25, 35, 45, 55), strict_top=False)
RAIN = Scale("Rain", "in/hr", (0.10, 0.25, 0.50, 1.00), strict_top=True)
SNOW = Scale("Snow", "in/hr", (0.5, 1.0, 2.0, 3.0), strict_top=True)

LOAD_NO_TRAVEL_LB = 30_000  # with 45–54 mph wind
LOAD_SEVERE_LB = 40_000  # with 35–44 mph wind


@dataclass(frozen=True)
class Assessment:
    level: Level
    score: float  # continuous 0..4, always within [level, level + 1)
    reasons: list = field(default_factory=list)


def _fmt(value, scale):
    return f"{value:.0f} {scale.unit}" if scale is WIND else f"{value:.2f} {scale.unit}"


def load_adjusted_level(wind_mph, load_lb):
    if 45 <= wind_mph < 55 and load_lb > LOAD_NO_TRAVEL_LB:
        return Level.NO_TRAVEL
    if 35 <= wind_mph < 45 and load_lb > LOAD_SEVERE_LB:
        return Level.SEVERE
    return None


def assess(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    level = Level.LOW
    reasons = []
    for scale, value in ((WIND, wind_mph), (RAIN, rain_in_hr), (SNOW, snow_in_hr)):
        scale_level = scale.level(value)
        if scale_level > Level.LOW:
            reasons.append(f"{scale.name} {_fmt(value, scale)} ({scale_level.label})")
        level = max(level, scale_level)

    load_level = load_adjusted_level(wind_mph, load_lb)
    if load_level is not None and load_level > level:
        reasons.append(
            f"Wind {wind_mph:.0f} mph with {load_lb:,} lb load ({load_level.label})"
        )
        level = load_level

    raw = max(WIND.score(wind_mph), RAIN.score(rain_in_hr), SNOW.score(snow_in_hr))
    score = min(max(raw, float(level)), level + 0.99)
    return Assessment(level=level, score=round(score, 2), reasons=reasons)
