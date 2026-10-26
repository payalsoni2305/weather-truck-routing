const HOUR_MS = 3_600_000;


export function sliderTime(departureIso, hour) {
  return Math.floor(Date.parse(departureIso) / HOUR_MS) * HOUR_MS + hour * HOUR_MS;
}


export function positionAt(route, seconds) {
  const g = route.geometry;
  if (!g.length || seconds < 0) return null;
  if (seconds >= g[g.length - 1][2]) return [g[g.length - 1][0], g[g.length - 1][1]];
  let lo = 0;
  let hi = g.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (g[mid][2] <= seconds) lo = mid;
    else hi = mid;
  }
  const span = g[hi][2] - g[lo][2];
  const f = span > 0 ? (seconds - g[lo][2]) / span : 0;
  return [g[lo][0] + (g[hi][0] - g[lo][0]) * f, g[lo][1] + (g[hi][1] - g[lo][1]) * f];
}

export function corridorPoints(routes, perRoute = 250) {
  return routes.flatMap((r) => {
    const step = Math.max(1, Math.floor(r.geometry.length / perRoute));
    return r.geometry.filter((_, i) => i % step === 0).map(([lat, lon]) => [lat, lon]);
  });
}
