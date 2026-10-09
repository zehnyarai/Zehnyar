/* رشته‌یار — service worker
 * فقط فایل‌های ایستای خودِ سایت (CSS، فونت، آیکون، اسکریپت) را کش می‌کند.
 * صفحات HTML، API، پرداخت، پنل مدیریت و حساب کاربری هرگز کش نمی‌شوند
 * تا اطلاعات لایسنس یا پرداخت کاربر بین حساب‌ها یا نسخه‌های قدیمی جابه‌جا نشود.
 */
const VERSION = 'rz-v1';
const STATIC_CACHE = 'rz-static-' + VERSION;
const SHELL = [
  '/static/css/style.css',
  '/static/fonts/Vazirmatn-Variable.woff2',
  '/static/favicon.svg',
  '/static/js/pwa.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

const OFFLINE_HTML = '<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width,initial-scale=1"><title>آفلاین · رشته‌یار</title>' +
  '<body style="font-family:Vazirmatn,Tahoma,sans-serif;background:#f0f9ff;color:#0c4a6e;' +
  'display:grid;place-items:center;min-height:100vh;margin:0;text-align:center;padding:24px">' +
  '<div><h1>اتصال اینترنت برقرار نیست</h1><p>پس از برقراری اتصال، صفحه را دوباره باز کنید.</p></div></body></html>';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== STATIC_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // درخواست‌های تغییردهنده هرگز دخالت نمی‌کنند
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(STATIC_CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }))
    );
    return;
  }

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req, { cache: 'no-store' }).catch(() =>
        new Response(OFFLINE_HTML, { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } })
      )
    );
  }
});
