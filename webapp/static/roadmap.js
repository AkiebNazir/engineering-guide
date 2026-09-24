/* ============================================================================
   AI Roadmap day pages — turns the fixed lesson shape into things to do.

     Hour track       the day's three hours as a clickable progress track
     Labs             interactive visualizations next to the theory (viz*.js)
     Takeaways        numbered cards
     Build challenge  requirements become a saved checklist
     Mock interview   question card, countdown, saved draft, self-graded rubric
     End of day       a finish line with "Mark day complete"
     Glossary terms   dotted terms with pop-up definitions from Day 0
     Day 0            the glossary itself: searchable cards, flashcards, quiz
   ========================================================================= */
'use strict';

const GLOSSARY_ID = '0_day_prerequisites_and_notation';

/* Which labs appear on which day. [lab, options] when a lab needs a setup. */
const DAY_LABS = {
  1: ['vectors'], 2: ['matrix'], 3: [['matrix', { eigen: true }]], 4: ['svd'], 5: ['norms', 'vectors'], 6: ['backprop'],
  7: ['vectors', 'matrix'], 8: ['bayes'], 9: [['distributions', { mode: 'clt' }]], 10: ['mle'], 11: ['entropy'],
  12: ['distributions'], 13: [['distributions', { mode: 'clt' }]], 14: ['bayes'], 15: ['gradient'], 16: [['gradient', { noise: 1.2 }]],
  17: [['gradient', { surface: 'ravine' }]], 18: ['lrschedule'], 19: [['norms', { reg: true }]], 20: ['gradient'], 21: ['gradient', 'lrschedule'],
  22: ['regression'], 23: [['regression', { mode: 'logistic' }], 'softmax'], 24: ['tree'], 25: [['tree', { forest: true }]], 26: ['tree'],
  27: ['kmeans'], 28: ['pca'], 31: ['activation'], 32: ['activation'], 33: ['backprop'], 34: ['init'], 35: ['entropy'],
  36: [['init', { ln: true }]], 38: ['convolution'], 39: ['convolution'], 40: ['convolution'], 41: ['convolution'], 42: ['convolution'],
  43: ['rnn'], 44: [['rnn', { lstm: true }]], 45: [['rnn', { lstm: true }]], 46: ['rnn', 'attention'], 47: ['attention'], 48: ['embeddings'],
  49: ['bpe'], 51: ['convolution'], 52: ['softmax'], 56: ['diffusion'], 57: ['diffusion'], 58: ['diffusion'], 59: ['gnn'], 60: ['embeddings'],
  61: ['attention'], 62: ['attention'], 63: ['posenc'], 64: ['activation'], 65: ['attention'], 66: [['attention', { causal: true }], 'softmax'],
  67: ['attention'], 68: ['attention'], 69: ['softmax', 'scaling'], 71: ['attention'], 72: ['attention'], 73: ['bpe'], 76: ['softmax'],
  78: ['quantization'], 79: ['moe'], 80: ['rnn'], 81: ['posenc', 'attention'], 82: ['attention'], 83: ['rag'], 84: ['rag'], 85: ['rag', 'kmeans'],
  86: ['embeddings', 'vectors'], 87: ['embeddings', 'kmeans'], 88: ['softmax'], 89: ['agentloop'], 90: ['rag'], 91: ['scaling'],
  93: ['distributed'], 94: ['quantization', 'distributed'], 95: ['distributed'], 96: ['lora'], 97: ['lora'], 98: ['lora', 'quantization'],
  108: ['vectors'], 111: ['softmax'], 112: ['softmax'], 113: ['agentloop'], 115: ['agentloop'], 118: ['quantization'], 121: ['agentloop'],
  123: ['agentloop'], 124: ['agentloop'], 131: ['agentloop'], 132: ['agentloop'], 138: ['agentloop'], 141: ['rag', 'agentloop'],
  147: ['serving'], 151: ['serving'], 152: ['serving', 'quantization'], 154: ['distributed'], 155: ['quantization'], 156: ['semcache'],
  157: ['serving'], 159: ['drift'], 167: ['drift'], 168: ['drift'], 172: ['rag'],
};

