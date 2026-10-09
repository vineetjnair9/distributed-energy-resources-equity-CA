import { useMemo } from "react";
import { MapContainer, Polygon, TileLayer } from "react-leaflet";
import { latLngBounds } from "leaflet";
import "leaflet/dist/leaflet.css";
import { parseWkt } from "../lib/wkt";

export function RegionMap({ wkt, label }: { wkt: string; label: string }) {
  const polygons = useMemo(() => parseWkt(wkt), [wkt]);
  const points = polygons.flat(2);
  if (!points.length) return <div className="map map-empty">No boundary available</div>;
  const bounds = latLngBounds(points).pad(0.6);
  return (
    <div className="map" role="img" aria-label={`Map of ${label}`}>
      <MapContainer bounds={bounds} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {polygons.map((rings, index) => (
          <Polygon key={index} positions={rings} pathOptions={{ color: "#b45309", weight: 2, fillOpacity: 0.18 }} />
        ))}
      </MapContainer>
    </div>
  );
}
