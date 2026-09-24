/* ============================================================================
   Visualizations for 25_design — every problem here is a stateful class, so
   each spec takes an operation-sequence input (comma-separated ops) and shows
   the real internal data structure changing across calls, per the actual
   PyDSA/25_design/0NN_..._solution.py "✅ the answer" class — not a generic
   textbook implementation.
   ========================================================================= */
'use strict';

/* ---------------------------------------------------------- shared: a small
   doubly-linked-chain renderer (dummy head + dummy tail), reused by Design
   Linked List and LFU Cache's per-frequency lists. ------------------------ */
function dllChainHTML(items, { label = v => v, cls = () => '', headTag = 'HEAD', tailTag = 'TAIL' } = {}) {
  let html = `
  <div class="array-node merged" style="flex-direction:column; background:var(--bg-surface); padding:8px; border-radius:8px; margin-right:16px;">
      <div style="font-size:11px; font-weight:bold; color:var(--text-bright);">${headTag}</div>
  </div>`;
  if (!items.length) {
    html += `<div style="color:var(--text-dim); padding:14px; font-style:italic;">(empty)</div>`;
  } else {
    html += items.map(it => `
      <div class="array-node ${cls(it)}" style="flex-direction:column; margin-right:16px; border-radius:8px; padding:8px; min-width:54px;">
          ${label(it)}
      </div>`).join('');
  }
  html += `
  <div class="array-node merged" style="flex-direction:column; background:var(--bg-surface); padding:8px; border-radius:8px; margin-left:2px;">
      <div style="font-size:11px; font-weight:bold; color:var(--text-bright);">${tailTag}</div>
  </div>`;
  return html;
}

/* ------------------------------------------------------ shared: op parser - */
function opsParse(s, { max = 12 } = {}) {
  const ops = String(s || '').split(',').map(x => x.trim()).filter(Boolean);
  if (!ops.length) throw new Error('Enter at least one operation');
  if (ops.length > max) throw new Error(`Use at most ${max} operations`);
  return ops;
}