/* Where a lab goes: after the first Hour-1 subsection whose heading matches. */
const LAB_PLACE = {
  vectors: [/dot product|cosine|task vector/i, /vector/i], matrix: [/eigen|transform/i, /matri/i], svd: /svd|singular|low.rank|approximat/i,
  norms: /norm|distance|l1|l2|regulari|lasso|ridge/i, backprop: /chain rule|backprop|computational graph|jacobian|autograd/i,
  bayes: /bayes|conditional|base rate|posterior/i, distributions: /distribution|central limit|clt|gaussian|sampl|monte carlo|hypothesis/i,
  mle: /likelihood|mle|map|prior/i, entropy: /entropy|kl|cross.entropy|information/i,
  gradient: /gradient|momentum|adam|rmsprop|sgd|optimi|convex/i, lrschedule: /schedul|warmup|cosine|decay/i,
  regression: /regression|normal equation|least squares|logistic|sigmoid/i, tree: /gini|split|tree|forest|bagging|boost/i,
  kmeans: /k.means|centroid|cluster|ivf/i, pca: /pca|principal|variance/i, activation: /activation|relu|gelu|sigmoid|perceptron|universal|feed.forward/i,
  init: /xavier|kaiming|initiali|normaliz|batchnorm|layernorm/i, convolution: /convolution|kernel|filter|receptive|feature map|stride/i,
  rnn: /vanishing|through time|bptt|gate|lstm|gru|recurrent|state space/i, diffusion: /noise|forward process|diffusion|latent|reparam/i,
  gnn: /message passing|aggregat|graph/i, attention: /attention|query|keys?\b|mask|head/i, embeddings: /word2vec|skip.gram|embedding|analog|contrastive/i,
  bpe: /bpe|byte.pair|merge|subword|token/i, softmax: /temperature|top.k|top.p|nucleus|perplexity|sampling|decod|distill/i,
  posenc: /positional|sinusoid|rope|rotary/i, scaling: /scaling|chinchilla|compute/i, quantization: /quantiz|int8|int4|precision|fp16|bf16|awq|gptq|nf4/i,
  moe: /expert|gating|router|sparse/i, rag: /chunk|retriev|rerank|hybrid|rag/i, distributed: /zero|fsdp|parallel|memory/i,
  lora: /lora|low.rank|rank|adapter/i, agentloop: /react|loop|tool|function call|agent|reason/i,
  serving: /batching|continuous|paged|kv|throughput|serving|queue|autoscal|load balanc/i, semcache: /semantic|cach/i, drift: /drift|psi|monitor/i,
};

const takeUntil = (start, stop) => {
  const out = [];
  for (let n = start.nextElementSibling; n && !stop(n); n = n.nextElementSibling) out.push(n);
  return out;
};
const stripEmoji = h => {
  const t = h.firstChild;
  if (t && t.nodeType === 3) t.textContent = t.textContent.replace(/^[\p{Extended_Pictographic}️\s]+/u, '');
  h.dataset.label = (h.dataset.label || h.textContent).replace(/^[\p{Extended_Pictographic}️\s]+/u, '');
};

function enhanceRoadmapDay(host, prose, item, key) {
  prose.classList.add('roadmap-day');
  const day = item.kind === 'day' ? item.day : null;
  if (item.id === GLOSSARY_ID) buildGlossary(host, prose, key);

  markCodeFilenames(prose);
  upgradeTakeaways(prose);
  $$('h3', prose).forEach(h => { if (/the challenge/i.test(h.textContent)) upgradeChallenge(h, key); });
  $$('h3', prose).forEach(h => { if (/interview prep|mock interview/i.test(h.textContent)) upgradeInterview(h, key); });
  upgradeEndOfDay(prose);
  const labs = day != null ? mountDayLabs(prose, day) : 0;
  buildHourTrack(host, prose, labs);

  return {
    async afterRender() {
      if (item.id !== GLOSSARY_ID) await linkGlossaryTerms(prose);
      if (item.id === GLOSSARY_ID) paintGlossaryKnown(host, key);
    },
  };
}

/* ------------------------------------------------------------ hour track -- */
function buildHourTrack(host, prose, labs) {
  const hours = $$('.sec', prose).filter(s => /^hour/i.test($(':scope > h2 .h-step', s)?.textContent || ''));
  const meta = $('.doc-meta', host);
  if (labs && meta) meta.insertAdjacentHTML('beforeend', `<span class="doc-labs">${labs} interactive lab${labs > 1 ? 's' : ''}</span>`);
  if (hours.length < 2) return;
  const kind = t => /code|guided|exercise/i.test(t) ? 'Code-along' : /challenge|interview|assessment|capstone/i.test(t) ? 'Build & interview' : 'Theory';
  const track = document.createElement('ol');
  track.className = 'hour-track';
  track.innerHTML = hours.map((sec, i) => {
    const h2 = $('h2', sec), label = h2.dataset.label.replace(/^(hour|step|part|phase)\s*\d+\s*/i, '');
    return `<li data-sid="${sec.dataset.sid}"><button type="button" data-target="${h2.id}">
      <span class="ht-dot"><b>${i + 1}</b><svg viewBox="0 0 24 24">${CHECK_PATH}</svg></span>
      <span class="ht-text"><small>Hour ${i + 1} · ${kind(label)}</small><span>${esc(label)}</span></span></button></li>`;
  }).join('');
  meta.after(track);
}

function paintRoadmapDay() {
  if (!curDoc || curDoc.mod !== 'roadmap') return;
  const r = docRec(curDoc.key);
  const track = $('.hour-track');
  if (track) {
    const items = $$('li', track);
    items.forEach(li => li.classList.toggle('is-done', r.sections.includes(li.dataset.sid)));
    track.style.setProperty('--done', items.filter(li => li.classList.contains('is-done')).length / Math.max(1, items.length - 1));
  }
  $$('.eod').forEach(e => {
    e.classList.toggle('is-done', !!r.done);
    const b = $('[data-act="complete"]', e);
    if (b) b.textContent = r.done ? 'Day complete ✓' : 'Mark day complete';
  });
}

