import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react(), legacy({ targets: ['Chrome >= 53', 'Safari >= 12'], modernPolyfills: true })],
  server: {
    fs: { deny: ['.env', '.env.*', '*.{crt,pem}', '**/.git/**', '**/.private/**'] },
    host: '0.0.0.0',
    allowedHosts: ['.e2b.app', 'localhost'],
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  preview: { host: '0.0.0.0', allowedHosts: ['.e2b.app', 'localhost'] },
})
