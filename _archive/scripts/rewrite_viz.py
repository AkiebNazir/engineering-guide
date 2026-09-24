import re

with open("webapp/static/dsa-viz.js", "r") as f:
    content = f.read()

# I want to rewrite renderAlgoTab
# It starts at `function renderAlgoTab(body, topicId) {` and ends before `defineAlgo('01_arrays_hashing'`
match = re.search(r"function renderAlgoTab\(body, topicId\) \{.*?defineAlgo\('01_arrays_hashing'", content, flags=re.DOTALL)
if match:
    old_block = match.group(0).replace("defineAlgo('01_arrays_hashing'", "")
    # print(old_block)
    
new_block = """function renderAlgoTab(body, topicId) {
  const list = ALGOS[topicId];
  if (!list || !list.length) {
    body.innerHTML = emptyMsg('No visualizer for this topic yet', 'The Question, Solution and Topic guide tabs have everything else.');
    return;
  }
  
  // Clear the body and show a message that it's in a modal
  body.innerHTML = `
    <div class="algo-placeholder" style="padding: 40px; text-align: center;">
      <h3>Visualization is running in full screen mode</h3>
      <button class="btn btn-primary" style="margin-top: 20px;" onclick="document.getElementById('vizModal').showModal()">Re-open Visualizer</button>
    </div>
  `;

  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) {}
  const st = { k: Math.min(list.length - 1, prefs[topicId] || 0), variant: null, frames: [], i: 0, playing: false, speed: prefs.speed || 1, acc: 0, raf: 0 };
  
  const modal = document.getElementById('vizModal');
  const root = modal;
  const wrap = document.getElementById('vizModalStage');
  const title = document.getElementById('vizModalTitle');
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
    run();
  }

  function run() {
    stop();
    try {
      st.frames = spec.run(spec.parse(spec.input), st.variant);
      if (!st.frames.length) throw new Error('Nothing to show for this input');
    } catch (e) {
      explanation.textContent = 'Error: ' + e.message;
      return;
    }
    scrub.max = st.frames.length - 1;
    go(0);
  }

  function go(i) {
    st.i = clamp(i, 0, st.frames.length - 1);
    paint();
  }

  function paint() {
    const f = st.frames[st.i];
    if (!f) return;
    
    explanation.innerHTML = f.note || '';
    scrub.value = st.i;
    
    playBtn.querySelector('.btn-text').textContent = st.playing ? 'Pause' : st.i >= st.frames.length - 1 ? 'Replay' : 'Play';
    playBtn.querySelector('.ico-play').hidden = st.playing;
    playBtn.querySelector('.ico-pause').hidden = !st.playing;
    
    draw();
  }

  function draw() {
    if (!modal.open) return;
    const f = st.frames[st.i];
    const w = Math.max(280, wrap.clientWidth || 600);
    const h = Math.round(spec.height ? spec.height(w, st.frames[st.frames.length - 1], st.frames) : 260);
    const P = labPalette(modal);

    if (spec.renderDOM) {
      wrap.style.display = 'flex';
      wrap.style.height = `${h}px`;
      try { spec.renderDOM(wrap, { w, h }, f, P, st.frames); } catch (e) { console.error(e); }
    } else {
      // Fallback for canvas based algos (not fully ported yet)
      wrap.innerHTML = `<canvas></canvas>`;
      const cv = wrap.querySelector('canvas');
      const ctx = cv.getContext('2d');
      const d = window.devicePixelRatio || 1;
      cv.width = Math.round(w * d); cv.height = Math.round(h * d); cv.style.height = `${h}px`;
      ctx.setTransform(d, 0, 0, d, 0, 0);
      try { spec.draw(ctx, { w, h }, f, P, st.frames); } catch (e) { console.error(e); }
    }
  }

  function tick(now) {
    if (!st.playing || !modal.open) { st.playing = false; paint(); return; }
    const dt = Math.min(100, now - (st.last || now));
    st.last = now;
    st.acc += dt * st.speed;
    if (st.acc >= 850) {
      st.acc = 0;
      if (st.i >= st.frames.length - 1) { stop(); return; }
      go(st.i + 1);
    }
    st.raf = requestAnimationFrame(tick);
  }

  function play() {
    if (st.playing) return;
    if (st.i >= st.frames.length - 1) go(0);
    st.playing = true; st.last = performance.now(); st.acc = 0;
    st.raf = requestAnimationFrame(tick);
    paint();
  }

  function stop() {
    st.playing = false;
    cancelAnimationFrame(st.raf);
    paint();
  }
  
  // Event Listeners (ensure we don't duplicate by clearing old ones if any)
  playBtn.onclick = () => { if (st.playing) stop(); else play(); };
  prevBtn.onclick = () => { stop(); go(st.i - 1); };
  nextBtn.onclick = () => { stop(); go(st.i + 1); };
  scrub.oninput = (e) => { stop(); go(+e.target.value); };
  
  document.getElementById('vizModalClose').onclick = () => {
    stop();
    modal.close();
  };

  // Start
  modal.showModal();
  load(st.k);
}
"""

if match:
    content = content.replace(old_block, new_block)
    with open("webapp/static/dsa-viz.js", "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find block")