/* ------------------------------------------------------------------ labs -- */
function mountDayLabs(prose, day) {
  const list = DAY_LABS[day];
  if (!list || typeof createLab !== 'function') return 0;
  const hour1 = $$('.sec', prose).find(s => /hour\s*1/i.test($(':scope > h2', s)?.dataset.label || '')) || $$('.sec', prose).find(s => !s.classList.contains('sec-intro'));
  if (!hour1) return 0;
  const h3s = $$(':scope > h3', hour1);
  let count = 0;
  list.forEach(entry => {
    const [name, opts] = Array.isArray(entry) ? entry : [entry, {}];
    const fig = createLab(name, opts);
    if (!fig) return;
    // patterns are tried in order, most specific first
    const patterns = [].concat(LAB_PLACE[name] || []);
    let match = null;
    for (const re of patterns) { match = h3s.find(h => re.test(h.dataset.label || h.textContent)); if (match) break; }
    if (match) {
      const anchor = h3s[h3s.indexOf(match) + 1] || $(':scope > .sec-foot', hour1);
      anchor ? anchor.before(fig) : hour1.append(fig);
    } else {
      const foot = $(':scope > .sec-foot', hour1);
      foot ? foot.before(fig) : hour1.append(fig);
    }
    count++;
  });
  return count;
}

/* ------------------------------------------------------ lesson structure -- */
function markCodeFilenames(prose) {
  $$('p', prose).forEach(p => {
    if (!/file (named|called)|create (a )?file/i.test(p.textContent)) return;
    const code = $('code', p), pre = p.nextElementSibling;
    if (code && pre && pre.tagName === 'PRE' && /\.\w{1,5}$/.test(code.textContent)) pre.dataset.filename = code.textContent;
  });
}

function upgradeTakeaways(prose) {
  $$('h3', prose).forEach(h => {
    if (!/key takeaways/i.test(h.textContent)) return;
    const list = h.nextElementSibling;
    if (!list || !/^(OL|UL)$/.test(list.tagName)) return;
    list.classList.add('takeaways');
    $$(':scope > li', list).forEach(li => {
      const first = [...li.childNodes].find(n => !(n.nodeType === 3 && !n.textContent.trim()));
      if (first && first.nodeName === 'STRONG') {
        first.classList.add('tk-title');
        const after = first.nextSibling;
        if (after && after.nodeType === 3) after.textContent = after.textContent.replace(/^\s*:?\s*/, '');
      }
    });
    h.classList.add('takeaways-head');
  });
}

function upgradeChallenge(h3, key) {
  const block = takeUntil(h3, n => /^(H2|H3|HR)$/.test(n.tagName) || n.classList.contains('sec-foot') || n.classList.contains('lab'));
  const card = document.createElement('div');
  card.className = 'challenge';
  card.innerHTML = `<div class="ch-head"><span class="ch-icon" aria-hidden="true">🛠️</span><div class="ch-titles"><p class="ch-kicker">Build challenge</p></div><span class="ch-progress"></span></div><div class="ch-body"></div>`;
  h3.before(card);
  stripEmoji(h3);
  const title = h3.dataset.label.replace(/^the challenge:?\s*/i, '');
  h3.firstChild && h3.firstChild.nodeType === 3 && (h3.firstChild.textContent = title || 'The challenge');
  h3.dataset.label = `Challenge: ${title}`;
  $('.ch-titles', card).append(h3);
  const body = $('.ch-body', card);
  body.append(...block);
  body.querySelectorAll('p').forEach(p => { if (/^\s*why this matters/i.test(p.textContent)) p.classList.add('ch-why'); });
  const reqP = [...body.children].find(n => n.tagName === 'P' && /requirements/i.test(n.querySelector('strong')?.textContent || ''));
  let list = reqP ? takeUntil(reqP, n => n.tagName === 'P' && n.querySelector('strong'))[0] : null;
  if (!list || !/^(OL|UL)$/.test(list.tagName)) list = [...body.children].filter(n => /^(OL|UL)$/.test(n.tagName)).pop();
  if (!list) return;
  list.classList.add('task-list');
  const items = $$(':scope > li', list);
  const paint = () => {
    const done = docRec(key).tasks || [];
    items.forEach((li, i) => { const on = done.includes(i); li.classList.toggle('is-done', on); $('.task-check', li).setAttribute('aria-pressed', on); });
    $('.ch-progress', card).textContent = `${done.length} of ${items.length} done`;
    card.classList.toggle('is-complete', done.length === items.length);
  };
  items.forEach((li, i) => {
    li.insertAdjacentHTML('afterbegin', `<button type="button" class="task-check" data-i="${i}" aria-label="Mark requirement ${i + 1} done"><svg viewBox="0 0 24 24">${CHECK_PATH}</svg></button>`);
  });
  card.addEventListener('click', e => {
    const b = e.target.closest('.task-check');
    if (!b) return;
    const i = +b.dataset.i, cur = docRec(key).tasks || [];
    const tasks = cur.includes(i) ? cur.filter(x => x !== i) : [...cur, i];
    docSave(key, { tasks });
    paint();
    if (tasks.length === items.length && !cur.includes(i)) toast('Every requirement ticked. Nice build.', 'ok');
  });
  paint();
}

