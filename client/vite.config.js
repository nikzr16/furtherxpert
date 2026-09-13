import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Docker on Windows doesn't pass file-change events into the container,
    // so poll for changes; otherwise edits never hot-reload in the browser.
    watch: { usePolling: true, interval: 1000 },
  },
})
