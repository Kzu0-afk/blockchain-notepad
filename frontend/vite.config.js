import { defineConfig } from "vite";
import wasm from "vite-plugin-wasm";

export default defineConfig({
  plugins: [wasm()],
  define: {
    global: "globalThis",
  },
  resolve: {
    alias: {
      buffer: "buffer",
    },
  },
  optimizeDeps: {
    include: ["buffer"],
  },
  build: {
    outDir: "../notes/static/js/dist",
    emptyOutDir: false, // DO NOT DELETE existing static files
    rollupOptions: {
      input: {
        polyfills: "./src/polyfills.js",
        blaze: "./src/blaze-engine.js",
        wallet: "./src/wallet-connection.js"
      },
      output: {
        entryFileNames: "[name].js",
        format: "es"
      }
    }
  }
});

