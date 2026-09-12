import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        // Use 127.0.0.1 (not "localhost"): on macOS "localhost" resolves to
        // IPv6 ::1 first, where Docker Desktop's gvproxy may be listening on
        // :8000 and intercept the request before it reaches the IPv4 backend.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
