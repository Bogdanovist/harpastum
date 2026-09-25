import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  server: {
    // Listen on all interfaces so a phone on the tailnet can reach the dev server.
    host: true,
    port: 5174,
    // Fail instead of drifting to another port: the phone's bookmarked URL uses 5174.
    strictPort: true,
    // Vite answers requests by hostname only for hosts listed here. matt-human
    // is the laptop's Tailscale name, which the phone uses.
    allowedHosts: ['matt-human'],
    // The Claude Code sandbox blocks macOS file-system events, so the watcher
    // polls. Without it, edits made by an agent never reach the phone.
    watch: { usePolling: true, interval: 200 },
  },
  test: {
    environment: 'jsdom',
  },
})
