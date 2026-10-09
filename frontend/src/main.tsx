import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { CompareSelectionProvider } from "./lib/compareSelection";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <CompareSelectionProvider>
        <App />
      </CompareSelectionProvider>
    </BrowserRouter>
  </StrictMode>,
);
