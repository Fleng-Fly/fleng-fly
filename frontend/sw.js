// Only the public, self-contained offline screen is cached. Never cache API,
// credentials, user HTML, answers, chat, or progress.
const CACHE = 'fleng-offline-v1';
const OFFLINE = '/offline.html';
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.add(OFFLINE)));
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith('fleng-offline-') && key !== CACHE)
      .map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || event.request.mode !== 'navigate' ||
      url.origin !== self.location.origin || url.pathname === '/api' ||
      url.pathname.startsWith('/api/') || url.pathname === '/docs' ||
      url.pathname === '/redoc' || url.pathname === '/openapi.json') return;
  event.respondWith((async () => {
    try {
      return await fetch(event.request);
    } catch {
      return (await caches.match(OFFLINE)) || new Response('Fleng: no connection.', {
        status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }
  })());
});
