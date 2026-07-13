import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  // Domestic static hosts serve this application below their own project path.
  // A relative asset base makes the same build work on EdgeOne Pages, OSS and
  // CDN-backed custom domains without hard-coding a foreign hosting domain.
  base: mode === "public-cn" ? "./" : "/",
  plugins: [react()],
  server: { port: 5173 },
  build: mode === "public-cn" ? { outDir: "dist-cn", emptyOutDir: true } : undefined,
}));
