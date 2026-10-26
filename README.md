# Weather-Aware Truck Routing

Plan a truck trip and pick the safest of three routes based on the weather the truck will meet **at the time it reaches each point** on the road.

Enter an origin, destination, departure time and load weight. The app:

1. Gets up to 3 alternative routes from OSRM.
2. Places checkpoints every 10, 25 or 50 miles and estimates the truck's ETA at each one.
3. Reads the hourly forecast (Open-Meteo) at every checkpoint for that ETA.
4. Scores wind, rain and snow into a risk level (Low → No Travel), raising it for heavy loads in strong wind.
5. Recommends a route: fewest Severe miles → fewest High miles → lowest average risk → shortest time.
6. Shows everything on a map with a weather-risk heatmap and a 0–48 h forecast slider.

## Tech stack

- **Backend:** Django 5 + Django REST Framework. Stateless, so there is no database; results are cached in memory.
- **Frontend:** React 18 + Vite + Leaflet (react-leaflet).
- **External APIs (free, no keys):** [OSRM](https://project-osrm.org/) routing, [Open-Meteo](https://open-meteo.com/) forecasts, [Nominatim](https://nominatim.org/) geocoding.

## Risk rules

| Level | Wind (mph) | Rain (in/hr) | Snow (in/hr) |
|---|---|---|---|
| Low | < 25 | < 0.10 | < 0.5 |
| Moderate | 25–34 | 0.10–0.25 | 0.5–1.0 |
| High | 35–44 | 0.25–0.50 | 1.0–2.0 |
| Severe | 45–54 | 0.50–1.00 | 2.0–3.0 |
| No Travel | ≥ 55 | > 1.00 | > 3.0 |

Load rules: wind ≥ 55 mph → No Travel for any load; 45–54 mph with a load over 30,000 lb → No Travel; 35–44 mph with a load over 40,000 lb → Severe.

## Project layout

```
backend/
  config/            Django settings and URLs
  routing/
    services/        geocoding, routing, checkpoints, weather, risk, recommend, heatmap, planner
    serializers.py   request validation
    views.py         POST /api/plan, POST /api/heatmap, GET /api/health
    tests/           pytest suite
frontend/
  src/               App.jsx, api.js, components/ (map, form, route list, slider…)
Dockerfile           builds the frontend, then serves it and the API with gunicorn
render.yaml          one-click Render deployment
```

## Run locally

Backend (Python 3.10+):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
python manage.py runserver
```

Frontend (Node 18+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` requests to Django on port 8000.

## Run with Docker

```bash
docker build -t truck-routing .
docker run -p 8000:8000 truck-routing
```

Open http://localhost:8000. The container serves both the built React app and the API.

## Deploy on Render

The repo includes `render.yaml`. In Render choose **New → Blueprint**, select this repository and apply it. Render builds the Dockerfile, generates `DJANGO_SECRET_KEY` and checks `/api/health`.

## API

`POST /api/plan`

```json
{
  "origin": "Denver, CO",
  "destination": "Chicago, IL",
  "departure": "2026-10-27T08:00:00Z",
  "load_weight_lb": 35000,
  "interval_miles": 25
}
```

Returns the routes with geometry, checkpoints (ETA, weather, risk level, reasons), per-route summaries and the recommendation.

`POST /api/heatmap` takes `corridor` (a list of `[lat, lon]`), `departure`, `load_weight_lb` and `hours`. It returns a grid of risk scores for each forecast hour.
