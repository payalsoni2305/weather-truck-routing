import { LEVEL_COLORS, LEVEL_LABELS } from "../risk";

/** Stacked bar of miles at each risk level. */
export default function RiskBar({ summary, total }) {
  return (
    <div className="risk-bar" role="img" aria-label="Miles by risk level">
      {LEVEL_LABELS.map((label, i) => {
        const miles = summary.miles_by_level[label] ?? 0;
        if (miles <= 0) return null;
        return (
          <span
            key={label}
            style={{ width: `${(miles / total) * 100}%`, background: LEVEL_COLORS[i] }}
            title={`${label}: ${Math.round(miles)} mi`}
          />
        );
      })}
    </div>
  );
}
