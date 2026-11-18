// Classic (blocking) script: set <html lang> and hide the page for an instant
// while the Ukrainian dictionary is applied, so English never flashes.
(function () {
  try {
    var stored = window.localStorage.getItem('fleng.lang');
    var browser = ((navigator.languages && navigator.languages[0]) || navigator.language || 'en').toLowerCase();
    var lang = stored === 'uk' || stored === 'en' ? stored : browser.indexOf('uk') === 0 ? 'uk' : 'en';
    document.documentElement.lang = lang;
    if (lang === 'uk') {
      document.documentElement.classList.add('i18n-pending');
      // Safety net: never leave the page hidden if the module fails to load.
      window.setTimeout(function () { document.documentElement.classList.remove('i18n-pending'); }, 1500);
    }
  } catch (error) {
    /* Storage unavailable: keep the default English page. */
  }
})();

// Landing/login/register: hold the page back while a remembered session is restored, so a
// signed-in learner is sent straight to the dashboard without seeing these pages.
(function () {
  try {
    var path = window.location.pathname;
    var entry = path === '/' || path === '/index.html' || path === '/login.html' || path === '/register.html';
    if (entry && window.localStorage.getItem('fleng.session.hint')) {
      document.documentElement.classList.add('session-pending');
      window.setTimeout(function () { document.documentElement.classList.remove('session-pending'); }, 3000);
    }
  } catch (error) {
    /* Storage unavailable: pages render normally. */
  }
})();