function upgradeInterview(h3, key) {
  const isEod = n => n.tagName === 'P' && /^task for the end of the day/i.test(n.querySelector('strong')?.textContent || '');
  const block = takeUntil(h3, n => /^(H2|H3|HR)$/.test(n.tagName) || n.classList.contains('sec-foot') || isEod(n));
  const spend = block.find(n => n.tagName === 'P' && /^spend\s+\d+/i.test(n.textContent.trim()));
  const minutes = +(spend?.textContent.match(/(\d+)\s*min/i)?.[1] || 15);
  const qi = block.findIndex(n => n.tagName === 'P' && /the question/i.test(n.querySelector('strong')?.textContent || ''));
  let question = '';
  if (qi >= 0) {
    const p = block[qi], clone = p.cloneNode(true);
    clone.querySelector('strong').remove();
    const rest = clone.innerHTML.replace(/^\s*(<br\s*\/?>)?\s*:?\s*/i, '').trim();
    if (rest.replace(/<[^>]+>/g, '').trim()) question = rest;
    else if (block[qi + 1] && block[qi + 1].tagName !== 'H4') { question = block[qi + 1].innerHTML; block[qi + 1].remove(); }
    p.remove();
  }
  spend?.remove();
  const h4i = block.findIndex(n => n.tagName === 'H4');
  const rubricNodes = h4i >= 0 ? block.slice(h4i).filter(n => n.isConnected) : [];
  const card = document.createElement('div');
  card.className = 'iv';
  const R = 26, CIRC = 2 * Math.PI * R;
  card.innerHTML = `
    <div class="iv-head">
      <span class="iv-icon" aria-hidden="true">🎤</span>
      <div class="iv-titles"><p class="iv-kicker">Mock interview · ${minutes} minutes</p></div>
      <div class="iv-timer" data-state="idle">
        <svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="${R}" class="iv-ring-bg"/><circle cx="32" cy="32" r="${R}" class="iv-ring" style="stroke-dasharray:${CIRC};stroke-dashoffset:0"/></svg>
        <span class="iv-clock">${minutes}:00</span>
        <button type="button" class="iv-timer-btn">Start timer</button>
      </div>
    </div>
    ${question ? `<blockquote class="iv-q">${question}</blockquote>` : ''}
    <div class="iv-step">
      <p class="iv-step-label"><b>1</b> Say your answer out loud, then write down the points you made</p>
      <textarea class="iv-draft" rows="5" placeholder="e.g. Cosine ignores magnitude, so a heavy user and a light user with the same taste still match…"></textarea>
      <span class="iv-saved" aria-live="polite"></span>
    </div>
    <div class="iv-step">
      <p class="iv-step-label"><b>2</b> Grade yourself against the Strong Hire rubric</p>
      <button type="button" class="btn-mod iv-reveal">Reveal the rubric</button>
      <div class="iv-rubric" hidden></div>
      <div class="iv-score" hidden></div>
    </div>`;
  h3.before(card);
  stripEmoji(h3);
  $('.iv-titles', card).append(h3);
  const rubric = $('.iv-rubric', card);
  rubric.append(...rubricNodes);
  const points = $$(':scope > ol > li, :scope > ul > li', rubric);
  points.forEach((li, i) => li.insertAdjacentHTML('beforeend', `<button type="button" class="rub-check" data-i="${i}" aria-pressed="false"><svg viewBox="0 0 24 24">${CHECK_PATH}</svg>I covered this</button>`));

  const state = () => ({ draft: '', revealed: false, covered: [], ...(docRec(key).iv || {}) });
  const save = patch => docSave(key, { iv: { ...state(), ...patch } });
  const draft = $('.iv-draft', card);
  draft.value = state().draft;
  let t;
  draft.addEventListener('input', () => {
    clearTimeout(t);
    $('.iv-saved', card).textContent = '';
    t = setTimeout(() => { save({ draft: draft.value }); $('.iv-saved', card).textContent = 'Saved'; }, 600);
  });

  const paint = () => {
    const st = state();
    rubric.hidden = !st.revealed;
    $('.iv-reveal', card).hidden = st.revealed;
    points.forEach((li, i) => { const on = st.covered.includes(i); li.classList.toggle('is-covered', on); $('.rub-check', li).setAttribute('aria-pressed', on); });
    const score = $('.iv-score', card);
    score.hidden = !st.revealed || !points.length;
    if (!score.hidden) {
      const n = st.covered.length, pct = n / points.length;
      const verdict = pct === 1 ? ['Strong hire', 'ok'] : pct >= .6 ? ['Hire, with gaps to close', ''] : ['Not there yet: rehearse and retry', 'err'];
      score.innerHTML = `<div class="iv-meter"><i style="width:${pct * 100}%"></i></div><p><b class="${verdict[1]}">${verdict[0]}</b> · you covered ${n} of ${points.length} points</p>`;
    }
  };
  card.addEventListener('click', e => {
    if (e.target.closest('.iv-reveal')) {
      if (!draft.value.trim()) toast('Tip: write your answer first. The rubric sticks better when you have something to compare.');
      save({ revealed: true }); paint(); return;
    }
    const rc = e.target.closest('.rub-check');
    if (rc) {
      const i = +rc.dataset.i, cov = state().covered;
      save({ covered: cov.includes(i) ? cov.filter(x => x !== i) : [...cov, i] }); paint(); return;
    }
    if (e.target.closest('.iv-timer-btn')) toggleTimer();
  });

  let left = minutes * 60, timer = null;
  const timerEl = $('.iv-timer', card);
  const paintTimer = () => {
    $('.iv-clock', card).textContent = `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
    $('.iv-ring', card).style.strokeDashoffset = CIRC * (1 - left / (minutes * 60));
  };
  function toggleTimer() {
    const btn = $('.iv-timer-btn', card);
    if (timer) { clearInterval(timer); timer = null; timerEl.dataset.state = 'paused'; btn.textContent = 'Resume'; return; }
    if (left <= 0) { left = minutes * 60; paintTimer(); }
    timerEl.dataset.state = 'running';
    btn.textContent = 'Pause';
    timer = setInterval(() => {
      if (!card.isConnected) { clearInterval(timer); return; }
      left--; paintTimer();
      if (left <= 0) {
        clearInterval(timer); timer = null;
        timerEl.dataset.state = 'done'; btn.textContent = 'Restart';
        toast('Time is up. Compare your answer with the rubric.', 'warn');
      }
    }, 1000);
  }
  paint();
}

function upgradeEndOfDay(prose) {
  $$('p', prose).forEach(p => {
    const strong = p.querySelector('strong');
    if (!strong || p.firstElementChild !== strong || !/^task for the end of the day/i.test(strong.textContent)) return;
    const card = document.createElement('div');
    card.className = 'eod';
    strong.remove();
    card.innerHTML = `<span class="eod-flag" aria-hidden="true">🏁</span><div class="eod-body"><p class="eod-kicker">Before you finish today</p><p class="eod-text">${p.innerHTML.replace(/^\s*:?\s*/, '')}</p></div><button type="button" class="btn-mod" data-act="complete">Mark day complete</button>`;
    p.replaceWith(card);
  });
}

/* ============================================================ glossary == */
let glossaryLoad = null;
function loadGlossary() {
  glossaryLoad ??= (async () => {
    const ck = `doc:roadmap:${GLOSSARY_ID}`;
    let doc = docCache.get(ck);
    if (!doc) { doc = await api(`/api/roadmap-doc?id=${GLOSSARY_ID}`); docCache.set(ck, doc); }
    if (!doc.exists) return [];
    const terms = [];
    let cat = '';
    const lines = doc.markdown.split('\n');
    lines.forEach((line, i) => {
      if (/^##\s/.test(line)) cat = line.replace(/^#+\s*/, '').replace(/^[\p{Extended_Pictographic}️\s]+/u, '').replace(/\(added[^)]*\)/i, '').trim();
      const m = line.match(/^\s*-\s+((?:\$[^$]+\$(?:\s*(?:or|,)\s*)?)+\s*:\s*)?\*\*(.+?)\*\*\s*:?\s*(.*)$/);
      if (!m) return;
      let def = m[3].trim();
      if (!def) {
        for (let j = i + 1; j < lines.length && /^\s{2,}-\s/.test(lines[j]); j++) def += ` ${lines[j].replace(/^\s*-\s*/, '')}`;
      }
      const name = m[2].replace(/[:.]+$/, '').replace(/^"(.*)"$/, '$1').trim();
      terms.push({ name, cat, def: def.trim(), symbol: (m[1] || '').replace(/\s*:\s*$/, '').trim() });
    });
    return terms;
  })().catch(() => { glossaryLoad = null; return []; });
  return glossaryLoad;
}

const COMMON_WORDS = new Set(['training', 'inference', 'linear', 'batch', 'iteration', 'bias', 'loss', 'evidence', 'prior', 'parameter', 'vector',
  'matrix', 'scalar', 'tensor', 'model', 'layer', 'token', 'attention', 'embedding', 'sampling', 'likelihood', 'gradient', 'epoch', 'mean', 'variance']);

async function linkGlossaryTerms(prose) {
  const terms = await loadGlossary();
  if (!terms.length || !prose.isConnected) return;
  const alias = new Map();
  terms.forEach(t => {
    const parts = t.name.split(/\s+vs\.?\s+|\s*\/\s*/i);
    parts.forEach(part => {
      const main = part.replace(/\s*\(.*\)\s*/, '').replace(/^the\s+/i, '').trim();
      const inner = (part.match(/\(([^)]+)\)/) || [])[1];
      [main, inner && inner.replace(/^the\s+/i, '')].filter(Boolean).forEach(a => {
        if (a.length >= 3 && !/[$\\]/.test(a) && !alias.has(a.toLowerCase())) alias.set(a.toLowerCase(), { a, t });
      });
    });
  });
  const keys = [...alias.keys()].sort((x, y) => y.length - x.length).map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (!keys.length) return;
  const re = new RegExp(`(?<![\\w-])(${keys.join('|')})(?![\\w-])`, 'gi');
  const used = new Set();
  let links = 0;
  const walker = document.createTreeWalker(prose, NodeFilter.SHOW_TEXT, {
    acceptNode: n => n.parentElement.closest('pre, code, .katex, a, h1, h2, h3, h4, button, textarea, .callout-label, .lab, mark, .term, .iv-rubric, .hour-track, .tk-title')
      ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
  });
  const nodes = [];
  for (let n = walker.nextNode(); n; n = walker.nextNode()) nodes.push(n);
  for (const node of nodes) {
    if (links >= 60) break;
    const text = node.data;
    re.lastIndex = 0;
    const hits = [];
    let m;
    while ((m = re.exec(text))) {
      const entry = alias.get(m[1].toLowerCase());
      if (!entry || used.has(entry.t.name)) continue;
      const single = !/\s/.test(entry.a);
      if (single && COMMON_WORDS.has(entry.a.toLowerCase()) && m[1] !== entry.a) continue;
      if (single && entry.a === entry.a.toUpperCase() && m[1] !== entry.a) continue;
      used.add(entry.t.name);
      hits.push([m.index, m[1], entry.t]);
      if (++links >= 60) break;
    }
    if (!hits.length) continue;
    const frag = document.createDocumentFragment();
    let pos = 0;
    hits.forEach(([i, word, t]) => {
      frag.append(text.slice(pos, i));
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'term';
      b.textContent = word;
      b.dataset.term = t.name;
      frag.append(b);
      pos = i + word.length;
    });
    frag.append(text.slice(pos));
    node.replaceWith(frag);
  }
  wireTermPopovers(prose, terms);
}

function mathText(src) {
  return esc(src).replace(/\$([^$]+)\$/g, (_, tex) => {
    try { return window.katex ? katex.renderToString(tex.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"'), { throwOnError: false }) : tex; }
    catch (e) { return tex; }
  }).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/\*([^*]+)\*/g, '<i>$1</i>').replace(/`([^`]+)`/g, '<code>$1</code>');
}

function wireTermPopovers(prose, terms) {
  let pop = $('#termPop');
  if (!pop) {
    pop = document.createElement('div');
    pop.id = 'termPop';
    pop.className = 'term-pop';
    pop.hidden = true;
    pop.setAttribute('role', 'tooltip');
    document.body.append(pop);
    pop.addEventListener('mouseenter', () => clearTimeout(pop._hide));
    pop.addEventListener('mouseleave', () => { pop._hide = setTimeout(() => { pop.hidden = true; }, 180); });
  }
  const byName = new Map(terms.map(t => [t.name, t]));
  const show = btn => {
    const t = byName.get(btn.dataset.term);
    if (!t) return;
    clearTimeout(pop._hide);
    pop.innerHTML = `<p class="tp-cat">${esc(t.cat)}</p><p class="tp-name">${t.symbol ? `<span class="tp-sym">${mathText(t.symbol)}</span>` : ''}${esc(t.name)}</p><p class="tp-def">${mathText(t.def)}</p><a class="tp-link" href="#/roadmap/${GLOSSARY_ID}">Open the glossary</a>`;
    pop.hidden = false;
    const r = btn.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight;
    pop.style.left = `${clamp(r.left + r.width / 2 - w / 2, 10, innerWidth - w - 10)}px`;
    pop.style.top = `${r.top - h - 10 > 10 ? r.top - h - 10 : r.bottom + 10}px`;
  };
  const hide = () => { pop._hide = setTimeout(() => { pop.hidden = true; }, 180); };
  prose.addEventListener('mouseover', e => { const b = e.target.closest('.term'); if (b) show(b); });
  prose.addEventListener('mouseout', e => { if (e.target.closest('.term')) hide(); });
  prose.addEventListener('focusin', e => { const b = e.target.closest('.term'); if (b) show(b); });
  prose.addEventListener('focusout', e => { if (e.target.closest('.term')) hide(); });
  $('#viewDocReader').addEventListener('scroll', () => { pop.hidden = true; }, { passive: true });
}

/* --------------------------------------------------------- Day 0 itself -- */
function buildGlossary(host, prose, key) {
  const sections = $$('.sec', prose).filter(s => /glossary|jargon|dictionary/i.test($(':scope > h2', s)?.dataset.label || ''));
  let total = 0;
  sections.forEach(sec => {
    const cat = $(':scope > h2', sec).dataset.label.replace(/^part\s*\d+:\s*/i, '').replace(/\(added[^)]*\)/i, '').trim();
    $$(':scope > ul', sec).forEach(ul => {
      const lis = $$(':scope > li', ul);
      const cards = lis.map(li => glossaryCard(li, cat)).filter(Boolean);
      if (cards.length < Math.max(2, lis.length * .6)) return;
      const grid = document.createElement('div');
      grid.className = 'gloss-grid';
      grid.append(...cards);
      ul.replaceWith(grid);
      total += cards.length;
    });
  });
  if (!total) return;
  const bar = document.createElement('div');
  bar.className = 'gloss-bar';
  bar.innerHTML = `
    <label class="gloss-search"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      <input type="search" placeholder="Find a term or symbol…" aria-label="Filter glossary terms"></label>
    <span class="gloss-count"></span>
    <button type="button" class="btn-mod" data-gloss="flash">Flashcards</button>
    <button type="button" class="btn-mod ghost" data-gloss="quiz">Quiz me</button>`;
  sections[0].before(bar);

  const input = $('input', bar);
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    $$('.gloss-card', prose).forEach(c => { c.hidden = !!q && !c.dataset.search.includes(q); });
    $$('.gloss-grid', prose).forEach(g => {
      const any = $$('.gloss-card', g).some(c => !c.hidden);
      g.hidden = !any;
      const head = g.previousElementSibling;
      if (head && head.tagName === 'H3') head.hidden = !any;
    });
    paintGlossaryKnown(host, key);
  });
  bar.addEventListener('click', e => {
    const b = e.target.closest('[data-gloss]');
    if (b) openFlashcards(host, prose, key, b.dataset.gloss);
  });
  prose.addEventListener('click', e => {
    const b = e.target.closest('.gc-known');
    if (!b) return;
    const card = b.closest('.gloss-card'), known = docRec(key).known || [];
    docSave(key, { known: known.includes(card.dataset.slug) ? known.filter(k => k !== card.dataset.slug) : [...known, card.dataset.slug] });
    paintGlossaryKnown(host, key);
  });
  paintGlossaryKnown(host, key);
}

