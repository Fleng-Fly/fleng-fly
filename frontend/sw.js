// Retire older root-scope Fleng workers. No fetch handler or offline cache.
self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith('fleng-offline-v'))
      .map((key) => caches.delete(key)));
    await self.clients.claim();
    await self.registration.unregister();
  })());
});
