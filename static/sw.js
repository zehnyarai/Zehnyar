const CACHE_NAME = "zehnyar-shell-v5";
// The PWA is served at /, while the Android wrapper serves the same files at
// /assets/. Deriving paths from the registration scope keeps one worker valid
// in both hosts.
const APP_ROOT = new URL(self.registration.scope).pathname.replace(/\/$/, "");
const appPath = (path = "/") => `${APP_ROOT}${path}` || "/";
const CORE_ASSETS = [
  appPath("/"),
  appPath("/manifest.webmanifest"),
  appPath("/static/styles.css"),
  appPath("/static/app.js"),
  appPath("/static/offline-corpus.json"),
  appPath("/static/offline-framework.json"),
  appPath("/static/offline-topics.json"),
  appPath("/static/icons/zehnyar-192.png"),
  appPath("/static/icons/zehnyar-512.png")
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          const copy = response.clone();
          if (response.ok && (url.pathname.startsWith(`${APP_ROOT}/static/`) || request.mode === "navigate")) {
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(appPath("/")));
    })
  );
});
