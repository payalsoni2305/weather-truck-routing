import { useState } from "react";
import { formatTime } from "../format";
import { LEVEL_COLORS } from "../risk";

export default function CheckpointTable({ route, onFocus }) {
  const [riskyOnly, setRiskyOnly] = useState(false);
  const rows = riskyOnly ? route.checkpoints.filter((cp) => cp.level > 0) : route.checkpoints;

  return (
    <section className="checkpoints">
      <div className="checkpoints-head">
        <h2>Route {route.id} checkpoints</h2>
        <label>
          <input type="checkbox" checked={riskyOnly} onChange={(e) => setRiskyOnly(e.target.checked)} />
          Risky only
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Mile</th>
              <th>ETA</th>
              <th>Wind</th>
              <th>Rain</th>
              <th>Snow</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((cp) => (
              <tr key={cp.mile} onClick={() => onFocus(cp)} title={cp.reasons.join("; ") || "No hazards"}>
                <td>{Math.round(cp.mile)}</td>
                <td>{formatTime(cp.eta)}</td>
                <td>{Math.round(cp.weather.wind_mph)}</td>
                <td>{cp.weather.rain_in_hr.toFixed(2)}</td>
                <td>{cp.weather.snow_in_hr.toFixed(2)}</td>
                <td>
                  <span className="pill" style={{ background: LEVEL_COLORS[cp.level] }}>
                    {cp.level_label}
                  </span>
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={6} className="empty">
                  No risky checkpoints on this route.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="hint">Wind mph · rain &amp; snow in/hr · click a row to zoom the map.</p>
    </section>
  );
}
