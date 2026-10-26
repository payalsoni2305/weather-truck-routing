import { useEffect, useState } from "react";
import { formatTime } from "../format";
import { sliderTime } from "../geometry";

const PLAY_STEP_MS = 450;

export default function ForecastSlider({
  departure,
  hour,
  maxHour,
  onChange,
  route,
  heatmapLoading,
  showHeatmap,
  onToggleHeatmap,
}) {
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      onChange(hour >= maxHour ? 0 : hour + 1);
    }, PLAY_STEP_MS);
    return () => window.clearInterval(id);
  }, [playing, hour, maxHour, onChange]);

  const now = sliderTime(departure, hour);
  const elapsed = (now - Date.parse(departure)) / 1000;
  let status = "";
  if (route) {
    if (elapsed < 0) status = `Route ${route.id}: not departed`;
    else if (elapsed >= route.duration_s) status = `Route ${route.id}: arrived`;
    else status = `Route ${route.id}: ${Math.round((elapsed / route.duration_s) * 100)}% of trip`;
  }

  return (
    <div className="slider-panel">
      <div className="slider-top">
        <button type="button" className="play" onClick={() => setPlaying((p) => !p)} aria-label={playing ? "Pause" : "Play"}>
          {playing ? "❚❚" : "▶"}
        </button>
        <div className="slider-label">
          <strong>{formatTime(now)}</strong>
          <span>+{hour}h from departure</span>
        </div>
        <span className="truck-status">{status}</span>
        <label className="toggle">
          <input type="checkbox" checked={showHeatmap} onChange={(e) => onToggleHeatmap(e.target.checked)} />
          Heatmap{heatmapLoading ? " (loading…)" : ""}
        </label>
      </div>
      <input
        type="range"
        min={0}
        max={maxHour}
        step={1}
        value={hour}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label="Forecast hour"
      />
      <div className="slider-ticks">
        <span>0h</span>
        <span>12h</span>
        <span>24h</span>
        <span>36h</span>
        <span>48h</span>
      </div>
    </div>
  );
}
