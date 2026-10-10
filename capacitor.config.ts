import type { CapacitorConfig } from '@capacitor/cli'

// Native production builds use the same HTTPS site as the API, keeping cookies
// and requests first-party. Do not ship a localhost or a development URL.
const publicUrl = process.env.CAPACITOR_SERVER_URL
if (publicUrl) {
  const url = new URL(publicUrl)
  if (
    url.protocol !== 'https:' ||
    url.username ||
    url.password ||
    url.pathname !== '/' ||
    url.search ||
    url.hash ||
    ['localhost', '127.0.0.1', '::1', '[::1]'].includes(url.hostname) ||
    url.hostname.endsWith('.e2b.app')
  ) {
    throw new Error('CAPACITOR_SERVER_URL must be a public HTTPS site root, without credentials')
  }
}
const config: CapacitorConfig = {
  appId: 'ir.pestino.app',
  appName: 'پستینو',
  webDir: 'dist',
  ...(publicUrl ? { server: { url: publicUrl, cleartext: false } } : {}),
  android: { backgroundColor: '#f6f8f5' },
  plugins: { Camera: { presentationStyle: 'fullscreen' } },
}
export default config
