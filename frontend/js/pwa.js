// Compatibility cleanup for visits to an older Fleng installation.
// This script never registers a worker or requests installation.
(() => {
  window.addEventListener('beforeinstallprompt', (event) => event.preventDefault());
  async function retireLegacyWorker() {
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      const origin = window.location.origin;
      for (const registration of registrations) {
        const workers = [registration.active, registration.waiting, registration.installing];
        const ownsWorker = workers.some((worker) => worker?.scriptURL === `${origin}/sw.js`);
        if (registration.scope === `${origin}/` && ownsWorker) await registration.unregister();
      }
    }
  }
  async function clearLegacyCache() {
    if (!('caches' in window)) return;
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith('fleng-offline-v'))
      .map((key) => caches.delete(key)));
  }
  // Cleanup failures must never block lessons, sign-in or saved progress.
  retireLegacyWorker().catch(() => {});
  clearLegacyCache().catch(() => {});
})();
