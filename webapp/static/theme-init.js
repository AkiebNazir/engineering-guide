/* Paint the right theme BEFORE first paint. The server round-trip that loads
   settings.theme finishes long after this, so without it every reload flashes
   the wrong ground. localStorage mirrors the server copy; "system" follows
   prefers-color-scheme. Loaded as a file, not inline, so the hosted app's
   Content-Security-Policy can refuse every inline script. */
(function () {
  var pref = 'system';
  try { pref = localStorage.getItem('dsa-theme') || 'system'; } catch (e) {}
  var dark = pref === 'dark' ||
    (pref === 'system' && !matchMedia('(prefers-color-scheme: light)').matches);
  var r = document.documentElement;
  r.dataset.theme = dark ? 'dark' : 'light';
  r.dataset.themePref = pref;
})();
