import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      // Cloudflare Pages Function (votes) — run `wrangler pages dev` on :8788.
      // In production these are same-origin; this proxy is dev-only.
      "/votes": {
        target: "http://127.0.0.1:8788",
        changeOrigin: true,
      },
    },
  },
});
