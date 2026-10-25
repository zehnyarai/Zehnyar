/* مهاجریار — سرویس‌ورکر PWA
   صفحه‌ها: شبکه‌محور با بازگشت به کش
   دارایی‌های ثابت: کش‌محور با تازه‌سازی پس‌زمینه
   API: شبکه‌محور (بدون کش برای درخواست‌های تغییردهنده)
*/
const VERSION = "mohajeryar-v1.0.0";
const SHELL = VERSION + "-shell";
const PAGES = VERSION + "-pages";

const PRECACHE = [
  "/",
  "/wizard",
  "/methodology",
  "/offline",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/fonts/Vazirmatn-Variable.woff2",
  "/static/icons/favicon.svg",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) =>
      Promise.all(
        PRECACHE.map((url) =>
          cache.add(new Request(url, { cache: "reload" })).catch(() => null)
        )
      )
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== SHELL && key !== PAGES)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

function isStatic(url) {
  return (
    url.pathname.startsWith("/static/") ||
    url.pathname === "/manifest.webmanifest" ||
    url.pathname === "/favicon.ico"
  );
}

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    if (request.mode === "navigate") {
      const offline = await caches.match("/offline");
      if (offline) return offline;
    }
    throw error;
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    fetch(request)
      .then((response) => {
        if (response && response.ok) {
          caches.open(SHELL).then((cache) => cache.put(request, response.clone()));
        }
      })
      .catch(() => null);
    return cached;
  }
  const response = await fetch(request);
  if (response && response.ok) {
    const cache = await caches.open(SHELL);
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    // پاسخ‌های خواندنی برای مشاهده‌ی آفلاین نتیجه کش می‌شوند
    if (request.mode === "navigate" || request.headers.get("accept")?.includes("text/html")) return;
    event.respondWith(networkFirst(request, PAGES));
    return;
  }

  if (isStatic(url)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, PAGES));
    return;
  }

  event.respondWith(networkFirst(request, PAGES));
});
