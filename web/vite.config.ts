import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// base "./" keeps every asset path relative, so the site works from any GitHub Pages sub-path.
export default defineConfig({
  base: "./",
  plugins: [svelte()],
  server: { fs: { allow: [".."] } },
  build: { outDir: "dist", target: "es2022" },
});
