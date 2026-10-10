import { Link, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AboutPage } from "./pages/AboutPage";
import { ComparePage } from "./pages/ComparePage";
import { DefinitionsPage } from "./pages/DefinitionsPage";
import { ExplorePage } from "./pages/ExplorePage";
import { RegionPage } from "./pages/RegionPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ExplorePage />} />
        <Route path="regions/:regionId" element={<RegionPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="definitions" element={<DefinitionsPage />} />
        <Route path="*" element={<div className="prose"><h1>Page not found</h1><p><Link to="/">Back to regions</Link></p></div>} />
      </Route>
    </Routes>
  );
}
