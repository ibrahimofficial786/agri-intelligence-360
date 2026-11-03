import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The browser always calls /api on the same origin; Vite forwards it to the backend.
// This is what makes the app work identically on localhost and through an ngrok link.
const proxy = { '/api': { target: process.env.BACKEND_URL || 'http://127.0.0.1:8000', changeOrigin: true } }

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: true, allowedHosts: true, proxy },
  preview: { port: 5173, host: true, allowedHosts: true, proxy },
  test: { environment: 'node' },
})
