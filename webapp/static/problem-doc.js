/* ============================================================================
   Problem documents — the Question and Solution tabs.

   The files on disk are plain-text docstrings with ASCII rules, which used to
   be dumped into a <pre>. They are strictly structured, though, so they can be
   read properly instead:

     ====================                 banner: LeetCode N · Title  [Diff]
     PROBLEM / EXAMPLES / CONSTRAINTS     dash-underlined section headers
     ====  MAJOR SECTION  ====            banner-wrapped deep-dive headers
     Example 1:  Input/Output/Explan.     example blocks
         indented text                    code, traces and ASCII diagrams
     Time: O(n) / Space: O(1)             complexity lines

   Everything that is really prose becomes prose; everything that is really a
   grid, a trace or code keeps its monospace alignment. Nothing is dropped —
   unrecognised lines fall through as paragraphs or preformatted blocks.

   Uses app.js globals (esc, $, $$) and reader.js (ensureHljs, highlightCode).
   ========================================================================= */
'use strict';

/* ------------------------------------------------------------------ inline -- */
const PD_ARROWS = [[/-->/g, '→'], [/->/g, '→'], [/<=>/g, '⇔'], [/<-/g, '←']];

function pdInline(s, { arrows = true } = {}) {
  let out = esc(s);
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
  out = out.replace(/(https?:\/\/[^\s<)]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  out = out.replace(/\bO\(([^)]{1,24})\)/g, '<span class="pd-o">O($1)</span>');
  if (arrows) PD_ARROWS.forEach(([re, ch]) => { out = out.replace(re, ch); });
  return out;
}

