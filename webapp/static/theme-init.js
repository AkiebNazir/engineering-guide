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
/* iOS Safari zooms into any focused field whose text is under 16px (the code
   editor, search) and stays zoomed. maximum-scale=1 stops that, and iOS still
   allows pinch-zoom despite it. Elsewhere it would block pinch-zoom, and no
   other browser auto-zooms, so iOS only. */
(function () {
  var ios = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);   // iPadOS reports as a Mac
  var vp = document.querySelector('meta[name=viewport]');
  if (ios && vp) vp.content += ', maximum-scale=1';
})();
