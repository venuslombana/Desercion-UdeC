/* Service worker de Permanencia UdeC (aplicación instalable).
 * Reglas, pensadas para que nunca se muestre una versión vieja ni se guarden datos personales:
 *  - /api/*: siempre a la red; nunca se guarda (datos de estudiantes y token).
 *  - Páginas, JavaScript y CSS: primero la red; lo guardado solo se usa si no hay conexión.
 *  - Fuentes e imágenes: primero lo guardado (no cambian entre versiones).
 * Al publicar una versión nueva basta con cambiar VERSION: la caché anterior se borra sola. */
const VERSION = "permanencia-v5";
const BASICOS = ["/", "/static/offline.html", "/static/styles.css?v=5", "/static/app.js?v=5", "/static/tema.js?v=5", "/static/chart.umd.min.js?v=5",
  "/static/img/logo-udec.png", "/static/img/icono-192.png", "/static/fonts/montserrat-latin-400-normal.woff2", "/static/fonts/montserrat-latin-700-normal.woff2"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(BASICOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

async function redPrimero(req) {
  try {
    const r = await fetch(req);
    if (r.ok) { const c = await caches.open(VERSION); c.put(req, r.clone()); }
    return r;
  } catch (err) {
    const guardada = await caches.match(req, { ignoreSearch: req.mode === "navigate" });
    if (guardada) return guardada;
    if (req.mode === "navigate") return caches.match("/static/offline.html");
    throw err;
  }
}

async function cachePrimero(req) {
  const guardada = await caches.match(req);
  if (guardada) return guardada;
  const r = await fetch(req);
  if (r.ok) { const c = await caches.open(VERSION); c.put(req, r.clone()); }
  return r;
}

self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/docs") || url.pathname === "/openapi.json") return; // siempre red, nunca caché
  if (/\.(woff2|png|svg|ico)$/.test(url.pathname)) { e.respondWith(cachePrimero(req)); return; }
  e.respondWith(redPrimero(req));
});
