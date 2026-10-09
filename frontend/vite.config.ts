import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// In development the API runs separately (uvicorn on :8000); in production
// FastAPI serves this build from frontend/dist on the same origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});
