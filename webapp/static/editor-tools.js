/* ============================================================================
   Edit toolbar for the code editors: Select all, Copy, Cut, Paste, Delete,
   Undo, Redo as buttons.

   Keyboard shortcuts and the right-click menu cover a desktop, but on a phone
   CodeMirror's long-press menu is unreliable (it often selects a word, then
   offers nothing), so every edit action is also one tap away. Used by the main
   workspace editor (DSA, engineering, API, stdlib) and the Query Lab editor.

   Without a selection, Copy / Cut / Delete act on the cursor's line, as in VS Code.
   ========================================================================= */
const EDIT_ICONS = {
  selectAll: '<path d="M4 7V4h3M17 4h3v3M20 17v3h-3M7 20H4v-3"/><path d="M9 9h6v6H9z"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 012-2h8"/>',
  cut: '<circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><path d="M8.1 16L19 4M15.9 16L5 4"/>',
  paste: '<path d="M9 4h6v3H9z"/><path d="M15 5h2a2 2 0 012 2v12a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h2"/>',
  del: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3"/>',
  undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 010 11H11"/>',
  redo: '<path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 000 11H13"/>',
};
const EDIT_ACTIONS = [
  ['selectAll', 'Select all', 'Select all'],
  ['copy', 'Copy', 'Copy the selection, or the current line'],
  ['cut', 'Cut', 'Cut the selection, or the current line'],
  ['paste', 'Paste', 'Paste from the clipboard'],
  ['del', 'Delete', 'Delete the selection, or the current line'],
  ['undo', 'Undo', 'Undo'],
  ['redo', 'Redo', 'Redo'],
];

const editToast = (msg, kind = 'ok') => { if (typeof toast === 'function') toast(msg, kind); };

/* navigator.clipboard needs a secure context (https or localhost); the textarea +
   execCommand fallback covers everything else. */
async function clipboardWrite(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;font-size:16px';
    document.body.append(ta);
    ta.select();
    ta.setSelectionRange(0, text.length);
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (err) { /* unsupported */ }
    ta.remove();
    return ok;
  }
}

// The text a Copy / Cut / Delete acts on: the selection, else the cursor's whole line.
function selectionOrLine(cm) {
  if (cm.somethingSelected()) return { text: cm.getSelection(), line: false };
  const { line } = cm.getCursor();
  const last = line === cm.lastLine();
  cm.setSelection({ line, ch: 0 }, last ? { line, ch: cm.getLine(line).length } : { line: line + 1, ch: 0 });
  return { text: cm.getSelection() + (last ? '\n' : ''), line: true };
}

async function runEditAction(cm, act) {
  const ro = cm.getOption && cm.getOption('readOnly');
  switch (act) {
    case 'selectAll': cm.execCommand('selectAll'); break;
    case 'copy': {
      const had = cm.somethingSelected(), cursor = cm.getCursor();
      const { text, line } = selectionOrLine(cm);
      if (!had) cm.setCursor(cursor);           // copying a line leaves the cursor where it was
      if (!text) return;
      editToast(await clipboardWrite(text) ? (line ? 'Line copied' : 'Copied') : 'The browser blocked the clipboard', 'ok');
      break;
    }
    case 'cut': {
      if (ro) return;
      const { text, line } = selectionOrLine(cm);
      if (!text) return;
      if (await clipboardWrite(text)) { cm.replaceSelection(''); editToast(line ? 'Line cut' : 'Cut'); }
      else editToast('The browser blocked the clipboard', 'err');
      break;
    }
    case 'paste': {
      if (ro) return;
      let text = null;
      try { text = await navigator.clipboard.readText(); } catch (e) { /* denied or unsupported */ }
      if (text == null) {
        editToast('The browser did not allow pasting from this button. Long-press in the editor and choose Paste, or press Ctrl/⌘+V.', 'warn');
        return;
      }
      cm.replaceSelection(text);
      break;
    }
    case 'del':
      if (ro) return;
      selectionOrLine(cm);
      cm.replaceSelection('');
      break;
    case 'undo': cm.undo(); break;
    case 'redo': cm.redo(); break;
  }
  // On a touch screen, focusing the editor would pop the keyboard up after every tap.
  if (!matchMedia('(pointer: coarse)').matches) cm.focus();
}

/* Insert the toolbar just above `anchor` (the editor's host). getEditor() returns the
   current editor: the Query Lab builds a new one per question. */
function mountEditBar(anchor, getEditor) {
  const bar = document.createElement('div');
  bar.className = 'edit-bar';
  bar.setAttribute('role', 'toolbar');
  bar.setAttribute('aria-label', 'Edit');
  bar.innerHTML = EDIT_ACTIONS.map(([act, label, title], i) =>
    `${i === 5 ? '<span class="edit-sep" aria-hidden="true"></span>' : ''}<button type="button" class="edit-btn" data-edit="${act}" title="${title}" aria-label="${title}">
      <svg viewBox="0 0 24 24" aria-hidden="true">${EDIT_ICONS[act]}</svg><span>${label}</span></button>`).join('');
  // Keep the editor's focus and selection when a button is pressed with a mouse.
  bar.addEventListener('mousedown', e => { if (e.target.closest('.edit-btn')) e.preventDefault(); });
  bar.addEventListener('click', e => {
    const b = e.target.closest('.edit-btn');
    const cm = getEditor();
    if (b && cm && typeof cm.execCommand === 'function') runEditAction(cm, b.dataset.edit);
  });
  anchor.before(bar);
  return bar;
}
