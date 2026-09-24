import re

with open("webapp/static/index.html", "r") as f:
    content = f.read()

# Add vizModalVars below vizModalHeader
new_html = """    <div class="viz-modal-header">
      <div class="viz-modal-title-group" style="display: flex; align-items: center; gap: 16px;">
        <h2 id="vizModalTitle" class="viz-modal-title">Algorithm</h2>
        <div id="vizModalVariants" class="algo-variants"></div>
      </div>
      <div id="vizModalVars" class="viz-modal-vars" style="display: flex; gap: 8px; flex: 1; justify-content: center;"></div>
      <div class="viz-modal-input-group" style="display: flex; align-items: center; gap: 8px;">
        <label style="font-size: 0.9em; color: var(--text-muted);">Input: <input type="text" id="vizModalInput" class="viz-modal-input" spellcheck="false" style="background: var(--bg-base); color: var(--text-main); border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px;"></label>
        <button id="vizModalRun" class="btn btn-primary" style="padding: 4px 12px;">Run</button>
      </div>
      <button id="vizModalClose" class="icon-btn viz-modal-close" aria-label="Close" title="Close">
        <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>"""

content = re.sub(
    r'<div class="viz-modal-header">.*?</div>',
    new_html,
    content,
    flags=re.DOTALL
)

with open("webapp/static/index.html", "w") as f:
    f.write(content)


with open("webapp/static/dsa-viz.js", "r") as f:
    content = f.read()

# Add esc function if not present or make sure it's accessible. It should be in app.js globally.
# Add vars logic inside paint()
old_paint = """    explanation.innerHTML = f.note || '';
    scrub.value = st.i;"""
new_paint = """    explanation.innerHTML = f.note || '';
    document.getElementById('vizModalVars').innerHTML = Object.entries(f.vars || {}).map(([k, v]) => `<span class="stat-chip"><span>${typeof esc === 'function' ? esc(k) : k}</span><b>${typeof esc === 'function' ? esc(typeof v === 'object' ? JSON.stringify(v) : String(v)) : (typeof v === 'object' ? JSON.stringify(v) : String(v))}</b></span>`).join('');
    scrub.value = st.i;"""

content = content.replace(old_paint, new_paint)

with open("webapp/static/dsa-viz.js", "w") as f:
    f.write(content)

print("Vars added back")