/* ============================================================= 25 · Design HashSet == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design HashSet', short: 'HashSet',
  idea: 'Separate chaining: a fixed array of buckets, each a small list. A key always lives in bucket key % NUM_BUCKETS — add/remove/contains all just scan that one bucket.',
  complexity: 'add/remove/contains O(1) average (bucket length) · Space O(n + buckets)',
  input: 'add 3, add 8, add 5, contains 3, remove 8, contains 8', hint: 'ops: add k | remove k | contains k (buckets = 5 for this demo, real code uses 769)',
  code: [
    'NUM_BUCKETS = 5',
    'buckets = [[] for _ in range(NUM_BUCKETS)]',
    '',
    'def add(key):',
    '    b = buckets[key % NUM_BUCKETS]',
    '    if key not in b: b.append(key)',
    '',
    'def remove(key):',
    '    b = buckets[key % NUM_BUCKETS]',
    '    if key in b: b.remove(key)',
    '',
    'def contains(key):',
    '    return key in buckets[key % NUM_BUCKETS]',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (['add', 'remove', 'contains'].includes(t[0]) && t.length === 2 && /^\d+$/.test(t[1])) return { op: t[0], key: +t[1] };
      throw new Error(`"${op}" — use "add k", "remove k" or "contains k"`);
    }) };
  },
  buildStates({ ops }) {
    const N = 5;
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const buckets = Array.from({ length: N }, () => []);
    const snap = () => buckets.map(b => [...b]);
    domPushState(seq, { line: 2, color: 'default', buckets: snap(), active: -1, op: null, result: null,
      explTitle: 'Start', explText: `${N} empty buckets (a small illustrative count — the real solution uses 769).`, pause: true }, ctx);
    ops.forEach(o => {
      const b = o.key % N;
      if (o.op === 'add') {
        const had = buckets[b].includes(o.key);
        if (!had) buckets[b].push(o.key);
        domPushState(seq, { line: 5, color: 'blue', buckets: snap(), active: b, op: `add(${o.key})`, result: null,
          explTitle: `Bucket ${b} = ${o.key} % ${N}`, explText: had ? `${o.key} already in bucket ${b} — no-op.` : `Appended ${o.key} to bucket ${b}.` }, ctx);
      } else if (o.op === 'remove') {
        const had = buckets[b].includes(o.key);
        buckets[b] = buckets[b].filter(k => k !== o.key);
        domPushState(seq, { line: 9, color: 'rose', buckets: snap(), active: b, op: `remove(${o.key})`, result: null,
          explTitle: `Bucket ${b} = ${o.key} % ${N}`, explText: had ? `Removed ${o.key} from bucket ${b}.` : `${o.key} was not present — no-op.` }, ctx);
      } else {
        const found = buckets[b].includes(o.key);
        domPushState(seq, { line: 12, color: found ? 'emerald' : 'amber', buckets: snap(), active: b, op: `contains(${o.key})`, result: found,
          explTitle: 'Scan one bucket', explText: `Bucket ${b} ${found ? 'contains' : 'does not contain'} ${o.key} → ${found}.`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const rows = s.buckets.map((b, i) => `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px; padding:6px; border-radius:6px; ${i === s.active ? 'background:var(--bg-surface); border:1px solid var(--accent);' : ''}">
          <div style="width:70px; font-weight:bold; color:var(--text-dim);">bucket ${i}</div>
          ${chipRow(b, { cls: k => k === (s.op && +s.op.match(/\d+/)?.[0]) && i === s.active ? 'active-1' : '' })}
      </div>`).join('');
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:${s.result ? 'var(--emerald)' : 'var(--red)'};">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('buckets (key % 5)', rows)
    );
  }
});

/* ============================================================= 25 · Design HashMap == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design HashMap', short: 'HashMap',
  idea: 'Same separate-chaining idea as HashSet, but each bucket holds [key, value] pairs. put scans the bucket for an existing key first (update in place), else appends.',
  complexity: 'put/get/remove O(1) average · Space O(n + buckets)',
  input: 'put 1 10, put 6 60, put 2 20, get 1, put 1 99, get 1, remove 6, get 6', hint: 'ops: put k v | get k | remove k (buckets = 5 for this demo)',
  code: [
    'NUM_BUCKETS = 5',
    'buckets = [[] for _ in range(NUM_BUCKETS)]',
    '',
    'def put(key, value):',
    '    b = buckets[key % NUM_BUCKETS]',
    '    for pair in b:',
    '        if pair[0] == key: pair[1] = value; return',
    '    b.append([key, value])',
    '',
    'def get(key):',
    '    for k, v in buckets[key % NUM_BUCKETS]:',
    '        if k == key: return v',
    '    return -1',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'put' && t.length === 3) return { op: 'put', key: +t[1], val: +t[2] };
      if ((t[0] === 'get' || t[0] === 'remove') && t.length === 2) return { op: t[0], key: +t[1] };
      throw new Error(`"${op}" — use "put k v", "get k" or "remove k"`);
    }) };
  },
  buildStates({ ops }) {
    const N = 5;
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const buckets = Array.from({ length: N }, () => []);
    const snap = () => buckets.map(b => b.map(p => [...p]));
    domPushState(seq, { line: 2, color: 'default', buckets: snap(), active: -1, op: null, result: null,
      explTitle: 'Start', explText: `${N} empty buckets of [key, value] pairs.`, pause: true }, ctx);
    ops.forEach(o => {
      const b = o.key % N;
      if (o.op === 'put') {
        const pair = buckets[b].find(p => p[0] === o.key);
        if (pair) pair[1] = o.val; else buckets[b].push([o.key, o.val]);
        domPushState(seq, { line: 7, color: 'blue', buckets: snap(), active: b, op: `put(${o.key}, ${o.val})`, result: null,
          explTitle: `Bucket ${b}`, explText: pair ? `Key ${o.key} already there — updated its value to ${o.val}.` : `Key ${o.key} not found — appended [${o.key}, ${o.val}].` }, ctx);
      } else if (o.op === 'get') {
        const pair = buckets[b].find(p => p[0] === o.key);
        domPushState(seq, { line: 11, color: pair ? 'emerald' : 'amber', buckets: snap(), active: b, op: `get(${o.key})`, result: pair ? pair[1] : -1,
          explTitle: 'Scan one bucket', explText: pair ? `Found [${o.key}, ${pair[1]}] → ${pair[1]}.` : `${o.key} not in bucket ${b} → -1.`, pause: true }, ctx);
      } else {
        buckets[b] = buckets[b].filter(p => p[0] !== o.key);
        domPushState(seq, { line: 2, color: 'rose', buckets: snap(), active: b, op: `remove(${o.key})`, result: null,
          explTitle: `Bucket ${b}`, explText: `Removed any [${o.key}, _] pair from bucket ${b}.` }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const rows = s.buckets.map((b, i) => `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px; padding:6px; border-radius:6px; ${i === s.active ? 'background:var(--bg-surface); border:1px solid var(--accent);' : ''}">
          <div style="width:70px; font-weight:bold; color:var(--text-dim);">bucket ${i}</div>
          ${chipRow(b.map(p => `${p[0]}:${p[1]}`))}
      </div>`).join('');
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('buckets of [key,value]', rows)
    );
  }
});

/* ========================================================= 25 · Logger Rate Limiter == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Logger Rate Limiter', short: 'Logger',
  idea: 'One dict entry per distinct message: next_allowed[msg]. A message may print only once every 10 seconds — check the timestamp against that message\'s next-allowed time, then push it forward by 10.',
  complexity: 'shouldPrintMessage O(1) average · Space O(distinct messages)',
  input: 'log 1 foo, log 2 bar, log 3 foo, log 8 bar, log 11 foo', hint: 'ops: log timestamp message',
  code: [
    'next_allowed = {}',
    '',
    'def shouldPrintMessage(timestamp, message):',
    '    if timestamp < next_allowed.get(message, timestamp):',
    '        return False',
    '    next_allowed[message] = timestamp + 10',
    '    return True',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'log' && t.length === 3 && /^\d+$/.test(t[1])) return { t: +t[1], msg: t[2] };
      throw new Error(`"${op}" — use "log timestamp message"`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const nextAllowed = new Map();
    domPushState(seq, { line: 0, color: 'default', next: new Map(), msg: null, result: null,
      explTitle: 'Start', explText: 'No messages printed yet.', pause: true }, ctx);
    ops.forEach(o => {
      const had = nextAllowed.has(o.msg) ? nextAllowed.get(o.msg) : o.t;
      const allowed = o.t >= had;
      domPushState(seq, { line: 4, color: 'blue', next: new Map(nextAllowed), msg: o.msg, at: o.t, cmp: had, result: null,
        explTitle: `shouldPrintMessage(${o.t}, "${o.msg}")`, explText: `Compare ${o.t} against next_allowed["${o.msg}"] = ${nextAllowed.has(o.msg) ? had : '(none yet, so allowed)'}` }, ctx);
      if (allowed) nextAllowed.set(o.msg, o.t + 10);
      domPushState(seq, { line: allowed ? 6 : 4, color: allowed ? 'emerald' : 'rose', next: new Map(nextAllowed), msg: o.msg, at: o.t, cmp: had, result: allowed,
        explTitle: allowed ? 'Allowed' : 'Suppressed',
        explText: allowed ? `${o.t} >= ${had}, so it prints; next_allowed["${o.msg}"] = ${o.t + 10}.` : `${o.t} < ${had}, too soon — suppressed.`, pause: true }, ctx);
    });
    return seq;
  },
  renderDOM(container, s) {
    const rows = chipRow([...s.next.entries()].map(([m, t]) => `${m}: next ${t}`), { cls: (v) => s.msg && v.startsWith(s.msg + ':') ? 'active-1' : '' });
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.msg ? `shouldPrintMessage(${s.at}, "${s.msg}")` : 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:${s.result ? 'var(--emerald)' : 'var(--red)'};">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('next_allowed[message]', rows)
    );
  }
});

/* =========================================================== 25 · Design Linked List == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design Linked List', short: 'Linked List',
  idea: 'A doubly linked list with dummy head and dummy tail sentinels, plus a maintained size. get() walks from whichever end is closer to the index.',
  complexity: 'get/addAtIndex/deleteAtIndex O(min(index, size-index)) · addAtHead/addAtTail O(1) · Space O(n)',
  input: 'addHead 3, addTail 5, addIdx 1 9, get 1, delIdx 0, get 0', hint: 'ops: addHead v | addTail v | addIdx i v | delIdx i | get i',
  code: [
    'def addAtHead(val): insert_before(head.next, val)',
    'def addAtTail(val): insert_before(tail, val)',
    'def addAtIndex(index, val):',
    '    if index > size: return',
    '    target = node_at(index) if index < size else tail',
    '    insert_before(target, val)',
    'def deleteAtIndex(index):',
    '    if not (0 <= index < size): return',
    '    node = node_at(index)',
    '    node.prev.next, node.next.prev = node.next, node.prev',
    'def get(index): return node_at(index).val  # or -1 if out of range',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'addHead' && t.length === 2) return { op: 'addHead', val: +t[1] };
      if (t[0] === 'addTail' && t.length === 2) return { op: 'addTail', val: +t[1] };
      if (t[0] === 'addIdx' && t.length === 3) return { op: 'addIdx', idx: +t[1], val: +t[2] };
      if (t[0] === 'delIdx' && t.length === 2) return { op: 'delIdx', idx: +t[1] };
      if (t[0] === 'get' && t.length === 2) return { op: 'get', idx: +t[1] };
      throw new Error(`"${op}" — use addHead v | addTail v | addIdx i v | delIdx i | get i`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let list = [];
    domPushState(seq, { line: 0, color: 'default', list: [...list], result: null, op: null,
      explTitle: 'Start', explText: 'Empty list: dummy head <-> dummy tail.', pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'addHead') { list.unshift(o.val);
        domPushState(seq, { line: 1, color: 'blue', list: [...list], result: null, op: `addAtHead(${o.val})`, hi: 0,
          explTitle: 'Insert before head.next', explText: `${o.val} becomes the new first node.` }, ctx);
      } else if (o.op === 'addTail') { list.push(o.val);
        domPushState(seq, { line: 2, color: 'blue', list: [...list], result: null, op: `addAtTail(${o.val})`, hi: list.length - 1,
          explTitle: 'Insert before tail', explText: `${o.val} becomes the new last node.` }, ctx);
      } else if (o.op === 'addIdx') {
        if (o.idx > list.length) {
          domPushState(seq, { line: 4, color: 'rose', list: [...list], result: null, op: `addAtIndex(${o.idx}, ${o.val})`, hi: -1,
            explTitle: 'Out of range', explText: `index ${o.idx} > size ${list.length} — do nothing.`, pause: true }, ctx);
        } else {
          const idx = Math.max(0, o.idx);
          list.splice(idx, 0, o.val);
          domPushState(seq, { line: 5, color: 'blue', list: [...list], result: null, op: `addAtIndex(${o.idx}, ${o.val})`, hi: idx,
            explTitle: 'Walk to index, insert before it', explText: `Inserted ${o.val} at index ${idx}.` }, ctx);
        }
      } else if (o.op === 'delIdx') {
        if (o.idx < 0 || o.idx >= list.length) {
          domPushState(seq, { line: 8, color: 'rose', list: [...list], result: null, op: `deleteAtIndex(${o.idx})`, hi: -1,
            explTitle: 'Out of range', explText: `index ${o.idx} is not a valid index — do nothing.`, pause: true }, ctx);
        } else {
          const removed = list[o.idx]; list.splice(o.idx, 1);
          domPushState(seq, { line: 9, color: 'rose', list: [...list], result: null, op: `deleteAtIndex(${o.idx})`, hi: -1,
            explTitle: 'Unlink node', explText: `Removed node ${removed} at index ${o.idx}: node.prev.next = node.next, node.next.prev = node.prev.` }, ctx);
        }
      } else {
        const ok = o.idx >= 0 && o.idx < list.length;
        domPushState(seq, { line: 10, color: ok ? 'emerald' : 'amber', list: [...list], result: ok ? list[o.idx] : -1, op: `get(${o.idx})`, hi: ok ? o.idx : -1,
          explTitle: 'Walk to index', explText: ok ? `Node at index ${o.idx} has value ${list[o.idx]}.` : `index ${o.idx} out of range → -1.`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const body = dllChainHTML(s.list.map((v, i) => ({ v, i })), {
      label: it => `<div style="font-weight:bold;">${it.v}</div><div class="node-index" style="position:static; margin-top:2px;">${it.i}</div>`,
      cls: it => it.i === s.hi ? 'active-1' : 'merged',
    });
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('doubly linked list', `<div class="array-track" style="padding-top:15px; overflow-x:auto;">${body}</div>`)
    );
  }
});

/* =================================================== 25 · Insert Delete GetRandom O(1) == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Insert Delete GetRandom O(1)', short: 'RandomizedSet',
  idea: 'An array (for O(1) random access) plus a value->index dict. Removal swaps the target with the LAST array element, then pops — never shifting the middle of the array.',
  complexity: 'insert/remove/getRandom O(1) · Space O(n)',
  input: 'insert 4, insert 9, insert 2, remove 4, insert 4, getRandom', hint: 'ops: insert v | remove v | getRandom',
  code: [
    'def insert(val):',
    '    if val in index: return False',
    '    index[val] = len(arr); arr.append(val)',
    '    return True',
    'def remove(val):',
    '    if val not in index: return False',
    '    i, last = index[val], arr[-1]',
    '    arr[i] = last; index[last] = i     # swap gap with last',
    '    arr.pop(); del index[val]',
    '    return True',
    'def getRandom(): return random.choice(arr)',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if ((t[0] === 'insert' || t[0] === 'remove') && t.length === 2) return { op: t[0], val: +t[1] };
      if (t[0] === 'getRandom' && t.length === 1) return { op: 'getRandom' };
      throw new Error(`"${op}" — use "insert v", "remove v" or "getRandom"`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let arr = []; const index = new Map();
    domPushState(seq, { line: 0, color: 'default', arr: [...arr], index: new Map(index), result: null, op: null, hi: [],
      explTitle: 'Start', explText: 'Empty array and empty value->index map.', pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'insert') {
        const had = index.has(o.val);
        if (!had) { index.set(o.val, arr.length); arr.push(o.val); }
        domPushState(seq, { line: 2, color: had ? 'rose' : 'blue', arr: [...arr], index: new Map(index), result: !had, op: `insert(${o.val})`, hi: had ? [] : [arr.length - 1],
          explTitle: had ? 'Already present' : 'Append + index it', explText: had ? `${o.val} is already in the set → False.` : `Appended ${o.val} at index ${arr.length - 1}; index[${o.val}] = ${arr.length - 1}.`, pause: true }, ctx);
      } else if (o.op === 'remove') {
        const had = index.has(o.val);
        if (had) {
          const i = index.get(o.val), last = arr[arr.length - 1];
          arr[i] = last; index.set(last, i);
          arr.pop(); index.delete(o.val);
        }
        domPushState(seq, { line: 8, color: had ? 'rose' : 'amber', arr: [...arr], index: new Map(index), result: had, op: `remove(${o.val})`, hi: [],
          explTitle: had ? 'Swap-with-last, then pop' : 'Not present', explText: had ? `Moved the last element into ${o.val}'s old slot, then popped — O(1), no shifting.` : `${o.val} was not in the set → False.`, pause: true }, ctx);
      } else {
        domPushState(seq, { line: 10, color: 'emerald', arr: [...arr], index: new Map(index), result: arr.length ? `one of [${arr.join(', ')}]` : '(empty)', op: 'getRandom()', hi: [],
          explTitle: 'Uniform pick', explText: `random.choice(arr) — every array slot is equally likely, and the array has no gaps.`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const arrHTML = dpStrip(s.arr, { clsOf: (v, i) => s.hi.includes(i) ? 'active-k' : '' });
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      dpPanel('arr', arrHTML),
      ggPanel('index (value → position)', chipRow([...s.index.entries()].map(([v, i]) => `${v}@${i}`)))
    );
  }
});

/* ====================================================== 25 · Design Browser History == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design Browser History', short: 'Browser History',
  idea: 'An array of visited URLs plus a cursor. visit() truncates everything after the cursor before appending — that\'s how "forward" history disappears once you navigate somewhere new.',
  complexity: 'visit O(1) amortized · back/forward O(1) · Space O(pages visited)',
  input: 'visit a.com, visit b.com, visit c.com, back 1, back 1, forward 1, visit d.com, forward 2', hint: 'homepage = home.com; ops: visit url | back n | forward n',
  code: [
    'def visit(url):',
    '    del history[cursor+1:]        # discard forward history',
    '    history.append(url); cursor += 1',
    'def back(steps):',
    '    cursor = max(0, cursor - steps); return history[cursor]',
    'def forward(steps):',
    '    cursor = min(len(history)-1, cursor + steps); return history[cursor]',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'visit' && t.length === 2) return { op: 'visit', url: t[1] };
      if ((t[0] === 'back' || t[0] === 'forward') && t.length === 2 && /^\d+$/.test(t[1])) return { op: t[0], n: +t[1] };
      throw new Error(`"${op}" — use "visit url", "back n" or "forward n"`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let history = ['home.com'], cursor = 0;
    domPushState(seq, { line: 0, color: 'default', history: [...history], cursor, result: null, op: null,
      explTitle: 'Start', explText: 'homepage("home.com") — history = [home.com], cursor = 0.', pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'visit') {
        history = history.slice(0, cursor + 1);
        history.push(o.url); cursor++;
        domPushState(seq, { line: 1, color: 'blue', history: [...history], cursor, result: null, op: `visit("${o.url}")`,
          explTitle: 'Truncate forward, then append', explText: `Dropped everything after the cursor, appended "${o.url}", cursor -> ${cursor}.` }, ctx);
      } else if (o.op === 'back') {
        cursor = Math.max(0, cursor - o.n);
        domPushState(seq, { line: 4, color: 'amber', history: [...history], cursor, result: history[cursor], op: `back(${o.n})`,
          explTitle: 'Move cursor left, clamp at 0', explText: `cursor -> ${cursor} -> "${history[cursor]}".`, pause: true }, ctx);
      } else {
        cursor = Math.min(history.length - 1, cursor + o.n);
        domPushState(seq, { line: 6, color: 'amber', history: [...history], cursor, result: history[cursor], op: `forward(${o.n})`,
          explTitle: 'Move cursor right, clamp at end', explText: `cursor -> ${cursor} -> "${history[cursor]}".`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const body = s.history.map((u, i) => `
      <div class="array-node ${i === s.cursor ? 'active-1' : 'merged'}" style="flex-direction:column; min-width:80px;">
          ${i === s.cursor ? '<div class="pointer" style="color:var(--accent)">↓ cursor</div>' : ''}
          <div style="font-size:12px; word-break:break-all; text-align:center;">${esc(u)}</div>
          <div class="node-index">${i}</div>
      </div>`).join('');
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${esc(s.result)}</div>` : ''}
      </div>`,
      dpPanel('history (array + cursor)', body)
    );
  }
});

/* ============================================================ 25 · Design Snake Game == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design Snake Game', short: 'Snake Game',
  idea: 'A deque holds the body in order (head at the front); a parallel set gives O(1) self-collision checks. Each move: compute the new head, pop the tail UNLESS food is eaten, then check collision before committing.',
  complexity: 'move O(1) · Space O(width * height)',
  input: '3,3;1,2|2,2;R,R,D,D', hint: 'width,height; food r,c pairs (|-joined) ; moves (U/D/L/R, comma-joined)',
  code: [
    'def move(direction):',
    '    r, c = body[0] + delta[direction]',
    '    if out of bounds: return -1',
    '    ate = (r,c) == food[food_index]',
    '    tail = None if ate else body.pop()   # keep length if eating',
    '    if (r,c) in body_set:                # would hit itself',
    '        if tail: body.append(tail)       # undo the pop',
    '        return -1',
    '    body.appendleft((r,c))',
    '    if ate: score += 1; food_index += 1',
    '    return score',
  ],
  parse(s) {
    const m = String(s || '').split(';');
    if (m.length !== 3) throw new Error('Use "W,H; r,c|r,c; U,D,L,R,..."');
    const [wh, foodStr, movesStr] = m;
    const [w, h] = wh.split(',').map(Number);
    if (!(w > 0 && h > 0 && w <= 8 && h <= 8)) throw new Error('Grid must be 1..8 on each side');
    const food = foodStr.trim() ? foodStr.split('|').map(p => p.split(',').map(Number)) : [];
    const moves = movesStr.split(',').map(x => x.trim().toUpperCase()).filter(Boolean);
    if (!moves.length || moves.length > 12) throw new Error('Use 1..12 moves');
    moves.forEach(d => { if (!'UDLR'.includes(d)) throw new Error(`"${d}" must be one of U/D/L/R`); });
    return { w, h, food, moves };
  },
  buildStates({ w, h, food, moves }) {
    const DELTA = { U: [-1, 0], D: [1, 0], L: [0, -1], R: [0, 1] };
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let body = [[0, 0]], score = 0, foodIdx = 0;
    const key = p => p[0] + ',' + p[1];
    const bodySet = () => new Set(body.map(key));
    domPushState(seq, { line: 0, color: 'default', w, h, food, foodIdx, body: [...body], score, dead: false, dir: null,
      explTitle: 'Start', explText: 'Snake is a single segment at (0,0).', pause: true }, ctx);
    for (const d of moves) {
      const [dr, dc] = DELTA[d];
      const [r, c] = body[0];
      const nr = r + dr, nc = c + dc;
      if (nr < 0 || nr >= h || nc < 0 || nc >= w) {
        domPushState(seq, { line: 2, color: 'red', w, h, food, foodIdx, body: [...body], score, dead: true, dir: d,
          explTitle: 'Wall collision', explText: `Moving ${d} leaves the ${w}x${h} board → game over (-1).`, pause: true }, ctx);
        break;
      }
      const ate = foodIdx < food.length && nr === food[foodIdx][0] && nc === food[foodIdx][1];
      let tail = null;
      const set = bodySet();
      if (!ate) { tail = body[body.length - 1]; body = body.slice(0, -1); set.delete(key(tail)); }
      if (set.has(key([nr, nc]))) {
        domPushState(seq, { line: 6, color: 'red', w, h, food, foodIdx, body: [...body, ...(tail ? [tail] : [])], score, dead: true, dir: d,
          explTitle: 'Self collision', explText: `(${nr},${nc}) is already part of the body → game over (-1).`, pause: true }, ctx);
        break;
      }
      body.unshift([nr, nc]);
      if (ate) { score++; foodIdx++; }
      domPushState(seq, { line: 8, color: ate ? 'emerald' : 'blue', w, h, food, foodIdx, body: [...body], score, dead: false, dir: d,
        explTitle: ate ? 'Ate food — grow' : 'Move — same length', explText: ate ? `New head at (${nr},${nc}) eats food #${foodIdx - 1}; tail NOT removed, score -> ${score}.` : `New head at (${nr},${nc}); tail (${tail}) removed.` }, ctx);
    }
    return seq;
  },
  renderDOM(container, s) {
    const bodySet = new Map(s.body.map((p, i) => [p[0] + ',' + p[1], i]));
    const grid = [];
    for (let r = 0; r < s.h; r++) { const row = []; for (let c = 0; c < s.w; c++) row.push([r, c]); grid.push(row); }
    const isFood = (r, c) => !s.dead && s.foodIdx < s.food.length && r === s.food[s.foodIdx][0] && c === s.food[s.foodIdx][1];
    const html = ggGridHTML(grid, ([r, c]) => {
      const k = r + ',' + c, idx = bodySet.get(k);
      if (idx === 0) return { content: 'H', bg: 'var(--accent)', color: '#fff' };
      if (idx !== undefined) return { content: '', bg: 'var(--emerald)', opacity: 0.7 };
      if (isFood(r, c)) return { content: '*', bg: 'var(--amber)' };
      return { content: '' };
    }, { cell: 34 });
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.dir ? `move("${s.dir}")` : 'ready'}</div>
          <div style="font-weight:bold; color:${s.dead ? 'var(--red)' : 'var(--accent)'};">score = ${s.dead ? -1 : s.score}</div>
      </div>`,
      ggPanel(`${s.w}x${s.h} board`, html)
    );
  }
});

/* ==================================================================== 25 · LFU Cache == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'LFU Cache', short: 'LFU Cache',
  idea: 'A value map, a frequency->doubly-linked-list-of-keys map, and a running min_freq. get/put both bump a key one frequency bucket over (MRU end of its new bucket); eviction always pops the LRU end of the min_freq bucket.',
  complexity: 'get/put O(1) · Space O(capacity)',
  input: '2; put 1 1, put 2 2, get 1, put 3 3, get 2, get 3, put 4 4, get 1, get 3, get 4', hint: 'capacity; ops: get k | put k v',
  code: [
    'def get(key):',
    '    node = key_node[key]; bump(node); return node.val',
    'def put(key, value):',
    '    if key in key_node: key_node[key].val = value; bump(key_node[key]); return',
    '    if len(key_node) >= capacity:',
    '        evict = freq_list[min_freq].pop_back(); del key_node[evict.key]',
    '    node = Node(key, value); key_node[key] = node',
    '    freq_list[1].push_front(node); min_freq = 1',
    '',
    'def bump(node):                       # move node up one frequency bucket',
    '    freq_list[node.freq].remove(node)',
    '    if freq_list[node.freq] empty and min_freq == node.freq: min_freq += 1',
    '    node.freq += 1; freq_list[node.freq].push_front(node)',
  ],
  parse(s) {
    const m = String(s || '').split(';');
    if (m.length !== 2) throw new Error('Use "capacity; ops"');
    const cap = +m[0].trim();
    if (!(cap >= 1 && cap <= 6)) throw new Error('capacity must be 1..6');
    const raw = opsParse(m[1]);
    return { cap, ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'get' && t.length === 2) return { op: 'get', key: +t[1] };
      if (t[0] === 'put' && t.length === 3) return { op: 'put', key: +t[1], val: +t[2] };
      throw new Error(`"${op}" — use "get k" or "put k v"`);
    }) };
  },
  buildStates({ cap, ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let minFreq = 0;
    const val = new Map();       // key -> value
    const keyFreq = new Map();   // key -> current freq
    const buckets = new Map();   // freq -> [keys], index 0 = MRU (front), last index = LRU (back) — mirrors the real _DLList's push_front/pop_back
    const bucketOf = f => { if (!buckets.has(f)) buckets.set(f, []); return buckets.get(f); };
    const removeFromBucket = (k, f) => { const b = bucketOf(f); const i = b.indexOf(k); if (i >= 0) b.splice(i, 1); };
    const snap = extra => ({ cap, val: new Map(val), freqList: new Map([...buckets].filter(([, arr]) => arr.length).map(([f, arr]) => [f, [...arr]])), minFreq, ...extra });
    const bump = k => {
      const f = keyFreq.get(k);
      removeFromBucket(k, f);
      if (bucketOf(f).length === 0 && minFreq === f) minFreq++;
      keyFreq.set(k, f + 1);
      bucketOf(f + 1).unshift(k); // push_front
    };
    domPushState(seq, { line: 0, color: 'default', ...snap({ op: null, result: null, hi: null }) }, ctx);
    ops.forEach(o => {
      if (o.op === 'get') {
        if (!val.has(o.key)) {
          domPushState(seq, { line: 1, color: 'amber', ...snap({ op: `get(${o.key})`, result: -1, hi: null }),
            explTitle: 'Miss', explText: `${o.key} is not cached → -1.`, pause: true }, ctx);
        } else {
          bump(o.key);
          domPushState(seq, { line: 1, color: 'emerald', ...snap({ op: `get(${o.key})`, result: val.get(o.key), hi: o.key }),
            explTitle: 'Hit — bump frequency', explText: `Return ${val.get(o.key)}; key ${o.key} moves to freq ${keyFreq.get(o.key)} (front of that bucket).`, pause: true }, ctx);
        }
      } else {
        if (val.has(o.key)) {
          val.set(o.key, o.val); bump(o.key);
          domPushState(seq, { line: 3, color: 'blue', ...snap({ op: `put(${o.key}, ${o.val})`, result: null, hi: o.key }),
            explTitle: 'Update + bump', explText: `Key ${o.key} already cached — update value, bump to freq ${keyFreq.get(o.key)}.` }, ctx);
        } else {
          if (val.size >= cap) {
            const bucket = bucketOf(minFreq);
            const evictKey = bucket[bucket.length - 1]; // back of the bucket = LRU
            bucket.pop();
            val.delete(evictKey); keyFreq.delete(evictKey);
            domPushState(seq, { line: 5, color: 'rose', ...snap({ op: `put(${o.key}, ${o.val})`, result: null, hi: null }),
              explTitle: 'Evict', explText: `Cache full at capacity ${cap} — evict key ${evictKey}, the LRU entry of freq ${minFreq}.` }, ctx);
          }
          val.set(o.key, o.val); keyFreq.set(o.key, 1); bucketOf(1).unshift(o.key); minFreq = 1;
          domPushState(seq, { line: 7, color: 'blue', ...snap({ op: `put(${o.key}, ${o.val})`, result: null, hi: o.key }),
            explTitle: 'Insert at freq 1', explText: `New key ${o.key} = ${o.val}, freq 1; min_freq resets to 1.`, pause: true }, ctx);
        }
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const freqs = [...s.freqList.keys()].sort((a, b) => a - b);
    const rows = freqs.map(f => `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px; padding:6px; border-radius:6px; ${f === s.minFreq ? 'background:var(--bg-surface); border:1px solid var(--amber);' : ''}">
          <div style="width:90px; font-weight:bold; color:var(--text-dim);">freq ${f}${f === s.minFreq ? ' (min)' : ''}</div>
          ${chipRow(s.freqList.get(f).map(k => `${k}:${s.val.get(k)}`), { cls: v => v.startsWith(s.hi + ':') ? 'active-1' : '' })}
      </div>`).join('') || `<div style="color:var(--text-dim); padding:10px;">(empty cache)</div>`;
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'} (cap ${s.cap})</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('per-frequency doubly linked lists (MRU first)', rows)
    );
  }
});

/* ================================================ 25 · Design In-Memory File System == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design In-Memory File System', short: 'File System',
  idea: 'A tree of nodes, each a dict of named children. Every path operation walks segment by segment from the root; a file node also carries content.',
  complexity: 'each op O(path depth) · Space O(total path characters + content)',
  input: 'mkdir /a/b, addContent /a/b/c.txt hello, ls /a/b, readContent /a/b/c.txt, mkdir /a/x, ls /a', hint: 'ops: mkdir /p | addContent /p text | readContent /p | ls /p',
  code: [
    'def _walk(path, create_dirs=False):',
    '    node = root',
    '    for seg in segments(path):',
    '        if seg not in node.children:',
    '            if not create_dirs: return None',
    '            node.children[seg] = Node()',
    '        node = node.children[seg]',
    '    return node',
    '',
    'def ls(path): ...       # sorted(node.children) or [basename] if a file',
    'def mkdir(path): _walk(path, create_dirs=True)',
    'def addContentToFile(path, content): ...   # walk to parent, create file if new, append',
    'def readContentFromFile(path): return _walk(path).content',
  ],
  parse(s) {
    const raw = opsParse(s, { max: 10 });
    return { ops: raw.map(op => {
      const m1 = op.match(/^mkdir\s+(\/\S*)$/);
      if (m1) return { op: 'mkdir', path: m1[1] };
      const m2 = op.match(/^addContent\s+(\/\S*)\s+(.+)$/);
      if (m2) return { op: 'addContent', path: m2[1], text: m2[2] };
      const m3 = op.match(/^readContent\s+(\/\S*)$/);
      if (m3) return { op: 'readContent', path: m3[1] };
      const m4 = op.match(/^ls\s+(\/\S*)$/);
      if (m4) return { op: 'ls', path: m4[1] };
      throw new Error(`"${op}" — use mkdir /p | addContent /p text | readContent /p | ls /p`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const mkNode = () => ({ children: {}, isFile: false, content: null });
    const root = mkNode();
    const segs = p => p.split('/').filter(Boolean);
    const clone = n => ({ children: Object.fromEntries(Object.entries(n.children).map(([k, v]) => [k, clone(v)])), isFile: n.isFile, content: n.content });
    const walk = (path, create) => {
      let node = root, cur = '';
      for (const seg of segs(path)) {
        cur += '/' + seg;
        if (!node.children[seg]) { if (!create) return null; node.children[seg] = mkNode(); }
        node = node.children[seg];
      }
      return node;
    };
    domPushState(seq, { line: 0, color: 'default', root: clone(root), op: null, result: null, path: null,
      explTitle: 'Start', explText: 'Just the root directory.', pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'mkdir') {
        walk(o.path, true);
        domPushState(seq, { line: 1, color: 'blue', root: clone(root), op: `mkdir("${o.path}")`, result: null, path: o.path,
          explTitle: 'Walk + create', explText: `Created any missing directory segments of "${o.path}".` }, ctx);
      } else if (o.op === 'addContent') {
        const parts = segs(o.path); const name = parts[parts.length - 1];
        const parentPath = '/' + parts.slice(0, -1).join('/');
        const parent = walk(parentPath, true);
        if (!parent.children[name]) { parent.children[name] = mkNode(); parent.children[name].isFile = true; parent.children[name].content = ''; }
        parent.children[name].content += o.text;
        domPushState(seq, { line: 9, color: 'blue', root: clone(root), op: `addContentToFile("${o.path}", "${o.text}")`, result: null, path: o.path,
          explTitle: 'Append to file', explText: `File "${name}" now holds "${parent.children[name].content}".` }, ctx);
      } else if (o.op === 'readContent') {
        const node = walk(o.path, false);
        domPushState(seq, { line: 11, color: 'emerald', root: clone(root), op: `readContentFromFile("${o.path}")`, result: node ? node.content : '(not found)', path: o.path,
          explTitle: 'Walk to the file', explText: `Content: "${node ? node.content : ''}".`, pause: true }, ctx);
      } else {
        const node = walk(o.path, false);
        const listing = node ? (node.isFile ? [o.path.split('/').pop()] : Object.keys(node.children).sort()) : [];
        domPushState(seq, { line: 8, color: 'amber', root: clone(root), op: `ls("${o.path}")`, result: `[${listing.join(', ')}]`, path: o.path,
          explTitle: 'List children (sorted) or the file itself', explText: `${node && node.isFile ? 'This path is a file' : 'This path is a directory'} → [${listing.join(', ')}].`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const renderTree = (node, name, depth, path) => {
      const isTarget = s.path === path;
      const line = `<div style="padding-left:${depth * 18}px; ${isTarget ? 'background:var(--bg-surface); border-radius:4px;' : ''}">
        <span style="color:${node.isFile ? 'var(--amber)' : 'var(--accent)'}; font-weight:${isTarget ? 'bold' : '600'};">${node.isFile ? '📄' : '📁'} ${esc(name)}</span>
        ${node.isFile ? `<span style="color:var(--text-dim); font-size:12px;"> — "${esc(node.content || '')}"</span>` : ''}
      </div>`;
      const kids = Object.entries(node.children).sort(([a], [b]) => a < b ? -1 : 1)
        .map(([k, v]) => renderTree(v, k, depth + 1, path === '/' ? '/' + k : path + '/' + k)).join('');
      return line + kids;
    };
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${esc(String(s.result))}</div>` : ''}
      </div>`,
      ggPanel('directory tree', renderTree(s.root, '/', 0, '/'))
    );
  }
});

/* ============================================= 25 · Design Search Autocomplete System == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design Search Autocomplete System', short: 'Autocomplete',
  idea: 'A trie where EVERY node (not just leaves) keeps a sentence -> hot_degree tally, updated on the path of every insert. Typing a character walks one edge; the ranked top-3 (highest count, then lexicographically) is read straight off the current node.',
  complexity: 'input(c) O(1) navigation + O(k log k) to rank k matching sentences · Space O(sum of len(sentence)^2)',
  input: 'i love you:5, island:3, iroman:2, i love leetcode:2 ; i,#,i, ,a,#', hint: 'sentences:count (comma-joined) ; typed chars, "#" ends a sentence',
  code: [
    'def _insert(sentence, delta):',
    '    node = root; node.counts[sentence] += delta',
    '    for ch in sentence:',
    '        node = node.children.setdefault(ch, Node())',
    '        node.counts[sentence] += delta',
    '',
    'def input(c):',
    '    if c == "#": _insert(buffer, 1); buffer = ""; node = root; return []',
    '    buffer += c; node = node.children.get(c)',
    '    if node is None: return []',
    '    ranked = sorted(node.counts.items(), key=lambda kv: (-kv[1], kv[0]))',
    '    return [sentence for sentence, _ in ranked[:3]]',
  ],
  parse(s) {
    const parts = String(s || '').split(';');
    if (parts.length !== 2) throw new Error('Use "sentence:count, ... ; typed chars"');
    const seed = parts[0].split(',').map(x => x.trim()).filter(Boolean).map(x => {
      const i = x.lastIndexOf(':');
      if (i < 0) throw new Error(`"${x}" needs a ":count"`);
      return { sentence: x.slice(0, i).trim(), count: +x.slice(i + 1) };
    });
    const chars = parts[1].split(',').map(x => x.trim());
    if (!chars.length || chars.length > 14) throw new Error('Use 1..14 typed characters');
    return { seed, chars: chars.map(c => c === '' ? ' ' : c) };
  },
  buildStates({ seed, chars }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const mkNode = () => ({ counts: new Map() });
    const root = mkNode();
    const bump = (node, sentence, delta) => node.counts.set(sentence, (node.counts.get(sentence) || 0) + delta);
    const insert = (sentence, delta) => { let node = root; bump(node, sentence, delta); for (const ch of sentence) { if (!node.children) node.children = {}; node.children[ch] = node.children[ch] || mkNode(); node = node.children[ch]; bump(node, sentence, delta); } };
    seed.forEach(({ sentence, count }) => insert(sentence, count));
    let node = root, buffer = '', path = [];
    const rankOf = n => [...n.counts.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).slice(0, 3).map(([snt]) => snt);
    domPushState(seq, { line: 0, color: 'default', buffer: '', path: [], ranked: [], ch: null,
      explTitle: 'Start', explText: `Trie seeded with ${seed.length} sentence(s). Buffer is empty.`, pause: true }, ctx);
    chars.forEach(c => {
      if (c === '#') {
        insert(buffer, 1);
        domPushState(seq, { line: 7, color: 'emerald', buffer, path: [...path], ranked: [], ch: '#',
          explTitle: 'End of sentence', explText: `"${buffer}" inserted (hot_degree +1) along its whole path; buffer resets, node -> root.`, pause: true }, ctx);
        buffer = ''; node = root; path = [];
        return;
      }
      buffer += c;
      node = node && node.children ? node.children[c] : undefined;
      path.push(c);
      const ranked = node ? rankOf(node) : [];
      domPushState(seq, { line: 8, color: node ? 'blue' : 'rose', buffer, path: [...path], ranked, ch: c,
        explTitle: node ? `Follow '${c === ' ' ? '␣' : c}'` : 'No such branch',
        explText: node ? `Buffer is now "${buffer}"; top-3 at this node: [${ranked.join(', ') || '(none)'}].` : `No child for '${c}' — nothing matches "${buffer}", return [].`,
        pause: true }, ctx);
    });
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">input('${s.ch === ' ' ? '␣' : (s.ch ?? '')}')</div>
          <div style="font-weight:bold; color:var(--accent);">buffer: "${esc(s.buffer)}"</div>
      </div>`,
      ggPanel('trie path walked so far', chipRow(s.path.length ? s.path.map(c => c === ' ' ? '␣' : c) : ['(root)'])),
      ggPanel('ranked top-3 at current node (count desc, then lexicographic)', chipRow(s.ranked.length ? s.ranked : ['(none)'], { cls: () => 'active-k' }))
    );
  }
});

/* ========================================================= 25 · Design Hit Counter == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Design Hit Counter', short: 'Hit Counter',
  idea: 'A fixed circular array of buckets, one per second in the window, each tagged with the second it currently represents. On a hit, if the bucket\'s tag is stale it resets before incrementing — this bounds memory at exactly WINDOW slots (real LeetCode uses 300; this demo uses 10 so it fits on screen).',
  complexity: 'hit O(1) · getHits O(WINDOW) · Space O(WINDOW)',
  input: 'hit 1, hit 2, hit 2, getHits 3, hit 11, getHits 11, getHits 12', hint: 'WINDOW=10 for this demo; ops: hit t | getHits t',
  code: [
    'WINDOW = 10   # real LeetCode: 300',
    'times = [0]*WINDOW; counts = [0]*WINDOW',
    '',
    'def hit(timestamp):',
    '    i = timestamp % WINDOW',
    '    if times[i] != timestamp: times[i] = timestamp; counts[i] = 0',
    '    counts[i] += 1',
    '',
    'def getHits(timestamp):',
    '    return sum(c for s, c in zip(times, counts) if timestamp - s < WINDOW)',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if ((t[0] === 'hit' || t[0] === 'getHits') && t.length === 2 && /^\d+$/.test(t[1])) return { op: t[0], t: +t[1] };
      throw new Error(`"${op}" — use "hit t" or "getHits t"`);
    }) };
  },
  buildStates({ ops }) {
    const W = 10;
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const times = new Array(W).fill(0), counts = new Array(W).fill(0);
    let touched = new Array(W).fill(false);
    domPushState(seq, { line: 1, color: 'default', times: [...times], counts: [...counts], touched: [...touched], active: -1, op: null, result: null,
      explTitle: 'Start', explText: `${W} empty circular buckets.`, pause: true }, ctx);
    ops.forEach(o => {
      const i = o.t % W;
      if (o.op === 'hit') {
        const stale = times[i] !== o.t;
        if (stale) { times[i] = o.t; counts[i] = 0; }
        counts[i]++; touched[i] = true;
        domPushState(seq, { line: 5, color: 'blue', times: [...times], counts: [...counts], touched: [...touched], active: i, op: `hit(${o.t})`, result: null,
          explTitle: `Bucket ${i} = ${o.t} % ${W}`, explText: stale ? `Bucket was tagged for a different second — reset to ${o.t}, count=1.` : `Bucket already tagged ${o.t} — count -> ${counts[i]}.` }, ctx);
      } else {
        const total = times.reduce((sum, tS, idx) => sum + (o.t - tS < W && touched[idx] ? counts[idx] : 0), 0);
        domPushState(seq, { line: 9, color: 'emerald', times: [...times], counts: [...counts], touched: [...touched], active: -1, op: `getHits(${o.t})`, result: total, atQuery: o.t,
          explTitle: 'Sum still-fresh buckets', explText: `Every bucket with (t - tag) < ${W} contributes its count; total = ${total}.`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const grid = [s.times.map((t, i) => ({ t, c: s.counts[i], i, touched: s.touched[i] }))];
    const html = ggGridHTML(grid, cell => {
      const stale = s.atQuery !== undefined && (s.atQuery - cell.t >= 10 || !cell.touched);
      return {
        content: cell.touched ? `${cell.c}` : '·',
        bg: cell.i === s.active ? 'var(--accent)' : (s.atQuery !== undefined && cell.touched && !stale ? 'var(--emerald)' : 'var(--surface)'),
        color: cell.i === s.active ? '#fff' : undefined,
        fontSize: 12,
      };
    }, { cell: 40 });
    const tags = ggGridHTML([s.times.map((t, i) => ({ t, touched: s.touched[i] }))], c => ({ content: c.touched ? c.t : '-', fontSize: 10, bg: 'transparent' }), { cell: 40 });
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('bucket second-tags (times[])', tags),
      ggPanel('bucket counts (counts[]) — green = still inside the window', html)
    );
  }
});

/* ============================================================ 25 · Snapshot Array == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Snapshot Array', short: 'Snapshot Array',
  idea: 'Each index keeps its OWN sparse history of (snap_id, value) pairs — set() only touches the one index being written, and a global snap_id counter is shared by all indices. get() binary-searches an index\'s history for the newest entry at or before the requested snap_id.',
  complexity: 'set O(1) amortized · snap O(1) · get O(log entries at that index) · Space O(total sets)',
  input: '4; set 0 5, snap, set 0 6, get 0 0, snap, set 2 9, get 0 1, get 2 1', hint: 'length; ops: set i v | snap | get i snapId',
  code: [
    'history = [[(-1, 0)] for _ in range(length)]   # sentinel (-1, 0) = "0 before any set"',
    'snap_id = 0',
    '',
    'def set(index, val):',
    '    h = history[index]',
    '    if h[-1][0] == snap_id: h[-1] = (snap_id, val)   # same snapshot, overwrite',
    '    else: h.append((snap_id, val))',
    '',
    'def snap(): snap_id += 1; return snap_id - 1',
    '',
    'def get(index, snap_id):',
    '    h = history[index]',
    '    return h[bisect_right(h, (snap_id, INF)) - 1][1]',
  ],
  parse(s) {
    const m = String(s || '').split(';');
    if (m.length !== 2) throw new Error('Use "length; ops"');
    const len = +m[0].trim();
    if (!(len >= 1 && len <= 6)) throw new Error('length must be 1..6');
    const raw = opsParse(m[1]);
    return { len, ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'set' && t.length === 3) return { op: 'set', i: +t[1], v: +t[2] };
      if (t[0] === 'snap' && t.length === 1) return { op: 'snap' };
      if (t[0] === 'get' && t.length === 3) return { op: 'get', i: +t[1], snapId: +t[2] };
      throw new Error(`"${op}" — use "set i v", "snap" or "get i snapId"`);
    }) };
  },
  buildStates({ len, ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const history = Array.from({ length: len }, () => [[-1, 0]]);
    let snapId = 0;
    const snapshot = () => history.map(h => [...h]);
    domPushState(seq, { line: 0, color: 'default', history: snapshot(), snapId, op: null, result: null, hi: null,
      explTitle: 'Start', explText: `${len} indices, each starting with the sentinel (-1, 0).`, pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'set') {
        const h = history[o.i];
        if (h[h.length - 1][0] === snapId) h[h.length - 1] = [snapId, o.v]; else h.push([snapId, o.v]);
        domPushState(seq, { line: 5, color: 'blue', history: snapshot(), snapId, op: `set(${o.i}, ${o.v})`, result: null, hi: o.i,
          explTitle: 'Append/overwrite this index\'s history', explText: `Index ${o.i} now has (${snapId}, ${o.v}) as its latest entry.` }, ctx);
      } else if (o.op === 'snap') {
        const id = snapId; snapId++;
        domPushState(seq, { line: 8, color: 'amber', history: snapshot(), snapId, op: 'snap()', result: id, hi: null,
          explTitle: 'Bump the global counter', explText: `Returns ${id}; future set() calls now write under snap_id ${snapId}.`, pause: true }, ctx);
      } else {
        const h = history[o.i];
        let lo = 0, hi = h.length; // bisect_right on (snapId, +inf)
        while (lo < hi) { const mid = (lo + hi) >> 1; if (h[mid][0] <= o.snapId) lo = mid + 1; else hi = mid; }
        const val = h[lo - 1][1];
        domPushState(seq, { line: 11, color: 'emerald', history: snapshot(), snapId, op: `get(${o.i}, ${o.snapId})`, result: val, hi: o.i,
          explTitle: 'Binary search this index\'s history', explText: `Newest entry with snap_id <= ${o.snapId} is (${h[lo - 1][0]}, ${val}) -> ${val}.`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const rows = s.history.map((h, i) => `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px; padding:6px; border-radius:6px; ${i === s.hi ? 'background:var(--bg-surface); border:1px solid var(--accent);' : ''}">
          <div style="width:60px; font-weight:bold; color:var(--text-dim);">index ${i}</div>
          ${chipRow(h.map(([id, v]) => `(${id},${v})`))}
      </div>`).join('');
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'} · next snap_id = ${s.snapId}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('per-index history of (snap_id, value)', rows)
    );
  }
});

/* ==================================================== 25 · Stock Price Fluctuation == */
defineAlgoDom('25_design', {
  type: 'dom',
  title: 'Stock Price Fluctuation', short: 'Stock Price',
  idea: 'A timestamp->price dict is the source of truth; a max-heap and a min-heap of (price, timestamp) give fast current-max/min, but a correction can leave STALE heap entries — maximum()/minimum() lazily pop any entry whose price no longer matches the dict.',
  complexity: 'update O(log n) · current O(1) · maximum/minimum O(log n) amortized · Space O(updates)',
  input: 'update 1 10, update 2 5, current, maximum, minimum, update 1 3, maximum, minimum', hint: 'ops: update t price | current | maximum | minimum',
  code: [
    'def update(timestamp, price):',
    '    prices[timestamp] = price',
    '    latest = max(latest, timestamp)',
    '    heappush(max_heap, (-price, timestamp))',
    '    heappush(min_heap, (price, timestamp))',
    '',
    'def current(): return prices[latest]',
    '',
    'def maximum():',
    '    while prices[max_heap[0][1]] != -max_heap[0][0]: heappop(max_heap)   # discard stale',
    '    return -max_heap[0][0]',
    '',
    'def minimum():   # symmetric with min_heap',
  ],
  parse(s) {
    const raw = opsParse(s);
    return { ops: raw.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'update' && t.length === 3) return { op: 'update', ts: +t[1], price: +t[2] };
      if (['current', 'maximum', 'minimum'].includes(t[0]) && t.length === 1) return { op: t[0] };
      throw new Error(`"${op}" — use "update t price", "current", "maximum" or "minimum"`);
    }) };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const prices = new Map();
    let latest = 0, maxHeap = [], minHeap = [];
    const snap = extra => ({ prices: new Map(prices), latest, maxHeap: hqClone(maxHeap), minHeap: hqClone(minHeap), ...extra });
    domPushState(seq, { line: 0, color: 'default', ...snap({ op: null, result: null, stale: [] }),
      explTitle: 'Start', explText: 'No prices recorded yet.', pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'update') {
        prices.set(o.ts, o.price);
        if (o.ts > latest) latest = o.ts;
        hqPush(maxHeap, [-o.price, o.ts]);
        hqPush(minHeap, [o.price, o.ts]);
        domPushState(seq, { line: 3, color: 'blue', ...snap({ op: `update(${o.ts}, ${o.price})`, result: null, stale: [] }),
          explTitle: 'Overwrite + push to both heaps', explText: `prices[${o.ts}] = ${o.price} (old value, if any, is now stale in both heaps — not removed yet).` }, ctx);
      } else if (o.op === 'current') {
        domPushState(seq, { line: 6, color: 'emerald', ...snap({ op: 'current()', result: prices.get(latest), stale: [] }),
          explTitle: 'Read the latest timestamp', explText: `prices[${latest}] = ${prices.get(latest)}.`, pause: true }, ctx);
      } else if (o.op === 'maximum') {
        const popped = [];
        while (maxHeap.length && prices.get(maxHeap[0][1]) !== -maxHeap[0][0]) popped.push(hqPop(maxHeap));
        domPushState(seq, { line: 9, color: 'amber', ...snap({ op: 'maximum()', result: maxHeap.length ? -maxHeap[0][0] : null, stale: popped }),
          explTitle: popped.length ? 'Discard stale heap top(s)' : 'Heap top is already fresh', explText: popped.length ? `Discarded ${popped.length} stale entr${popped.length === 1 ? 'y' : 'ies'} whose price no longer matches; max = ${-maxHeap[0][0]}.` : `max_heap[0] matches prices — max = ${-maxHeap[0][0]}.`,
          pause: true }, ctx);
      } else {
        const popped = [];
        while (minHeap.length && prices.get(minHeap[0][1]) !== minHeap[0][0]) popped.push(hqPop(minHeap));
        domPushState(seq, { line: 10, color: 'amber', ...snap({ op: 'minimum()', result: minHeap.length ? minHeap[0][0] : null, stale: popped }),
          explTitle: popped.length ? 'Discard stale heap top(s)' : 'Heap top is already fresh', explText: popped.length ? `Discarded ${popped.length} stale entr${popped.length === 1 ? 'y' : 'ies'}; min = ${minHeap[0][0]}.` : `min_heap[0] matches prices — min = ${minHeap[0][0]}.`,
          pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s) {
    const maxLabel = ([negP, ts]) => `${-negP}@${ts}`;
    const minLabel = ([p, ts]) => `${p}@${ts}`;
    container.innerHTML = dpWrap(
      `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:12px; border-radius:8px;">
          <div style="font-weight:bold; color:var(--text-bright);">${s.op || 'ready'}</div>
          ${s.result !== null ? `<div style="font-weight:bold; color:var(--accent);">→ ${s.result}</div>` : ''}
      </div>`,
      ggPanel('prices (timestamp → price)', chipRow([...s.prices.entries()].map(([t, p]) => `${t}:${p}`))),
      `<div style="display:flex; gap:15px;">
          <div style="flex:1;">${ggPanel('max_heap (as tree, top = current best guess)', heapTreeHTML(s.maxHeap.map(maxLabel), { width: 260 }))}</div>
          <div style="flex:1;">${ggPanel('min_heap (as tree)', heapTreeHTML(s.minHeap.map(minLabel), { width: 260 }))}</div>
      </div>`
    );
  }
});
