const CACHE_NAME = "weebarr-static-v3";
const STATIC_ASSETS = [
  "/manifest.webmanifest",
  "/static/img/back.png",
  "/static/img/hamburger.png",
  "/static/img/weebarr-mark.svg",
  "/static/img/weebarr-pwa-180.png",
  "/static/img/weebarr-pwa-192.png",
  "/static/img/weebarr-pwa-512.png",
  "/static/img/weebarr-pwa-1024.png",
  "/static/img/weebarr-wordmark.svg",
  "/static/img/weebarr-wordmark-light.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;
  if (url.pathname.startsWith("/auth/")) return;
  if (url.pathname === "/login" || url.pathname === "/logout" || url.pathname.startsWith("/setup")) return;

  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        });
      }),
    );
  }
});
