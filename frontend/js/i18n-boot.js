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
