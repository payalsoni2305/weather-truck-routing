export const LEVEL_LABELS = ["Low", "Moderate", "High", "Severe", "No Travel"];
export const LEVEL_COLORS = ["#2f9e44", "#e8b600", "#f76707", "#e03131", "#7048e8"];

export const ROUTE_COLORS = {
  A: "#1c7ed6",
  B: "#0b7285",
  C: "#495057",
};

const RGB = LEVEL_COLORS.map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));

export function scoreToRgba(score) {
  const s = Math.min(Math.max(score, 0), 4);
  const i = Math.min(Math.floor(s), 3);
  const f = s - i;
  const [r, g, b] = RGB[i].map((c, k) => Math.round(c + (RGB[i + 1][k] - c) * f));
  const alpha = Math.round(Math.min(70 + s * 50, 230));
  return [r, g, b, alpha];
}
