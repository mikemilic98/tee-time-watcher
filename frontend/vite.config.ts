import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/courses": "http://localhost:8000",
      "/watch-rules": "http://localhost:8000",
      "/bookings": "http://localhost:8000",
      "/notifications": "http://localhost:8000"
    }
  }
});

