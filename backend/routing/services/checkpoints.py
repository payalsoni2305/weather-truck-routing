
from dataclasses import dataclass

MIN_FINAL_GAP_MI = 0.5 

@dataclass(frozen=True)
class Checkpoint:
    mile: float
    lat: float
    lon: float
    offset_s: float 


def build_checkpoints(route, interval_mi):
    """Checkpoints at mile 0, every `interval_mi`, and at the destination."""
    total = route.distance_mi
    miles = []
    mile = 0.0
    while mile < total - MIN_FINAL_GAP_MI:
        miles.append(mile)
        mile += interval_mi
    miles.append(total)

    checkpoints = []
    for m in miles:
        lat, lon, t = route.locate(m)
        checkpoints.append(Checkpoint(mile=m, lat=lat, lon=lon, offset_s=t))
    return checkpoints
