import { memo, useEffect, useMemo } from "react";
import L from "leaflet";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { formatDuration, formatMiles, formatTime } from "../format";
import { positionAt, sliderTime } from "../geometry";
import { LEVEL_COLORS, ROUTE_COLORS } from "../risk";
import HeatmapLayer from "./HeatmapLayer";

const pin = (label, cls) =>
  L.divIcon({ className: "", html: `<div class="pin ${cls}">${label}</div>`, iconSize: [28, 28], iconAnchor: [14, 14] });
const START_ICON = pin("S", "pin-start");
const END_ICON = pin("E", "pin-end");
const TRUCK_ICON = L.divIcon({ className: "", html: '<div class="truck">🚚</div>', iconSize: [30, 30], iconAnchor: [15, 15] });

function FitToPlan({ plan }) {
  const map = useMap();
  useEffect(() => {
    if (!plan) return;
    const bounds = L.latLngBounds(plan.routes.flatMap((r) => r.geometry.map(([lat, lon]) => [lat, lon])));
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [map, plan]);
  return null;
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.flyTo([focus.lat, focus.lon], Math.max(map.getZoom(), 9), { duration: 0.8 });
  }, [map, focus]);
  return null;
}

const RouteLayer = memo(function RouteLayer({ route, selected, onSelect }) {
  const positions = useMemo(() => route.geometry.map(([lat, lon]) => [lat, lon]), [route]);
  const s = route.summary;
  return (
    <>
      <Polyline
        positions={positions}
        pathOptions={{
          color: ROUTE_COLORS[route.id],
          weight: selected ? 6 : 4,
          opacity: selected ? 0.95 : 0.5,
          dashArray: selected ? undefined : "8 8",
        }}
        eventHandlers={{ click: () => onSelect(route.id) }}
      >
        <Tooltip sticky>
          <strong>
            Route {route.id}
            {route.recommended ? " (recommended)" : ""}
          </strong>
          <br />
          {formatMiles(route.distance_mi)} · {formatDuration(route.duration_s)} · arrive {formatTime(route.arrival)}
          <br />
          Severe {formatMiles(s.miles_by_level.Severe)} · High {formatMiles(s.miles_by_level.High)} · avg risk{" "}
          {s.avg_risk.toFixed(2)}
        </Tooltip>
      </Polyline>
      {route.checkpoints.map((cp) => (
        <CircleMarker
          key={cp.mile}
          center={[cp.lat, cp.lon]}
          radius={selected ? 6 : 3.5}
          pathOptions={{
            color: selected ? "#fff" : LEVEL_COLORS[cp.level],
            weight: selected ? 1.5 : 1,
            fillColor: LEVEL_COLORS[cp.level],
            fillOpacity: selected ? 1 : 0.6,
          }}
          eventHandlers={{ click: () => onSelect(route.id) }}
        >
          <Popup>
            <div className="cp-popup">
              <strong>
                Route {route.id} · mile {Math.round(cp.mile)}
              </strong>
              <div>ETA {formatTime(cp.eta)}</div>
              <div>
                Risk: <b style={{ color: LEVEL_COLORS[cp.level] }}>{cp.level_label}</b>
              </div>
              <div>
                Wind {Math.round(cp.weather.wind_mph)} mph (gust {Math.round(cp.weather.gust_mph)}) · {Math.round(cp.weather.temp_f)}°F
              </div>
              <div>
                Rain {cp.weather.rain_in_hr.toFixed(2)} in/hr · Snow {cp.weather.snow_in_hr.toFixed(2)} in/hr
              </div>
              {cp.reasons.length > 0 && (
                <ul>
                  {cp.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  );
});

export default function MapView({ plan, selectedId, onSelect, heatmap, hour, focus }) {
  const selected = plan?.routes.find((r) => r.id === selectedId) ?? null;
  // Draw the selected route last so it sits on top.
  const ordered = plan ? [...plan.routes].sort((a, b) => Number(a.id === selectedId) - Number(b.id === selectedId)) : [];

  const truck = useMemo(() => {
    if (!plan || !selected) return null;
    const elapsed = (sliderTime(plan.departure, hour) - Date.parse(plan.departure)) / 1000;
    return positionAt(selected, Math.max(0, elapsed));
  }, [plan, selected, hour]);

  return (
    <MapContainer center={[39.5, -98.35]} zoom={4} zoomSnap={0.5} preferCanvas className="map">
      <TileLayer
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
        className="basemap"
      />
      {heatmap && <HeatmapLayer data={heatmap} hour={hour} />}
      {ordered.map((route) => (
        <RouteLayer key={route.id} route={route} selected={route.id === selectedId} onSelect={onSelect} />
      ))}
      {plan && (
        <>
          <Marker position={[plan.origin.lat, plan.origin.lon]} icon={START_ICON}>
            <Tooltip>{plan.origin.label}</Tooltip>
          </Marker>
          <Marker position={[plan.destination.lat, plan.destination.lon]} icon={END_ICON}>
            <Tooltip>{plan.destination.label}</Tooltip>
          </Marker>
        </>
      )}
      {truck && <Marker position={truck} icon={TRUCK_ICON} interactive={false} />}
      <FitToPlan plan={plan} />
      <FlyTo focus={focus} />
    </MapContainer>
  );
}
