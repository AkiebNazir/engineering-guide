import re

with open("webapp/static/index.html", "r") as f:
    content = f.read()

# Add variants and input to modal header
new_header = """    <div class="viz-modal-header">
      <div class="viz-modal-title-group" style="display: flex; align-items: center; gap: 16px;">
        <h2 id="vizModalTitle" class="viz-modal-title">Algorithm</h2>
        <div id="vizModalVariants" class="algo-variants"></div>
      </div>
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
    new_header,
    content,
    flags=re.DOTALL
)

with open("webapp/static/index.html", "w") as f:
    f.write(content)

print("index.html patched")

with open("webapp/static/dsa-viz.js", "r") as f:
    content = f.read()

# Update dsa-viz.js to use these new elements
# Add the logic for variants and input back

new_js = """  const modal = document.getElementById('vizModal');
  const root = modal;
  const wrap = document.getElementById('vizModalStage');
  const title = document.getElementById('vizModalTitle');
  const variantsContainer = document.getElementById('vizModalVariants');
  const inputEl = document.getElementById('vizModalInput');
  const runBtn = document.getElementById('vizModalRun');
  const explanation = document.getElementById('vizModalExplanation');
  const scrub = document.getElementById('vizSlider');
  const playBtn = document.getElementById('vizBtnPlayPause');
  const prevBtn = document.getElementById('vizBtnPrev');
  const nextBtn = document.getElementById('vizBtnNext');
  
  let spec = null;

  function load(k) {
    spec = list[k]; st.k = k;
    prefs[topicId] = k;
    try { localStorage.setItem('algo-prefs', JSON.stringify(prefs)); } catch (e) {}
    title.textContent = spec.title;
    st.variant = spec.variants ? spec.variants[0][0] : null;
    variantsContainer.innerHTML = spec.variants ? `<div class="seg">${spec.variants.map(([v, l]) => `<button type="button" data-variant="${v}" class="${v === st.variant ? 'is-on' : ''}">${l}</button>`).join('')}</div>` : '';
    
    // Bind variants click
    const vBtns = variantsContainer.querySelectorAll('[data-variant]');
    vBtns.forEach(b => b.onclick = () => {
      st.variant = b.dataset.variant;
      vBtns.forEach(btn => btn.classList.toggle('is-on', btn.dataset.variant === st.variant));
      run();
    });
    
    inputEl.value = spec.input;
    run();
  }

  runBtn.onclick = run;
  inputEl.onkeydown = (e) => { if (e.key === 'Enter') run(); };

  function run() {
    stop();
    try {
      st.frames = spec.run(spec.parse(inputEl.value), st.variant);
      if (!st.frames.length) throw new Error('Nothing to show for this input');
    } catch (e) {
      explanation.textContent = 'Error: ' + e.message;
      return;
    }
    scrub.max = st.frames.length - 1;
    go(0);
  }"""

content = re.sub(
    r'  const modal = document\.getElementById\(\'vizModal\'\);.*?function run\(\) \{.*?go\(0\);\n  \}',
    new_js,
    content,
    flags=re.DOTALL
)

with open("webapp/static/dsa-viz.js", "w") as f:
    f.write(content)

print("dsa-viz.js patched")

