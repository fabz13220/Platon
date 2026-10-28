// BLIZ sans internet : le téléphone garde la page, les polices et les icônes.
// Avec internet, la page vient toujours du réseau (les mises à jour arrivent comme avant) ;
// sans internet, ou si le réseau traîne plus de 4 s, on ouvre la dernière copie gardée.
const CACHE = "bliz-1";
const PAGE = new URL("./", self.registration.scope).href;
self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll([PAGE, "manifest.webmanifest", "icon-180.png?v=6", "icon-192.png?v=6"])).catch(() => {}));
});
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));
// les polices déjà chargées par la page avant que ce fichier prenne la main (première ouverture)
self.addEventListener("message", e => {
  const k = e.data && e.data.keep; if (!Array.isArray(k)) return;
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(k.filter(u => /^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(u))
    .map(u => c.match(u).then(h => h || fetch(u).then(res => res.ok && c.put(u, res))).catch(() => {})))));
});
self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET") return;
  // la page de l'appli (avec ou sans ?salle=…) ; admin.html n'est jamais gardée
  if (r.mode === "navigate" && u.origin === location.origin && /\/(index\.html)?$/.test(u.pathname)) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE);
      const net = fetch(PAGE, { cache: "no-cache" }).then(res => { if (res.ok) c.put(PAGE, res.clone()); return res; });
      const slow = new Promise(ok => setTimeout(ok, 4000));
      try {
        const res = await Promise.race([net, slow.then(() => null)]);
        if (res) return res;
      } catch (err) {}
      e.waitUntil(net.catch(() => {}));
      return (await c.match(PAGE)) || net;
    })());
    return;
  }
  // polices, Firebase et icônes : la copie gardée tout de suite, rafraîchie en arrière-plan
  const keep = /^(fonts\.googleapis\.com|fonts\.gstatic\.com)$/.test(u.hostname) || (u.hostname === "www.gstatic.com" && u.pathname.startsWith("/firebasejs/"))
    || (u.origin === location.origin && /\.(png|webmanifest)$/.test(u.pathname));
  if (!keep) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(r);
    const net = fetch(r).then(res => { if (res.ok || res.type === "opaque") c.put(r, res.clone()); return res; });
    if (hit) { e.waitUntil(net.catch(() => {})); return hit; }
    return net;
  }));
});