function glossaryCard(li, cat) {
  const nodes = [...li.childNodes];
  const si = nodes.findIndex(n => n.nodeName === 'STRONG');
  if (si < 0 || nodes.slice(0, si).some(n => n.nodeType !== 3 || n.textContent.length > 90)) return null;
  const symbol = nodes.slice(0, si).map(n => n.textContent).join('').replace(/\s*:\s*$/, '').trim();
  const term = nodes[si].textContent.trim().replace(/[:.]+$/, '').replace(/^"(.*)"$/, '$1');
  const rest = nodes.slice(si + 1);
  if (rest[0] && rest[0].nodeType === 3) rest[0].textContent = rest[0].textContent.replace(/^\s*[:.]?\s*/, '');
  const card = document.createElement('article');
  card.className = 'gloss-card';
  card.dataset.slug = slug(term);
  card.dataset.cat = cat;
  card.innerHTML = `<div class="gc-top">${symbol ? `<span class="gc-sym">${esc(symbol)}</span>` : ''}<h4 class="gc-term">${esc(term)}</h4>
    <button type="button" class="gc-known" aria-pressed="false" title="I know this one"><svg viewBox="0 0 24 24">${CHECK_PATH}</svg></button></div><div class="gc-def"></div>`;
  $('.gc-def', card).append(...rest);
  card.dataset.search = `${term} ${symbol} ${$('.gc-def', card).textContent}`.toLowerCase();
  return card;
}

