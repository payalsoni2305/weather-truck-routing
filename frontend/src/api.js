const BASE = import.meta.env.VITE_API_BASE ?? "";

async function post(path, body, signal) {
  const resp = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  const data = await resp.json().catch(() => null);
  if (!resp.ok) throw new Error(errorMessage(data, resp.status));
  return data;
}

function errorMessage(data, status) {
  if (data && typeof data === "object") {
    if (typeof data.detail === "string") return data.detail;
    const parts = Object.entries(data).map(
      ([field, msgs]) => `${field.replace(/_/g, " ")}: ${[].concat(msgs).join(" ")}`,
    );
    if (parts.length) return parts.join("; ");
  }
  return `Request failed (${status})`;
}

export const planTrip = (req, signal) => post("/api/plan", req, signal);

export const fetchHeatmap = (body, signal) => post("/api/heatmap", body, signal);
