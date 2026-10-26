import { useState } from "react";
import { toLocalInput } from "../format";

function defaultDeparture() {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setMinutes(0, 0, 0);
  return toLocalInput(d);
}

export default function TripForm({ onSubmit, loading }) {
  const [origin, setOrigin] = useState("Denver, CO");
  const [destination, setDestination] = useState("Chicago, IL");
  const [departure, setDeparture] = useState(defaultDeparture);
  const [weight, setWeight] = useState("35000");
  const [interval, setInterval] = useState(25);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      origin,
      destination,
      departure: new Date(departure).toISOString(),
      load_weight_lb: Number(weight),
      interval_miles: interval,
    });
  };

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <label>
        Origin
        <input value={origin} onChange={(e) => setOrigin(e.target.value)} placeholder="City, address or lat,lon" required />
      </label>
      <label>
        Destination
        <input value={destination} onChange={(e) => setDestination(e.target.value)} placeholder="City, address or lat,lon" required />
      </label>
      <div className="row">
        <label>
          Departure
          <input
            type="datetime-local"
            value={departure}
            min={toLocalInput(new Date())}
            onChange={(e) => setDeparture(e.target.value)}
            required
          />
        </label>
        <label>
          Load (lb)
          <input
            type="number"
            min={1}
            max={200000}
            step={1}
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            required
          />
        </label>
      </div>
      <fieldset className="interval">
        <legend>Sample weather every</legend>
        {[10, 25, 50].map((mi) => (
          <label key={mi} className={interval === mi ? "active" : ""}>
            <input type="radio" name="interval" checked={interval === mi} onChange={() => setInterval(mi)} />
            {mi} mi
          </label>
        ))}
      </fieldset>
      <button type="submit" disabled={loading}>
        {loading ? "Planning…" : "Find safest route"}
      </button>
    </form>
  );
}
