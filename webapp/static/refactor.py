import re

with open('/Users/njasm/Njasm/AI/DSA-Practice/webapp/static/dsa-viz.js', 'r') as f:
    content = f.read()

# Extract the body of renderAlgoTab
match = re.search(r'function renderAlgoTab\(body, topicId\) \{(.*?)\n\}\n\n/\* ==', content, re.DOTALL)
old_body = match.group(1)

# We want to rename `renderAlgoTab` to `renderCanvasAlgo` and adjust its signature
canvas_algo = """function renderCanvasAlgo(body, list, topicId, initialK, loadAlgo) {
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) { /* private mode */ }
  const st = { k: initialK, variant: null, frames: [], i: 0, playing: false, speed: prefs.speed || 1, acc: 0, raf: 0 };
""" + old_body[old_body.find("body.innerHTML = `"):]

# Replace `load(k)` with `loadAlgo(k)` inside canvas_algo
canvas_algo = canvas_algo.replace("function load(k) {", "function load(k) {\n    if(list[k].type === 'dom') return loadAlgo(k);")
canvas_algo = canvas_algo.replace("load(+b.dataset.pick);", "loadAlgo(+b.dataset.pick);")

new_render_algo = """function renderAlgoTab(body, topicId) {
  const list = ALGOS[topicId];
  if (!list || !list.length) {
    body.innerHTML = emptyMsg('No visualizer for this topic yet', 'The Question, Solution and Topic guide tabs have everything else.');
    return;
  }
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) { }
  
  function loadAlgo(k) {
    prefs[topicId] = k;
    try { localStorage.setItem('algo-prefs', JSON.stringify(prefs)); } catch (e) { }
    const spec = list[k];
    if (spec.type === 'dom') {
      renderDomAlgo(body, list, topicId, k, loadAlgo);
    } else {
      renderCanvasAlgo(body, list, topicId, k, loadAlgo);
    }
  }
  
  let initialK = Math.min(list.length - 1, prefs[topicId] || 0);
  loadAlgo(initialK);
}
"""

