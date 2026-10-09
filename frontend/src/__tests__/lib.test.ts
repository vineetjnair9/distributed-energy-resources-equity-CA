import { flagDirection, modelName, percentile } from "../lib/labels";
import { parseWkt } from "../lib/wkt";
import { safeHref } from "../lib/safeHref";
import { extremes } from "../pages/ComparePage";

describe("parseWkt", () => {
  it("swaps WKT x/y into Leaflet lat/lng", () => {
    const [polygon] = parseWkt("POLYGON ((-118.2 33.9, -118.1 33.9, -118.1 34.0, -118.2 33.9))");
    expect(polygon[0][0]).toEqual([33.9, -118.2]);
    expect(polygon[0]).toHaveLength(4);
  });

  it("keeps holes and multiple parts", () => {
    const parts = parseWkt(
      "MULTIPOLYGON (((0 0, 4 0, 4 4, 0 0), (1 1, 2 1, 2 2, 1 1)), ((10 10, 11 10, 11 11, 10 10)))",
    );
    expect(parts).toHaveLength(2);
    expect(parts[0]).toHaveLength(2);
    expect(parts[1][0][0]).toEqual([10, 10]);
  });

  it("returns nothing for unsupported geometry", () => {
    expect(parseWkt("POINT (1 2)")).toEqual([]);
  });
});

describe("labels", () => {
  it.each([
    [0.01, "1st"], [0.02, "2nd"], [0.03, "3rd"], [0.11, "11th"], [0.12, "12th"],
    [0.13, "13th"], [0.21, "21st"], [0.25, "25th"], [1, "100th"], [null, "—"],
  ])("percentile(%s) = %s", (value, expected) => {
    expect(percentile(value)).toBe(expected);
  });

  it("matches the backend flag directions", () => {
    expect(flagDirection("y_pv")).toBe("low");
    expect(flagDirection("energy_burden_pct")).toBe("high");
    expect(flagDirection("any_turbines")).toBe("absolute");
  });

  it("unwraps exported model names", () => {
    expect(modelName("y_pv | Model 7 (infrastructure controls) | levels")).toBe("Model 7 (infrastructure controls)");
    expect(modelName("Model 1 baseline")).toBe("Model 1 baseline");
  });
});

describe("extremes", () => {
  it("ignores missing values and ties", () => {
    expect(extremes([3, null, 1, undefined])).toEqual({ max: 3, min: 1 });
    expect(extremes([2, 2])).toEqual({ max: null, min: null });
    expect(extremes([5, null])).toEqual({ max: null, min: null });
  });
});

describe("safeHref", () => {
  it("allows http(s) and takes the first of several sources", () => {
    expect(safeHref("https://a.example/x; https://b.example")).toBe("https://a.example/x");
  });
  it.each(["javascript:alert(1)", " JaVaScRiPt:alert(1)", "data:text/html,<script>", "/relative", "", null])(
    "rejects %s",
    (url) => expect(safeHref(url)).toBeNull(),
  );
});
