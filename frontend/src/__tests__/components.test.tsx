import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SummaryBody } from "../components/SummaryPanel";
import { CompareSelectionProvider } from "../lib/compareSelection";
import { CompareTables } from "../pages/ComparePage";
import { ExplorePage } from "../pages/ExplorePage";
import { availableSummary, comparison, region, unavailableSummary } from "./fixtures";

const wrap = (ui: React.ReactNode, path = "/") => (
  <MemoryRouter initialEntries={[path]}>
    <CompareSelectionProvider>{ui}</CompareSelectionProvider>
  </MemoryRouter>
);

describe("SummaryBody (grounding)", () => {
  it("shows the text with every cited evidence record", () => {
    render(<SummaryBody summary={availableSummary} />);
    expect(screen.getByText("Grounded overview text.")).toBeInTheDocument();
    expect(screen.getByText("Cited evidence")).toBeInTheDocument();
    expect(screen.getByText("E11")).toBeInTheDocument();
    expect(screen.getByText("E12")).toBeInTheDocument();
    expect(screen.getByText(/cites 2 evidence records/)).toBeInTheDocument();
  });

  it("never renders text for an unavailable summary, and shows why", () => {
    render(<SummaryBody summary={{ ...unavailableSummary, summary_text: "should not appear" }} />);
    expect(screen.queryByText("should not appear")).not.toBeInTheDocument();
    expect(screen.getByText(/No grounded summary is shown/)).toBeInTheDocument();
    expect(screen.getByText(/No stored summary exists/)).toBeInTheDocument();
    expect(screen.getByText("Retrieved evidence")).toBeInTheDocument();
  });
});

describe("CompareTables", () => {
  it("marks extremes and shows missing values as blanks", () => {
    render(wrap(<CompareTables data={comparison} />));
    const income = screen.getByText("Median household income").closest("tr")!;
    expect(within(income).getByText("$180,000").closest("td")).toHaveClass("cell-hi");
    expect(within(income).getByText("$50,000").closest("td")).toHaveClass("cell-lo");
    const pv = screen.getByText("Rooftop PV capacity (DC)").closest("tr")!;
    expect(within(pv).getByText("—")).toBeInTheDocument();
    expect(screen.getAllByText("Priority")).toHaveLength(1);
  });

  it("renders an overview card per region including the fallback", () => {
    render(wrap(<CompareTables data={comparison} />));
    expect(screen.getByText("Grounded overview text.")).toBeInTheDocument();
    expect(screen.getByText(/No grounded summary is shown/)).toBeInTheDocument();
  });
});

describe("ExplorePage (integration with mocked API)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("lists regions from /api/regions and links to their pages", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const body = url.startsWith("/api/regions")
        ? { total: 2, limit: 25, offset: 0, items: [region("94601"), region("93701", "Fresno")] }
        : url.startsWith("/api/facets")
          ? { counties: [{ value: "Alameda", label: "Alameda", count: 1 }], utilities: [], outcomes: [{ value: "y_pv", label: "y_pv", count: 2 }] }
          : { outcome_name: "y_pv", direction: "low", total: 0, items: [] };
      return new Response(JSON.stringify(body), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(wrap(<Routes><Route path="/" element={<ExplorePage />} /></Routes>));

    const link = await screen.findByRole("link", { name: "94601" });
    expect(link).toHaveAttribute("href", "/regions/94601");
    expect(screen.getByText("2 regions")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/No region is flagged/)).toBeInTheDocument());
    expect(fetchMock.mock.calls.some(([url]) => String(url).startsWith("/api/screening?outcome_name=y_pv"))).toBe(true);
  });

  it("surfaces API errors instead of an empty table", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: "Database is not ready." }), { status: 503 })));
    render(wrap(<Routes><Route path="/" element={<ExplorePage />} /></Routes>));
    expect((await screen.findAllByRole("alert"))[0]).toHaveTextContent("Database is not ready.");
  });
});
