import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { useMap } from "react-leaflet";
import { scoreToRgba } from "../risk";

const PANE = "heatmap";


function renderFrames(data) {
  const canvas = document.createElement("canvas");
  canvas.width = data.cols;
  canvas.height = data.rows;
  const ctx = canvas.getContext("2d");
  return data.scores.map((frame) => {
    const image = ctx.createImageData(data.cols, data.rows);
    data.cells.forEach((cell, i) => {
      const [r, g, b, a] = scoreToRgba(frame[i]);
      const o = cell * 4;
      image.data[o] = r;
      image.data[o + 1] = g;
      image.data[o + 2] = b;
      image.data[o + 3] = a;
    });
    ctx.putImageData(image, 0, 0);
    return canvas.toDataURL();
  });
}

export default function HeatmapLayer({ data, hour }) {
  const map = useMap();
  const frames = useMemo(() => renderFrames(data), [data]);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!map.getPane(PANE)) {
      const pane = map.createPane(PANE);
      pane.style.zIndex = "350"; 
      pane.style.pointerEvents = "none";
    }
    const layer = L.imageOverlay(frames[0], data.bounds, {
      pane: PANE,
      opacity: 0.75,
      className: "heatmap-image",
    }).addTo(map);
    layerRef.current = layer;
    return () => {
      layer.remove();
      layerRef.current = null;
    };
  }, [map, frames, data.bounds]);

  useEffect(() => {
    layerRef.current?.setUrl(frames[Math.min(hour, frames.length - 1)]);
  }, [frames, hour]);

  return null;
}