function paintGlossaryKnown(host, key) {
  const known = new Set(docRec(key).known || []);
  const cards = $$('.gloss-card', host);
  cards.forEach(c => { const on = known.has(c.dataset.slug); c.classList.toggle('is-known', on); $('.gc-known', c)?.setAttribute('aria-pressed', on); });
  const shown = cards.filter(c => !c.hidden).length, count = $('.gloss-count', host);
  if (count) count.textContent = `${shown === cards.length ? `${cards.length} terms` : `${shown} of ${cards.length} terms`} · ${[...known].length} known`;
}

function openFlashcards(host, prose, key, mode) {
  const reader = $('.reader', host);
  const all = $$('.gloss-card', prose);
  const pool = all.filter(c => !c.hidden);
  if (pool.length < 4) { toast('Clear the search to practise with more terms.'); return; }
  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const known = () => new Set(docRec(key).known || []);
  let deck = shuffle(pool.filter(c => !known().has(c.dataset.slug)));
  if (deck.length < 4) deck = shuffle([...pool]);
  deck = deck.slice(0, 20);
  let i = 0, score = 0, missed = [];
  const ov = document.createElement('div');
  ov.className = 'fc-overlay';
  ov.tabIndex = -1;
  ov.setAttribute('role', 'dialog');
  ov.setAttribute('aria-modal', 'true');
  ov.setAttribute('aria-label', mode === 'quiz' ? 'Glossary quiz' : 'Glossary flashcards');
  reader.append(ov);
  const back = document.activeElement;
  const close = () => { ov.remove(); back?.focus?.(); };
  const plain = card => { const d = $('.gc-def', card).cloneNode(true); d.querySelectorAll('.katex-mathml').forEach(n => n.remove()); return d.textContent.replace(/\s+/g, ' ').trim(); };
  const markKnown = (card, yes) => {
    const k = docRec(key).known || [], s = card.dataset.slug;
    docSave(key, { known: yes ? [...new Set([...k, s])] : k.filter(x => x !== s) });
  };

  function frame(inner) {
    ov.innerHTML = `<div class="fc-backdrop" data-fc="close"></div>
      <div class="fc-panel">
        <div class="fc-top"><span class="fc-mode">${mode === 'quiz' ? 'Quiz' : 'Flashcards'}</span>
          <div class="fc-progress"><i style="width:${Math.min(100, i / deck.length * 100)}%"></i></div>
          <span class="fc-count">${Math.min(i + 1, deck.length)} / ${deck.length}</span>
          <button type="button" class="icon-btn" data-fc="close" aria-label="Close"><svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
        ${inner}
      </div>`;
  }
  function render() {
    if (i >= deck.length) return finish();
    const card = deck[i], sym = $('.gc-sym', card), term = $('.gc-term', card).textContent;
    if (mode === 'quiz') {
      const others = shuffle(all.filter(c => c !== card && c.dataset.cat === card.dataset.cat));
      const pad = shuffle(all.filter(c => c !== card && !others.includes(c)));
      const options = shuffle([card, ...[...others, ...pad].slice(0, 3)]);
      let prompt = plain(card);
      const nameRe = new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      prompt = esc(prompt).replace(nameRe, '_____');
      frame(`<div class="qz">
        <p class="qz-label">Which term matches this definition?</p>
        <p class="qz-def">${prompt.length > 360 ? `${prompt.slice(0, 357)}…` : prompt}</p>
        <div class="qz-options">${options.map(o => `<button type="button" class="qz-opt" data-right="${o === card}">${esc($('.gc-term', o).textContent)}</button>`).join('')}</div>
        <div class="fc-actions"><span class="qz-score">Score ${score}</span><button type="button" class="btn-mod" data-fc="next" hidden>Next</button></div>
      </div>`);
    } else {
      frame(`<div class="fc-stage"><button type="button" class="fc-card" data-fc="flip" aria-label="Flip card">
          <span class="fc-face fc-front">${sym ? `<span class="fc-sym">${sym.innerHTML}</span><span class="fc-ask">What does this symbol mean?</span>` : `<span class="fc-term">${esc(term)}</span><span class="fc-ask">Explain it in your own words, then flip</span>`}</span>
          <span class="fc-face fc-back"><span class="fc-back-term">${esc(term)}</span><span class="fc-back-def">${$('.gc-def', card).innerHTML}</span></span>
        </button></div>
        <div class="fc-actions">
          <button type="button" class="btn-mod ghost" data-fc="learning">← Still learning</button>
          <span class="fc-hint">Space to flip</span>
          <button type="button" class="btn-mod" data-fc="know">I know it →</button>
        </div>`);
    }
    ov.focus();
  }
  function finish() {
    frame(`<div class="fc-done">
      <svg class="done-check" viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="23"/><path d="M15 27l7 7 15-16"/></svg>
      <h3>${mode === 'quiz' ? `${score} of ${deck.length} correct` : `${deck.length - missed.length} of ${deck.length} known`}</h3>
      <p>${missed.length ? `${missed.length} term${missed.length > 1 ? 's' : ''} to review. Known terms are ticked on the page and skipped next time.` : 'A clean run. Every term in this round is marked as known.'}</p>
      <div class="fc-actions">${missed.length ? '<button type="button" class="btn-mod" data-fc="again">Practise the missed ones</button>' : ''}<button type="button" class="btn-mod ghost" data-fc="close">Close</button></div>
    </div>`);
    $('.fc-panel', ov).classList.add('just-done');
    paintGlossaryKnown(host, key);
  }
  ov.addEventListener('click', e => {
    const b = e.target.closest('[data-fc], .qz-opt');
    if (!b) return;
    if (b.classList.contains('qz-opt')) {
      if ($('.qz-opt[disabled]', ov)) return;
      const right = b.dataset.right === 'true';
      $$('.qz-opt', ov).forEach(o => { o.disabled = true; if (o.dataset.right === 'true') o.classList.add('is-right'); });
      if (!right) { b.classList.add('is-wrong'); missed.push(deck[i]); } else { score++; markKnown(deck[i], true); }
      $('.qz-score', ov).textContent = `Score ${score}`;
      $('[data-fc="next"]', ov).hidden = false;
      $('[data-fc="next"]', ov).focus();
      return;
    }
    const act = b.dataset.fc;
    if (act === 'close') close();
    else if (act === 'flip') $('.fc-card', ov).classList.toggle('is-flipped');
    else if (act === 'know') { markKnown(deck[i], true); i++; render(); }
    else if (act === 'learning') { markKnown(deck[i], false); missed.push(deck[i]); i++; render(); }
    else if (act === 'next') { i++; render(); }
    else if (act === 'again') { deck = shuffle(missed); missed = []; i = 0; score = 0; render(); }
  });
  ov.addEventListener('keydown', e => {
    e.stopPropagation();
    if (e.key === 'Escape') { close(); return; }
    if (mode === 'quiz') { if (e.key === 'Enter' && !$('[data-fc="next"]', ov)?.hidden) { i++; render(); } return; }
    if (e.key === ' ') { e.preventDefault(); $('.fc-card', ov)?.classList.toggle('is-flipped'); }
    else if (e.key === 'ArrowRight' && $('[data-fc="know"]', ov)) $('[data-fc="know"]', ov).click();
    else if (e.key === 'ArrowLeft' && $('[data-fc="learning"]', ov)) $('[data-fc="learning"]', ov).click();
  });
  render();
}
