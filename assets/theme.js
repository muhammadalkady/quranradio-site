/* Theme toggle: cycles System -> Light -> Dark, persisted in localStorage.
   The no-flash applier runs inline in <head>; this only wires the button. */
(function () {
  var doc = document.documentElement;
  var btn = document.getElementById('themeToggle');
  if (!btn) return;
  var order = ['system', 'light', 'dark'];

  function get() {
    try { return localStorage.getItem('qr-theme') || 'system'; } catch (e) { return 'system'; }
  }
  function isDark(pref) {
    return pref === 'dark' ||
      (pref === 'system' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function apply(pref) {
    if (pref === 'light' || pref === 'dark') doc.dataset.theme = pref;
    else delete doc.dataset.theme;
    btn.dataset.pref = pref;
    btn.setAttribute('aria-label', 'Theme: ' + pref + ' (tap to change)');
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', isDark(pref) ? '#0E1512' : '#EAF3EC');
  }

  apply(get());

  btn.addEventListener('click', function () {
    var next = order[(order.indexOf(get()) + 1) % order.length];
    try { localStorage.setItem('qr-theme', next); } catch (e) {}
    apply(next);
  });

  // Keep meta theme-color in sync with the OS while in "system" mode.
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      if (get() === 'system') apply('system');
    });
  } catch (e) {}

  // Remember the language choice when the EN<->AR pill is clicked, before navigating.
  var langLink = document.querySelector('[data-set-lang]');
  if (langLink) {
    langLink.addEventListener('click', function () {
      try { localStorage.setItem('qr-lang', langLink.getAttribute('data-set-lang')); } catch (e) {}
    });
  }
})();
