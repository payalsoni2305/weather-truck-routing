import { useCallback, useEffect, useRef, useState } from "react";
import { fetchHeatmap, planTrip } from "./api";
import { corridorPoints } from "./geometry";
import TripForm from "./components/TripForm";
import RouteList from "./components/RouteList";
import CheckpointTable from "./components/CheckpointTable";
import MapView from "./components/MapView";
import ForecastSlider from "./components/ForecastSlider";
import Legend from "./components/Legend";

export const FORECAST_HOURS = 48;

export default function App() {
  const [plan, setPlan] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [focus, setFocus] = useState(null);
  const [hour, setHour] = useState(0);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [loading, setLoading] = useState(false);
  const [heatmapLoading, setHeatmapLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const submit = useCallback(async (req) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    setHeatmap(null);
    setFocus(null);
    try {
      const result = await planTrip(req, controller.signal);
      setPlan(result);
      setSelectedId(result.recommendation.route_id);
      setHour(0);
    } catch (e) {
      if (!controller.signal.aborted) setError(e.message);
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!plan) return;
    const controller = new AbortController();
    setHeatmapLoading(true);
    fetchHeatmap(
      {
        corridor: corridorPoints(plan.routes),
        departure: plan.departure,
        load_weight_lb: plan.load_weight_lb,
        hours: FORECAST_HOURS,
      },
      controller.signal,
    )
      .then(setHeatmap)
      .catch((e) => {
        if (!controller.signal.aborted) setError(`Heatmap: ${e.message}`);
      })
      .finally(() => {
        if (!controller.signal.aborted) setHeatmapLoading(false);
      });
    return () => controller.abort();
  }, [plan]);

  const selected = plan?.routes.find((r) => r.id === selectedId) ?? null;

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="brand">
          <h1>Weather-Aware Truck Routing</h1>
          <p>Compare routes by weather risk at the truck's arrival time at each checkpoint.</p>
        </header>
        <TripForm onSubmit={submit} loading={loading} />
        {error && <div className="error" role="alert">{error}</div>}
        {plan && (
          <>
            <RouteList plan={plan} selectedId={selectedId} onSelect={setSelectedId} />
            {selected && <CheckpointTable route={selected} onFocus={setFocus} />}
          </>
        )}
      </aside>

      <main className="map-area">
        <MapView
          plan={plan}
          selectedId={selectedId}
          onSelect={setSelectedId}
          heatmap={showHeatmap ? heatmap : null}
          hour={hour}
          focus={focus}
        />
        <Legend />
        {plan && (
          <ForecastSlider
            departure={plan.departure}
            hour={hour}
            maxHour={FORECAST_HOURS}
            onChange={setHour}
            route={selected}
            heatmapLoading={heatmapLoading}
            showHeatmap={showHeatmap}
            onToggleHeatmap={setShowHeatmap}
          />
        )}
        {loading && <div className="map-loading">Finding routes and sampling weather…</div>}
      </main>
    </div>
  );
}