new_dom_algo = """function renderDomAlgo(body, list, topicId, k, loadAlgo) {
    const spec = list[k];
    
    body.innerHTML = `
    <div class="dom-algo" tabindex="-1">
      <div class="algo-head">
        <div class="algo-titles"><p class="algo-kicker">Step-by-step visualizer</p><h3 class="algo-title">${esc(spec.title)}</h3></div>
        ${list.length > 1 ? `<div class="seg algo-pick">${list.map((a, i) => `<button type="button" data-pick="${i}" class="${i === k ? 'is-on' : ''}">${esc(a.short || a.title)}</button>`).join('')}</div>` : ''}
      </div>
      <p class="algo-idea">${spec.idea}</p>
      
      <div class="glass-panel controls-grid">
        <div style="flex:1;">
            <label>${spec.hint || 'Input'}</label>
            <input type="text" class="dom-input" value="${spec.input}">
        </div>
        <button class="btn-primary btn-apply">Initialize</button>
        <button class="btn-play dom-play">▶ Auto-Run</button>
      </div>
      <div class="text-error dom-err" style="color:var(--err);font-size:12px;display:none;margin:-6px 0 6px;"></div>

      <div class="workspace">
          <div class="main-col">
              <div class="dom-render-container" style="flex:1; display:flex; flex-direction:column; gap:10px;"></div>

              <!-- Inline Explanation Box -->
              <div class="glass-panel explanation-box" style="border-color: var(--accent); background: color-mix(in srgb, var(--accent) 5%, transparent); flex-shrink: 0;">
                  <div class="panel-heading" style="color: var(--accent); margin-bottom: 6px;">
                      <span style="display:flex; align-items:center; gap:6px;">ℹ️ <span class="expl-title">Concept</span></span>
                  </div>
                  <p class="expl-text" style="font-size: 0.9rem; color: var(--text); line-height: 1.4; min-height: 38px;">Ready to begin.</p>
                  <div class="explanation-actions" style="margin-top: 8px; display: none;">
                      <button class="btn-play btn-expl-resume" style="padding: 6px 12px; font-size: 0.8rem;">▶ Resume Auto-Run</button>
                  </div>
              </div>
          </div>

          <div class="glass-panel code-panel">
              <div class="panel-heading">Execution Trace</div>
              <ul class="pseudo-code">
                  ${spec.code.map((ln, i) => `<li data-line="${i+1}">${esc(ln).replace(/ /g, '&nbsp;')}</li>`).join('')}
              </ul>
              <div style="margin-top: 16px; display: flex; gap: 8px; flex-shrink: 0;">
                  <button class="btn-ghost dom-prev" style="flex: 1; padding: 8px;" disabled>◀ Prev</button>
                  <button class="btn-ghost dom-next" style="flex: 1; padding: 8px;">Next ▶</button>
              </div>
          </div>
      </div>

      <div class="status-bar">
          <div style="font-family: var(--mono); font-size: 0.75rem;" class="step-counter">Step 0 / 0</div>
          <div class="progress-container"><div class="progress-bar"></div></div>
          <div style="font-size: 0.8rem; font-weight: 500;" class="milestone-status">Ready</div>
      </div>
      <p class="algo-complexity">${spec.complexity}</p>
    </div>`;

    const root = body.querySelector('.dom-algo');
    const inputEl = root.querySelector('.dom-input');
    const errEl = root.querySelector('.dom-err');
    const btnApply = root.querySelector('.btn-apply');
    const btnPlay = root.querySelector('.dom-play');
    const btnPrev = root.querySelector('.dom-prev');
    const btnNext = root.querySelector('.dom-next');
    const btnResume = root.querySelector('.btn-expl-resume');
    const renderContainer = root.querySelector('.dom-render-container');
    const explTitle = root.querySelector('.expl-title');
    const explText = root.querySelector('.expl-text');
    const explActions = root.querySelector('.explanation-actions');
    const stepCounter = root.querySelector('.step-counter');
    const progressBar = root.querySelector('.progress-bar');
    const milestoneStatus = root.querySelector('.milestone-status');
    const codeLines = root.querySelectorAll('.pseudo-code li');

    let states = [];
    let currentStep = 0;
    let playInterval = null;

    function renderState() {
        if (!states.length) return;
        const s = states[currentStep];

        // Let the spec render the specific DOM components (arrays, maps, etc)
        spec.renderDOM(renderContainer, s, spec);

        // Highlight code
        codeLines.forEach(li => li.className = '');
        if (s.line) {
            const activeLine = root.querySelector(`.pseudo-code li[data-line="${s.line}"]`);
            if (activeLine) {
                activeLine.classList.add('active');
                if (s.color) activeLine.classList.add(s.color);
            }
        }

        // Status
        stepCounter.innerText = `Step ${currentStep + 1} / ${states.length}`;
        progressBar.style.width = `${((currentStep + 1) / states.length) * 100}%`;
        milestoneStatus.innerText = (s.kind || '').toUpperCase().replace(/-/g, ' ');

        // Buttons
        btnPrev.disabled = currentStep === 0;
        btnNext.disabled = currentStep === states.length - 1;
        
        // Explanation
        explTitle.innerText = s.explTitle || 'Concept';
        explText.innerText = s.explText || '';
        
        if (s.pause && playInterval) {
            pausePlay();
            explActions.style.display = 'block';
        } else {
            explActions.style.display = 'none';
        }
        
        if (currentStep === states.length - 1) pausePlay();
    }

    function parseAndInit() {
        errEl.style.display = 'none';
        try {
            const parsed = spec.parse(inputEl.value);
            states = spec.buildStates(parsed);
            if (!states.length) throw new Error("No steps generated.");
            currentStep = 0;
            renderState();
        } catch(e) {
            errEl.innerText = e.message;
            errEl.style.display = 'block';
        }
    }

    function pausePlay() {
        clearInterval(playInterval);
        playInterval = null;
        btnPlay.innerHTML = '▶ Auto-Run';
    }

    btnApply.addEventListener('click', () => { pausePlay(); parseAndInit(); });
    
    btnNext.addEventListener('click', () => {
        pausePlay(); explActions.style.display = 'none';
        if (currentStep < states.length - 1) { currentStep++; renderState(); }
    });
    
    btnPrev.addEventListener('click', () => {
        pausePlay(); explActions.style.display = 'none';
        if (currentStep > 0) { currentStep--; renderState(); }
    });

    btnPlay.addEventListener('click', () => {
        if (playInterval) {
            pausePlay();
        } else {
            if (currentStep === states.length - 1) currentStep = 0;
            btnPlay.innerHTML = '❚❚ Pause';
            playInterval = setInterval(() => {
                if (currentStep < states.length - 1) { currentStep++; renderState(); }
                else pausePlay();
            }, spec.speedMs || 600);
        }
    });

    btnResume.addEventListener('click', () => {
        explActions.style.display = 'none';
        btnPlay.click();
    });

    root.addEventListener('click', e => {
        const pick = e.target.closest('[data-pick]');
        if (pick) loadAlgo(+pick.dataset.pick);
    });

    parseAndInit();
}
"""

new_content = content[:match.start()] + new_render_algo + "\n" + canvas_algo + "\n" + new_dom_algo + "\n\n/* ==" + content[match.end():]

with open('/Users/njasm/Njasm/AI/DSA-Practice/webapp/static/dsa-viz.js', 'w') as f:
    f.write(new_content)

