const CACHE_NAME = "mi-tramite-justo-v1";
const PRECACHE_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./assets/branding/logo.png",
  "./assets/languages/nah_puebla.json",
  "./assets/languages/tot_sierra.json",
  "./assets/packs/acta_nacimiento/workflow.json",
  "./assets/packs/curp_tramite/workflow.json",
  "./assets/packs/imss_afiliacion/workflow.json",
  "./assets/packs/pension_adulto_mayor/workflow.json",
  "./assets/svg/documents.svg",
  "./assets/svg/office_map.svg",
  "./assets/svg/window_officer.svg",
  "./assets/svg/payment.svg",
  "./assets/svg/check_done.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((oldKey) => caches.delete(oldKey))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match("./index.html"));
    })
  );
});
