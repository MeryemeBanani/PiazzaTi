import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default ({ mode }: { mode: string }) => {
  // load .env files based on the `mode` (dev/production)
  const env = loadEnv(mode, process.cwd())
  const base = env.VITE_BASE || '/'

  return defineConfig({
    plugins: [react()],
    base,
    server: {
      proxy: {
        // Proxy /api requests to backend running on localhost:8000
        '/api': 'http://localhost:8000'
      }
    }
  })
}
