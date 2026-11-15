// Load early on every page to retain the browser's one-use install event.
(() => {
  let installPrompt = null;
  let installed = window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;
  let registrationFailed = false;
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
    render();
  });
  window.addEventListener('appinstalled', () => {
    installed = true;
    installPrompt = null;
    render();
  });
  function render() {
    const button = document.getElementById('install-app');
    const status = document.getElementById('install-status');
    if (!button || !status) return;
    button.hidden = !installPrompt || installed;
    if (installed) {
      status.textContent = 'Fleng уже відкрито як додаток або щойно встановлено. Можна переходити до навчання.';
    } else if (!window.isSecureContext) {
      status.textContent = 'Для встановлення відкрий сайт через HTTPS. На цьому комп’ютері також можна використовувати localhost.';
    } else if (installPrompt) {
      status.textContent = 'Браузер готовий встановити Fleng. Натисни кнопку й підтвердь встановлення.';
    } else if (registrationFailed) {
      status.textContent = 'Не вдалося підготувати встановлення. Перезавантаж сторінку й перевір доступність сервера. Інструкції для браузера — нижче.';
    } else {
      status.textContent = 'Якщо кнопка встановлення не з’явилася, скористайся меню браузера за інструкцією нижче. На iPhone додавання виконується через Safari.';
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('install-app');
    button?.addEventListener('click', async () => {
      const prompt = installPrompt;
      if (!prompt) return;
      installPrompt = null;
      button.hidden = true;
      try {
        await prompt.prompt();
        await prompt.userChoice;
      } catch (error) {
        console.warn('Fleng install prompt unavailable', error);
      }
      render();
    });
    render();
  });
  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).catch((error) => {
        registrationFailed = true;
        console.warn('Fleng service worker unavailable', error);
        render();
      });
    });
  }
})();
