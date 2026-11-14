// Keep offline support without offering an in-page installation flow.
(() => {
  window.addEventListener('beforeinstallprompt', (event) => event.preventDefault());
  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).catch((error) => {
        console.warn('Fleng service worker unavailable', error);
      });
    });
  }
})();
