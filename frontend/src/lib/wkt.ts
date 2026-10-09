export type Ring = [number, number][]; // [lat, lng] for Leaflet
export type PolygonRings = Ring[];

/** Parse POLYGON / MULTIPOLYGON WKT into Leaflet [lat, lng] rings. */
export function parseWkt(wkt: string): PolygonRings[] {
  const text = wkt.trim();
  const type = text.slice(0, text.indexOf("(")).trim().toUpperCase();
  const body = text.slice(text.indexOf("("));
  const ring = (chunk: string): Ring =>
    chunk
      .replace(/[()]/g, "")
      .split(",")
      .map((pair) => pair.trim().split(/\s+/).map(Number))
      .filter((xy) => xy.length >= 2 && xy.every(Number.isFinite))
      .map(([x, y]) => [y, x]);
  const polygon = (chunk: string): PolygonRings => chunk.split(/\)\s*,\s*\(/).map(ring);
  if (type === "POLYGON") return [polygon(body.slice(1, -1))];
  if (type === "MULTIPOLYGON") return body.slice(2, -2).split(/\)\)\s*,\s*\(\(/).map(polygon);
  return [];
}
