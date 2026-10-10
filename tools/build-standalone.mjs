import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const base = process.env.VITE_BASE_PATH || '/'
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('VITE_BASE_PATH must be a root or simple site directory')
const env = { ...process.env, VITE_APP_MODE: 'standalone', CAPACITOR_SERVER_URL: '' }
const build = spawnSync('npm', ['run', 'build'], { env, stdio: 'inherit', shell: process.platform === 'win32' })
if (build.status !== 0) process.exit(build.status ?? 1)
writeFileSync('dist/manifest.webmanifest', JSON.stringify({
  id: base, name: 'پستینو | Pestino', short_name: 'پستینو', lang: 'fa', dir: 'rtl',
  description: 'دفتر باغ، دانشنامه و عکس‌های پسته؛ مستقل و رایگان. بدون تحلیل خودکار یا پرداخت.',
  start_url: base, scope: base, display: 'standalone',
  theme_color: '#245b45', background_color: '#f6f8f5',
  icons: [192, 512].map(size => ({ src: `icon-${size}.png`, sizes: `${size}x${size}`, type: 'image/png', purpose: 'any' })),
}, null, 2))
function files(folder, prefix = '') {
  return readdirSync(folder, { withFileTypes: true }).flatMap(entry => {
    const path = prefix + entry.name
    return entry.isDirectory() ? files(join(folder, entry.name), path + '/') : [path]
  })
}
const paths = files('dist').filter(p => p !== 'sw.js' && !p.endsWith('.map'))
const digest = createHash('sha256')
for (const p of paths.sort()) digest.update(readFileSync(join('dist', p)))
const version = digest.digest('hex').slice(0, 16)
writeFileSync('dist/sw.js', `/* Generated for the local-only Pestino web edition. */
const CACHE = 'pestino-local-${version}';
const BASE = ${JSON.stringify(base)};
const ASSETS = ${JSON.stringify([base, ...paths.map(p => base + p)])};
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('pestino-local-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(BASE)) return;
  if (event.request.mode === 'navigate') {
    event.respondWith(caches.open(CACHE).then(cache => cache.match(BASE)).then(cached => cached || fetch(event.request)));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
`)
writeFileSync('dist/.nojekyll', '')
if (process.argv.includes('--android')) {
  if (base !== '/') throw new Error('Native APK needs the root base path, not the GitHub Pages path')
  const sync = spawnSync('npx', ['cap', 'sync', 'android'], { env, stdio: 'inherit', shell: process.platform === 'win32' })
  if (sync.status !== 0) process.exit(sync.status ?? 1)
  const config = JSON.parse(readFileSync('android/app/src/main/assets/capacitor.config.json', 'utf8'))
  if (config.server?.url) throw new Error('Standalone APK must have no remote URL')
}
console.log(`Pestino standalone assets ready (base ${base}); no API server or account needed.`)
