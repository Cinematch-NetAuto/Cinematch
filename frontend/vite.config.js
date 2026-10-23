// Vite settings for the CineMatch frontend.
//
// In development the browser talks only to Vite on port 5173. Vite forwards every
// request that starts with /api to the backend on port 8000, so the browser sees
// one address and CORS never comes up. Use 127.0.0.1, not localhost: the backend
// listens on 127.0.0.1 only, and "localhost" can resolve to IPv6 first.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true, // fail loudly instead of moving to another port
    // Google's advice for testing "Sign in with Google" on http://localhost
    headers: { 'Referrer-Policy': 'no-referrer-when-downgrade' },
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
