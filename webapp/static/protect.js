/* ============================================================================
   Content protection for the hosted guide and the public preview.

   Active when config.js sets EG_PROTECT (hosted mode, static build); the local
   app (`make app`) is the owner's own copy and is left alone.

   What it does:
     - copy / cut of page text is refused, except inside editors and form fields
       (your own code and notes) and through the Copy buttons on code examples,
       which write to the clipboard directly
     - the context menu, dragging text or images out, printing, "save page" and
       "view source" are refused
     - the developer-tools shortcuts are refused, and while developer tools are
       open (a paused `debugger` statement gives them away) the page is hidden
     - signed-in pages carry a faint watermark with the reader's email, so a
       screenshot or photo of a page is traceable to the account it came from

   None of this is a security boundary: anything a browser displays can be
   captured. The boundary is the server, which never sends a page above the
   reader's plan (entitlements.py). This layer makes bulk copying tedious and
   leaks attributable.
   ========================================================================= */
'use strict';

window.EGProtect = (function () {
  const on = !!(window.EG_PROTECT || window.EG_AUTH);
  const noop = { active: false, watermark() {} };
  if (!on) return noop;

  const EDITABLE = 'input, textarea, select, [contenteditable=""], [contenteditable="true"], .CodeMirror';
  const editable = t => !!(t && t.nodeType === 1 && t.closest(EDITABLE)) ||
    !!(t && t.parentElement && t.parentElement.closest(EDITABLE));

  let lastNote = 0;
  const note = msg => {
    const now = Date.now();
    if (now - lastNote < 2500) return;
    lastNote = now;
    if (typeof toast === 'function') toast(msg, 'err');
  };

  /* ----------------------------------------------------- copy and paste -- */
  const refuseClip = e => {
    if (editable(e.target) || editable(document.activeElement)) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.clipboardData) e.clipboardData.setData('text/plain', '');
    note('Copying page text is turned off. Code examples have their own Copy button.');
  };
  document.addEventListener('copy', refuseClip, true);
  document.addEventListener('cut', refuseClip, true);
  document.addEventListener('paste', e => { if (!editable(e.target)) e.preventDefault(); }, true);

  document.addEventListener('contextmenu', e => { if (!editable(e.target)) e.preventDefault(); }, true);
  document.addEventListener('dragstart', e => { if (!editable(e.target)) e.preventDefault(); }, true);

  /* ------------------------------------------------- inspect shortcuts -- */
  document.addEventListener('keydown', e => {
    const k = (e.key || '').toLowerCase();
    const mod = e.ctrlKey || e.metaKey;
    const devtools = k === 'f12' ||
      (mod && e.shiftKey && ['i', 'j', 'c', 'k', 'e'].includes(k)) ||   // Chrome / Edge / Firefox panels
      (e.metaKey && e.altKey && ['i', 'j', 'c', 'u'].includes(k));      // macOS
    const source = mod && !e.shiftKey && k === 'u';
    const save = mod && !e.shiftKey && (k === 's' || k === 'p');
    if (devtools || source || (save && !editable(e.target))) {
      e.preventDefault();
      e.stopPropagation();
      if (devtools || source) note('Developer tools are turned off on this site.');
    }
  }, true);

  /* ------------------------------------- developer tools left open anyway -- *
     A `debugger` statement costs nothing with developer tools closed and pauses
     when they are open, so a long gap means they are open. No false positives
     for ordinary readers; anyone who deactivates breakpoints gets past it,
     which is the honest limit of any client-side check. */
  const shield = document.createElement('div');
  shield.className = 'eg-shield';
  shield.setAttribute('role', 'alert');
  shield.innerHTML = '<div><b>Developer tools are open</b><span>Close them to keep reading.</span></div>';
  let shielded = false;
  const setShield = v => {
    if (v === shielded) return;
    shielded = v;
    document.documentElement.classList.toggle('eg-shielded', v);
    if (v) document.body.appendChild(shield); else shield.remove();
  };
  const probe = new Function('debugger');      // its own frame, so the pause is on this line only
  setInterval(() => {
    const t = performance.now();
    probe();
    setShield(performance.now() - t > 120);
  }, 1500);

  /* ---------------------------------------------------------- watermark -- */
  function watermark(text) {
    if (!text || document.getElementById('egWatermark')) return;
    const stamp = `${text} · ${new Date().toISOString().slice(0, 10)}`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="220">
      <text x="10" y="120" transform="rotate(-24 210 110)" font-family="sans-serif" font-size="15"
            fill="#7f7f7f">${stamp.replace(/[&<>"']/g, '')}</text></svg>`;
    const wm = document.createElement('div');
    wm.id = 'egWatermark';
    wm.className = 'eg-watermark';
    wm.setAttribute('aria-hidden', 'true');
    wm.style.setProperty('--eg-wm', `url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}")`);
    document.body.appendChild(wm);
    // Removing the node in the inspector brings it straight back.
    new MutationObserver(() => {
      if (!document.getElementById('egWatermark')) document.body.appendChild(wm);
    }).observe(document.body, { childList: true });
  }

  return { active: true, watermark };
})();
