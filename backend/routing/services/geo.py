
import math

EARTH_RADIUS_MI = 3958.8
MILES_PER_DEG_LAT = 69.0


def haversine_mi(a, b):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MI * math.asin(math.sqrt(h))


def approx_distance_mi(a, b):
    """Equirectangular distance: fast and accurate enough for short ranges."""
    kx = math.cos(math.radians((a[0] + b[0]) / 2))
    dx = (b[1] - a[1]) * kx
    dy = b[0] - a[0]
    return math.hypot(dx, dy) * MILES_PER_DEG_LAT


def lerp_point(a, b, fraction):
    return (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)


def decimate(items, max_items):
    """Evenly thin a sequence down to at most `max_items`, keeping both ends."""
    items = list(items)
    if len(items) <= max_items:
        return items
    step = (len(items) - 1) / (max_items - 1)
    return [items[round(i * step)] for i in range(max_items)]
