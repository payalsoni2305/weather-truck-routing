import { formatDuration, formatMiles, formatTime } from "../format";
import { LEVEL_COLORS, LEVEL_LABELS, ROUTE_COLORS } from "../risk";
import RiskBar from "./RiskBar";

export default function RouteList({ plan, selectedId, onSelect }) {
  const { recommendation } = plan;
  return (
    <section className="routes">
      <div className="recommendation">
        <strong>Recommended: Route {recommendation.route_id}</strong>
        <p>{recommendation.reason}</p>
        {recommendation.warning && <p className="warning">⚠ {recommendation.warning}</p>}
      </div>

      {plan.routes.map((route) => {
        const s = route.summary;
        return (
          <button
            key={route.id}
            type="button"
            className={`route-card${route.id === selectedId ? " selected" : ""}`}
            onClick={() => onSelect(route.id)}
          >
            <div className="route-head">
              <span className="swatch" style={{ background: ROUTE_COLORS[route.id] }} />
              <strong>Route {route.id}</strong>
              {route.recommended && <span className="badge">Best</span>}
              <span className="rank">#{route.rank}</span>
            </div>
            <div className="route-stats">
              <span>{formatMiles(route.distance_mi)}</span>
              <span>{formatDuration(route.duration_s)}</span>
              <span>Arrive {formatTime(route.arrival)}</span>
            </div>
            <RiskBar summary={s} total={route.distance_mi} />
            <div className="route-risk">
              <span>
                Severe <b>{formatMiles(s.miles_by_level.Severe + s.miles_by_level["No Travel"])}</b>
              </span>
              <span>
                High <b>{formatMiles(s.miles_by_level.High)}</b>
              </span>
              <span>
                Avg risk <b>{s.avg_risk.toFixed(2)}</b>
              </span>
              <span>
                Worst <b style={{ color: LEVEL_COLORS[s.max_level] }}>{LEVEL_LABELS[s.max_level]}</b>
              </span>
            </div>
            {route.comparison && <p className="comparison">Route {recommendation.route_id} has {route.comparison}</p>}
          </button>
        );
      })}
    </section>
  );
}
