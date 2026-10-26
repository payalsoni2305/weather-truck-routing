import math

from .geo import MILES_PER_DEG_LAT, approx_distance_mi, decimate
from .risk import assess
from .weather import fetch_hourly

CORRIDOR_MI = 50
MAX_CELLS = 400
PAD_DEG = 0.5
MIN_CELL_DEG = 0.1


def _grid(corridor):
    pts = decimate(corridor, 300)
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    south, north = min(lats) - PAD_DEG, max(lats) + PAD_DEG
    west, east = min(lons) - PAD_DEG, max(lons) + PAD_DEG

    area = (north - south) * (east - west)
    cell = max(MIN_CELL_DEG, math.sqrt(area / (MAX_CELLS * 3)))
    while True:
        rows = math.ceil((north - south) / cell)
        cols = math.ceil((east - west) / cell)
        reach = CORRIDOR_MI + cell * MILES_PER_DEG_LAT / 2
        reach_deg = reach / MILES_PER_DEG_LAT
        kept = []
        for r in range(rows):
            lat = north - (r + 0.5) * cell
            nearby = [p for p in pts if abs(p[0] - lat) <= reach_deg]
            if not nearby:
                continue
            for c in range(cols):
                center = (lat, west + (c + 0.5) * cell)
                if any(approx_distance_mi(center, p) <= reach for p in nearby):
                    kept.append((r * cols + c, center))
        if len(kept) <= MAX_CELLS:
            bounds = [[north - rows * cell, west], [north, west + cols * cell]]
            return bounds, rows, cols, cell, kept
        cell *= 1.2


def build_heatmap(corridor, start_ts, hours, load_lb):
    bounds, rows, cols, cell, kept = _grid(corridor)
    start_ts = int(start_ts // 3600 * 3600)
    series = fetch_hourly([center for _, center in kept], start_ts, start_ts + hours * 3600)

    frames = []
    for h in range(hours + 1):
        ts = start_ts + h * 3600
        frame = []
        for s in series:
            w = s.at(ts)
            frame.append(assess(w.wind_mph, w.rain_in_hr, w.snow_in_hr, load_lb).score)
        frames.append(frame)

    return {
        "bounds": bounds,
        "rows": rows,
        "cols": cols,
        "cell_deg": round(cell, 4),
        "start": start_ts,
        "hours": hours,
        "cells": [idx for idx, _ in kept],
        "scores": frames,
    }