const PD_HEAD_RE = /^(?:(QUESTION|SOLUTION)\s*[·|-]\s*)?LeetCode\s+(\d+)\s*[·|-]\s*(.+?)\s*(?:\[(Easy|Medium|Hard)\])?\s*$/i;
const pdRule = l => /^={6,}$/.test(l.trim());
const pdUnderline = l => /^[-=]{3,}$/.test(l.trim());
const pdCaps = l => /^[A-Z][A-Z0-9 ()/&,'.:\-]{3,}$/.test(l.trim()) && /[A-Z]{3}/.test(l);
const pdIndent = l => /^\s{4,}\S/.test(l);
const pdBlank = l => !l.trim();

/* --------------------------------------------------------------- the parser -- */
function pdParse(text) {
  const lines = String(text || '').replace(/\r/g, '').split('\n');
  // python docstring fences, if the server handed them through
  while (lines.length && /^\s*("""|''')\s*$/.test(lines[0])) lines.shift();
  while (lines.length && /^\s*("""|''')\s*$/.test(lines[lines.length - 1])) lines.pop();

  const meta = {};
  const blocks = [];
  let i = 0;

  /* the opening banner carries the identity of the problem */
  if (pdRule(lines[i] || '')) {
    const close = lines.findIndex((l, k) => k > i && pdRule(l));
    if (close > i && close - i <= 8) {
      for (let k = i + 1; k < close; k++) {
        const l = lines[k].trim();
        const m = l.match(PD_HEAD_RE);
        if (m) { meta.kind = (m[1] || '').toUpperCase(); meta.lc = m[2]; meta.title = m[3]; meta.diff = m[4] || ''; continue; }
        if (/^https?:\/\//.test(l)) { meta.url = l; continue; }
        const t = l.match(/^Topic:\s*(.+)$/i);
        if (t) { meta.topic = t[1]; continue; }
        if (l) (meta.extra ??= []).push(l);
      }
      i = close + 1;
    }
  }

  const push = b => { if (b) blocks.push(b); };
  const takeIndented = () => {
    const buf = [];
    while (i < lines.length && (pdIndent(lines[i]) || (pdBlank(lines[i]) && pdIndent(lines[i + 1] || '')))) buf.push(lines[i++]);
    while (buf.length && pdBlank(buf[buf.length - 1])) buf.pop();
    return buf;
  };

  while (i < lines.length) {
    const line = lines[i];

    if (pdBlank(line)) { i++; continue; }

    /* ==== MAJOR SECTION ====  (rule, title, rule) */
    if (pdRule(line) && lines[i + 1] && !pdRule(lines[i + 1]) && pdRule(lines[i + 2] || '')) {
      push({ type: 'major', text: lines[i + 1].trim() });
      i += 3;
      continue;
    }
    if (pdRule(line)) { i++; continue; }              // stray rule: it was decoration

    /* SECTION HEADER over a dashed underline */
    if (lines[i + 1] !== undefined && pdUnderline(lines[i + 1]) && line.trim() && !pdIndent(line)) {
      push({ type: 'section', text: line.trim() });
      i += 2;
      continue;
    }

    /* Example 1:  … */
    const ex = line.match(/^\s*Example\s+(\d+)\s*:?\s*(.*)$/i);
    if (ex && !pdIndent(line)) {
      i++;
      const body = [];
      if (ex[2].trim()) body.push('    ' + ex[2].trim());
      body.push(...takeIndented());
      push({ type: 'example', n: ex[1], body });
      continue;
    }

    /* an indented run: code, a trace, or an ASCII diagram */
    if (pdIndent(line)) {
      const buf = takeIndented();
      const flat = buf.map(l => l.replace(/^\s{4}/, ''));
      const complexity = flat.filter(l => /^\s*(Time|Space)\s*[:=]/i.test(l));
      if (complexity.length && complexity.length === flat.filter(l => l.trim()).length) {
        push({ type: 'complexity', items: complexity.map(l => l.trim()) });
      } else {
        push({ type: 'pre', lines: flat, complexity: complexity.map(l => l.trim()) });
      }
      continue;
    }

    /* an all-caps line on its own is a label (STEP BY STEP …) */
    if (pdCaps(line) && !pdUnderline(lines[i + 1] || '')) {
      push({ type: 'label', text: line.trim() });
      i++;
      continue;
    }

    /* otherwise: a paragraph, up to the next blank line or structural line */
    const para = [];
    while (i < lines.length && !pdBlank(lines[i]) && !pdIndent(lines[i]) && !pdRule(lines[i])
           && !(lines[i + 1] !== undefined && pdUnderline(lines[i + 1]))
           && !/^\s*Example\s+\d+\s*:/i.test(lines[i])) {
      para.push(lines[i++]);
    }
    if (para.length) push({ type: 'para', text: para.join(' ').trim() });
    else i++;
  }
  return { meta, blocks };
}

/* ------------------------------------------------------------------ render -- */
const PD_SECTION_ICON = {
  PROBLEM: 'M12 3l8 4.5v9L12 21l-8-4.5v-9z',
  EXAMPLES: 'M4 5h16M4 12h16M4 19h10',
  CONSTRAINTS: 'M5 12h14M7 7h10M7 17h10',
  'FOLLOW UP': 'M5 12h14M13 6l6 6-6 6',
};

function pdExample(b) {
  const rows = [];
  const art = [];
  let cur = null;
  b.body.forEach(raw => {
    const l = raw.replace(/^\s{4}/, '');
    const m = l.match(/^\s*(Input|Output|Explanation)\s*:\s*(.*)$/i);
    if (m) {
      cur = { label: m[1], lines: m[2].trim() ? [m[2].trim()] : [] };
      rows.push(cur);
    } else if (cur && (pdIndent(raw) || raw.trim())) {
      // an Output is a single value; diagrams that follow it are their own block
      if (cur.label.toLowerCase() === 'output' && cur.lines.length) art.push(l);
      else cur.lines.push(l);
    } else if (raw.trim()) {
      art.push(l);
    }
  });
  if (!rows.length) return `<div class="pd-example"><pre>${esc(b.body.join('\n'))}</pre></div>`;

  const row = r => {
    const multi = r.lines.length > 1;
    const val = multi
      ? `<pre>${esc(r.lines.join('\n').replace(/^\s+$/gm, ''))}</pre>`
      : `<code>${esc(r.lines[0] || '')}</code>`;
    return `<div class="pd-ex-row is-${r.label.toLowerCase()}${multi ? ' is-multi' : ''}">
      <span class="pd-ex-label">${r.label}</span>${val}</div>`;
  };
  return `<figure class="pd-example">
    <figcaption>Example ${b.n}</figcaption>
    ${rows.map(row).join('')}
    ${art.length ? `<pre class="pd-art">${esc(art.join('\n'))}</pre>` : ''}
  </figure>`;
}

function pdConstraints(b) {
  const items = b.lines.filter(l => l.trim());
  return `<ul class="pd-chips">${items.map(l => `<li>${pdInline(l.trim(), { arrows: false })}</li>`).join('')}</ul>`;
}

/* An indented run in these files is one of three things: code, an aligned
   trace/diagram, or a plain sentence that happened to be indented. Only the
   first two need a monospace card. */
function pdIsProse(lines) {
  const real = lines.filter(l => l.trim());
  if (!real.length) return false;
  if (real.some(l => /\s{3,}\S/.test(l.trim()))) return false;     // aligned columns
  if (real.some(l => /(^|\s)(def |class |return |import |for |while )/.test(l))) return false;
  const wordy = real.filter(l => l.trim().split(/\s+/).length >= 4 && /[a-z]{3}/.test(l)).length;
  return wordy / real.length >= 0.7;
}

/* A walked-through trace lines its columns up with runs of spaces; source code
   does not. That, not the presence of an "=", is what separates them. */
function pdIsTrace(lines) {
  const real = lines.filter(l => l.trim());
  if (!real.length) return false;
  const aligned = real.filter(l => /\S\s{3,}\S/.test(l)).length;
  return aligned / real.length >= 0.3;
}

function pdPre(b) {
  if (pdIsProse(b.lines)) {
    return `<p class="pd-p pd-inset">${pdInline(b.lines.map(l => l.trim()).filter(Boolean).join(' '))}</p>`;
  }
  // complexity lines are lifted into badges, so do not repeat them in the card
  let lines = b.complexity.length
    ? b.lines.filter(l => !/^\s*(Time|Space)\s*[:=]/i.test(l))
    : b.lines;
  while (lines.length && !lines[lines.length - 1].trim()) lines = lines.slice(0, -1);
  if (!lines.length) return '';
  const body = lines.join('\n').replace(/\s+$/, '');
  const isCode = !pdIsTrace(lines)
    && /(^|\n)\s*(def |class |return |import |from |for |while |if |elif |else:|print\()/.test(body);
  return `<div class="code pd-pre${isCode ? '' : ' is-plain'}">
    <div class="code-head"><span class="code-lang">${isCode ? 'Python' : 'Trace'}</span>
      <button type="button" class="code-copy">Copy</button></div>
    <pre><code class="${isCode ? 'language-python' : ''}">${esc(body)}</code></pre>
  </div>`;
}

const pdComplexity = items => `<div class="pd-cx">${items.map(t => {
  const m = t.match(/^(Time|Space)\s*[:=]\s*(.+)$/i);
  if (!m) return `<span class="pd-cx-item">${pdInline(t)}</span>`;
  return `<span class="pd-cx-item is-${m[1].toLowerCase()}"><b>${m[1]}</b>${pdInline(m[2])}</span>`;
}).join('')}</div>`;

function renderProblemDoc(text, tab) {
  const { meta, blocks } = pdParse(text);
  if (!meta.kind) meta.kind = tab === 'solution' ? 'SOLUTION' : 'QUESTION';
  let html = '';
  let approach = 0;
  let section = '';

  blocks.forEach((b, k) => {
    switch (b.type) {
      case 'major': {
        const isApproach = /^APPROACH\b/i.test(b.text);
        if (isApproach) approach++;
        section = b.text.toUpperCase();
        html += `<h2 class="pd-h2${isApproach ? ' is-approach' : ''}" id="pd-${k}">
          ${isApproach ? `<span class="pd-h2-badge">${approach}</span>` : ''}
          <span>${pdInline(b.text.replace(/^APPROACH\s*\d+\s*[·.-]?\s*/i, ''))}</span>
        </h2>`;
        break;
      }
      case 'section': {
        section = b.text.toUpperCase();
        const d = PD_SECTION_ICON[section];
        html += `<h3 class="pd-h3" id="pd-${k}">
          ${d ? `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg>` : ''}
          <span>${pdInline(b.text)}</span></h3>`;
        break;
      }
      case 'label':
        html += `<p class="pd-label">${pdInline(b.text)}</p>`;
        break;
      case 'para': {
        const warn = /^(⚠️|WARNING|NOTE|CAUTION|Precision note)/i.test(b.text.trim());
        html += warn
          ? `<p class="pd-note">${pdInline(b.text)}</p>`
          : `<p class="pd-p">${pdInline(b.text)}</p>`;
        break;
      }
      case 'example':
        html += pdExample(b);
        break;
      case 'complexity':
        html += pdComplexity(b.items);
        break;
      case 'pre':
        html += section === 'CONSTRAINTS' ? pdConstraints(b) : pdPre(b);
        if (b.complexity.length && section !== 'CONSTRAINTS') html += pdComplexity(b.complexity);
        break;
    }
  });

  const kind = meta.kind === 'SOLUTION' ? 'solution' : 'question';
  return `<article class="pd pd-${kind}">
    <div class="pd-strip">
      <span class="pd-kind">${kind === 'solution' ? 'Reference solution' : 'Problem statement'}</span>
      ${meta.lc ? `<span class="pd-topic">LeetCode ${esc(meta.lc)}</span>` : ''}
    </div>
    ${html}
  </article>`;
}

/* things that need the DOM: syntax highlighting and the copy buttons */
function enhanceProblemDoc(root) {
  const blocks = $$('.pd-pre code.language-python', root);
  if (blocks.length && typeof ensureHljs === 'function') {
    ensureHljs().then(ok => { if (ok) blocks.forEach(c => highlightCode(c, 'python')); });
  }
  if (root.dataset.pdWired) return;
  root.dataset.pdWired = '1';
  root.addEventListener('click', e => {
    const btn = e.target.closest('.pd .code-copy');
    if (!btn) return;
    const code = btn.closest('.code')?.querySelector('code');
    if (!code) return;
    navigator.clipboard?.writeText(code.textContent).then(() => {
      btn.textContent = 'Copied';
      btn.classList.add('is-done');
      setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('is-done'); }, 1400);
    }).catch(() => { btn.textContent = 'Press ⌘C'; });
  });
}
