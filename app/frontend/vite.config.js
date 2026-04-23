import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      // Proxy /api and /stream requests to Flask backend during dev
      '/api': {
        target: 'http://localhost:5050',
        changeOrigin: true,
      },
      '/stream': {
        target: 'http://localhost:5050',
        changeOrigin: true,
      },
      // Proxy Socket.IO
      '/socket.io': {
        target: 'http://localhost:5050',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
