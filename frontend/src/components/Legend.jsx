import { LEVEL_COLORS, LEVEL_LABELS } from "../risk";

export default function Legend() {
  return (
    <div className="legend">
      <strong>Risk</strong>
      {LEVEL_LABELS.map((label, i) => (
        <div key={label}>
          <span className="dot" style={{ background: LEVEL_COLORS[i] }} />
          {label}
        </div>
      ))}
      <p>Dots: risk at the truck's ETA. Shading: risk at the slider's hour.</p>
    </div>
  );
}
