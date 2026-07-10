import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  base: "/admin/",
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    css: true,
    globalSetup: "./tests/globalSetup.js",
    setupFiles: "./tests/setup.js",
    include: ["tests/**/*.spec.{js,jsx}"],
    fileParallelism: false,
    maxWorkers: 1,
    clearMocks: true,
    restoreMocks: true,
  },
});
