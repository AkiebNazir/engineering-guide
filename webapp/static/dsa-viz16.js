/* ============================================================================
   Visualizations for 12_heap_priority_queue
   ========================================================================= */
'use strict';

/* ============================================================= shared: a JS
   port of CPython's heapq (_siftdown/_siftup) so every array snapshot below
   is the SAME array layout the real `heapq` module would produce — not an
   approximation. Elements may be plain numbers or arrays (compared
   lexicographically, matching how Python compares tuples). ================ */
function hqLess(a, b) {
  if (Array.isArray(a) && Array.isArray(b)) {
    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) {
      if (a[i] < b[i]) return true;
      if (a[i] > b[i]) return false;
    }
    return a.length < b.length;
  }
  return a < b;
}
function hqSiftdown(heap, startpos, pos) {
  const newitem = heap[pos];
  while (pos > startpos) {
    const parentpos = (pos - 1) >> 1;
    const parent = heap[parentpos];
    if (hqLess(newitem, parent)) { heap[pos] = parent; pos = parentpos; continue; }
    break;
  }
  heap[pos] = newitem;
}
function hqSiftup(heap, pos) {
  const endpos = heap.length, startpos = pos;
  const newitem = heap[pos];
  let childpos = 2 * pos + 1;
  while (childpos < endpos) {
    const rightpos = childpos + 1;
    if (rightpos < endpos && !hqLess(heap[childpos], heap[rightpos])) childpos = rightpos;
    heap[pos] = heap[childpos];
    pos = childpos;
    childpos = 2 * pos + 1;
  }
  heap[pos] = newitem;
  hqSiftdown(heap, startpos, pos);
}
function hqPush(heap, item) { heap.push(item); hqSiftdown(heap, 0, heap.length - 1); }
function hqPop(heap) {
  const last = heap.pop();
  if (heap.length) { const top = heap[0]; heap[0] = last; hqSiftup(heap, 0); return top; }
  return last;
}
function hqReplace(heap, item) { const top = heap[0]; heap[0] = item; hqSiftup(heap, 0); return top; }
function hqPushPop(heap, item) {
  if (heap.length && hqLess(heap[0], item)) { const t = heap[0]; heap[0] = item; hqSiftup(heap, 0); return t; }
  return item;
}
function hqify(heap) { for (let i = (heap.length >> 1) - 1; i >= 0; i--) hqSiftup(heap, i); }
const hqClone = h => h.map(v => Array.isArray(v) ? v.slice() : v);

/* ---- DualHeap: lazy-deletion two-heap median tracker (problem 012) ---- */
function dhMake(k) { return { small: [], large: [], delayed: new Map(), smallSize: 0, largeSize: 0, k }; }
function dhGet(d, x) { return d.get(x) || 0; }
function dhPrune(heap, sign, delayed) {
  while (heap.length) {
    const top = sign * heap[0];
    if (dhGet(delayed, top) > 0) { delayed.set(top, delayed.get(top) - 1); hqPop(heap); }
    else break;
  }
}
function dhBalance(dh) {
  if (dh.smallSize > dh.largeSize + 1) {
    hqPush(dh.large, -hqPop(dh.small)); dh.smallSize--; dh.largeSize++;
    dhPrune(dh.small, -1, dh.delayed);
  } else if (dh.smallSize < dh.largeSize) {
    hqPush(dh.small, -hqPop(dh.large)); dh.smallSize++; dh.largeSize--;
    dhPrune(dh.large, 1, dh.delayed);
  }
}
function dhInsert(dh, x) {
  if (!dh.small.length || x <= -dh.small[0]) { hqPush(dh.small, -x); dh.smallSize++; }
  else { hqPush(dh.large, x); dh.largeSize++; }
  dhBalance(dh);
}
function dhErase(dh, x) {
  dh.delayed.set(x, dhGet(dh.delayed, x) + 1);
  if (x <= -dh.small[0]) { dh.smallSize--; if (x === -dh.small[0]) dhPrune(dh.small, -1, dh.delayed); }
  else { dh.largeSize--; if (x === dh.large[0]) dhPrune(dh.large, 1, dh.delayed); }
  dhBalance(dh);
}
function dhMedian(dh) { return (dh.k & 1) ? -dh.small[0] : (-dh.small[0] + dh.large[0]) / 2; }

/* ================================================== shared: heap-as-tree === */
function heapNodePositions(n) {
  const pos = [];
  for (let i = 0; i < n; i++) {
    const level = Math.floor(Math.log2(i + 1));
    const levelCount = 1 << level;
    const levelStart = levelCount - 1;
    pos.push({ level, slot: i - levelStart, levelCount });
  }
  return pos;
}
function heapTreeHTML(arr, { cls = () => '', label = v => v, width = 480 } = {}) {
  if (!arr.length) return `<div style="text-align:center; padding:24px; color:var(--text-dim);">Empty heap</div>`;
  const pos = heapNodePositions(arr.length);
  const depth = pos[pos.length - 1].level + 1;
  const rowH = 62, R = 23, topPad = 24;
  const height = topPad + (depth - 1) * rowH + R * 2 + 6;
  const xy = i => {
    const p = pos[i];
    const slotW = width / (p.levelCount + 1);
    return { x: slotW * (p.slot + 1), y: topPad + p.level * rowH + R };
  };
  let lines = '';
  for (let i = 1; i < arr.length; i++) {
    const parent = (i - 1) >> 1;
    const a = xy(parent), b = xy(i);
    lines += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="var(--border)" stroke-width="2"></line>`;
  }
  let nodes = '';
  for (let i = 0; i < arr.length; i++) {
    const { x, y } = xy(i);
    nodes += `<div class="array-node ${cls(arr[i], i)}" style="position:absolute; left:${x}px; top:${y}px; transform:translate(-50%,-50%); width:${R * 2}px; height:${R * 2}px; min-width:0; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; padding:0; margin:0;">${label(arr[i], i)}</div>`;
  }
  return `<div style="position:relative; width:100%; max-width:${width}px; height:${height}px; margin:0 auto;">
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="position:absolute; left:0; top:0; overflow:visible;">${lines}</svg>
    ${nodes}
  </div>`;
}
function heapArrayStripHTML(arr, { cls = () => '', label = v => v } = {}) {
  if (!arr.length) return `<div style="text-align:center; padding:10px; color:var(--text-dim); font-size:12px;">[ ]</div>`;
  return arr.map((v, i) => `
            <div class="array-node ${cls(v, i)}" style="min-width:46px;">
                ${label(v, i)}
                <div class="node-index">${i}</div>
    </div>`).join('');
}
function chipRow(items, { cls = () => '' } = {}) {
  if (!items.length) return `<div style="color:var(--text-dim); font-size:12px; padding:6px;">(none)</div>`;
  return `<div style="display:flex; flex-wrap:wrap; gap:8px; padding:6px 0;">${items.map((t, i) =>
    `<span class="array-node ${cls(t, i)}" style="min-width:auto; padding:6px 12px;">${t}</span>`).join('')}</div>`;
}

/* ============================================== 001 · Kth Largest in a Stream */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Kth Largest Element in a Stream', short: 'Kth Largest (Stream)',
  idea: 'Keep a min-heap capped at size k holding the k largest values seen so far. Its root — the smallest of that set — is always the k-th largest.',
  complexity: 'add: O(log k) amortized · Space O(k)',
  input: '3;4,5,8,2;3,5,10,9,4', hint: 'k ; initial nums ; values to add',
  code: [
    'class KthLargest:',
    '    def __init__(self, k, nums):',
    '        self.k = k',
    '        self.heap = nums[:]',
    '        heapq.heapify(self.heap)',
    '        while len(self.heap) > k:',
    '            heapq.heappop(self.heap)',
    '',
    '    def add(self, val):',
    '        if len(self.heap) < self.k:',
    '            heapq.heappush(self.heap, val)',
    '        elif val > self.heap[0]:',
    '            heapq.heapreplace(self.heap, val)',
    '        return self.heap[0]',
  ],
  parse(s) {
    const [kStr, initStr, addStr] = avParts(s);
    const k = avNum(kStr, 'k');
    if (!Number.isInteger(k) || k < 1 || k > 8) throw new Error('k must be an integer from 1 to 8');
    const init = String(initStr || '').trim() ? avNums(initStr, 8, 'initial numbers') : [];
    const adds = avNums(addStr, 8, 'values to add');
    return { k, init, adds };
  },
  buildStates({ k, init, adds }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let heap = init.slice();
    domPushState(seq, { line: 4, color: 'default', heap: heap.slice(), k, result: null, adding: null,
      explTitle: 'Copy the input', explText: `Copy nums into the heap array so the caller's list is never mutated.`, pause: true }, ctx);
    hqify(heap);
    domPushState(seq, { line: 5, color: 'blue', heap: heap.slice(), k, result: null, adding: null,
      explTitle: 'Heapify', explText: `heapify rearranges the array in place so every parent is <= its children.` }, ctx);
    while (heap.length > k) {
      const popped = hqPop(heap);
      domPushState(seq, { line: 7, color: 'rose', heap: heap.slice(), k, result: null, adding: null,
        explTitle: 'Trim to size k', explText: `More than k elements — pop the smallest (${popped}) so only the k largest survive.` }, ctx);
    }
    domPushState(seq, { line: 7, color: 'emerald', heap: heap.slice(), k, result: heap[0] ?? null, adding: null,
      explTitle: 'Ready', explText: `Heap now holds the ${k} largest values so far. Root = ${heap[0]} is the current k-th largest.`, pause: true }, ctx);
    adds.forEach(val => {
      if (heap.length < k) {
        domPushState(seq, { line: 10, color: 'blue', heap: heap.slice(), k, result: null, adding: val,
          explTitle: `add(${val})`, explText: `Heap has fewer than k elements — push ${val} straight in.` }, ctx);
        hqPush(heap, val);
        domPushState(seq, { line: 11, color: 'emerald', heap: heap.slice(), k, result: heap[0], adding: null,
          explTitle: 'Pushed', explText: `Heap: [${heap.join(', ')}]. Return heap[0] = ${heap[0]}.` }, ctx);
      } else if (val > heap[0]) {
        domPushState(seq, { line: 12, color: 'amber', heap: heap.slice(), k, result: null, adding: val,
          explTitle: `add(${val})`, explText: `${val} > root ${heap[0]} — it beats the smallest of the top-k, so it gets in.` }, ctx);
        const removed = hqReplace(heap, val);
        domPushState(seq, { line: 13, color: 'emerald', heap: heap.slice(), k, result: heap[0], adding: null,
          explTitle: 'Replaced', explText: `heapreplace popped ${removed} and pushed ${val} in one sift. Return heap[0] = ${heap[0]}.` }, ctx);
      } else {
        domPushState(seq, { line: 12, color: 'rose', heap: heap.slice(), k, result: heap[0], adding: val,
          explTitle: `add(${val})`, explText: `${val} <= root ${heap[0]} — it can never be top-${k}, discard it. Return heap[0] = ${heap[0]}.` }, ctx);
      }
    });
    domPushState(seq, { line: 14, color: 'emerald', heap: heap.slice(), k, result: heap[0], adding: null,
      explTitle: 'Done', explText: `Final k-th largest = ${heap[0]}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Min-heap (size ${s.k})</span>
                      <span style="color:var(--emerald);">${s.result !== null ? `k-th largest = ${s.result}` : (s.adding !== null ? `add(${s.adding})` : '')}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">heap array</div>
                  <div class="array-track">${heapArrayStripHTML(s.heap, { cls: (v, i) => i === 0 ? 'active-k' : '' })}</div>
              </div>
    </div>`;
  }
});

/* ============================================== 002 · Last Stone Weight ==== */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Last Stone Weight', short: 'Last Stone Weight',
  idea: "heapq is min-heap only, so negate every weight — a min-heap of negatives behaves exactly like a max-heap of the real weights, giving the two heaviest stones in O(log n) each.",
  complexity: 'Time O(n log n) · Space O(n)',
  input: '2,7,4,1,8,1', hint: 'stone weights',
  code: [
    'def lastStoneWeight(stones):',
    '    heap = [-w for w in stones]',
    '    heapq.heapify(heap)',
    '    while len(heap) > 1:',
    '        y = -heapq.heappop(heap)',
    '        x = -heapq.heappop(heap)',
    '        if y != x:',
    '            heapq.heappush(heap, -(y - x))',
    '    return -heap[0] if heap else 0',
  ],
  parse(s) {
    const stones = avNums(s, 10, 'stone weights');
    stones.forEach(w => { if (w <= 0 || !Number.isInteger(w)) throw new Error('Stone weights must be positive integers'); });
    return { stones };
  },
  buildStates({ stones }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let heap = stones.map(w => -w);
    domPushState(seq, { line: 2, color: 'default', heap: heap.slice(), y: null, x: null, result: null,
      explTitle: 'Negate', explText: `Negate every weight so the min-heap of negatives IS a max-heap of the real weights.`, pause: true }, ctx);
    hqify(heap);
    domPushState(seq, { line: 3, color: 'blue', heap: heap.slice(), y: null, x: null, result: null,
      explTitle: 'Heapify', explText: `The heaviest stone is now at the root.` }, ctx);
    while (heap.length > 1) {
      const y = -hqPop(heap);
      domPushState(seq, { line: 5, color: 'amber', heap: heap.slice(), y, x: null, result: null,
        explTitle: 'Pop heaviest', explText: `y = ${y}, the current heaviest stone.` }, ctx);
      const x = -hqPop(heap);
      domPushState(seq, { line: 6, color: 'amber', heap: heap.slice(), y, x, result: null,
        explTitle: 'Pop 2nd heaviest', explText: `x = ${x}, the next heaviest stone.` }, ctx);
      if (y !== x) {
        hqPush(heap, -(y - x));
        domPushState(seq, { line: 8, color: 'emerald', heap: heap.slice(), y, x, result: null,
          explTitle: 'Smash', explText: `${y} vs ${x}: the lighter is destroyed, the heavier survives at weight ${y - x}. Push it back.` }, ctx);
      } else {
        domPushState(seq, { line: 7, color: 'rose', heap: heap.slice(), y, x, result: null,
          explTitle: 'Equal — both destroyed', explText: `${y} == ${x}: both stones are destroyed, nothing goes back in.` }, ctx);
      }
    }
    const result = heap.length ? -heap[0] : 0;
    domPushState(seq, { line: 9, color: 'emerald', heap: heap.slice(), y: null, x: null, result,
      explTitle: 'Done', explText: heap.length ? `One stone remains, weight ${result}.` : `No stones remain — return 0.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Max-heap (stone weights)</span>
                      <span style="color:var(--emerald);">${s.result !== null ? `Result = ${s.result}` : (s.y !== null ? `y=${s.y}${s.x !== null ? `, x=${s.x}` : ''}` : '')}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => -v, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
    </div>`;
  }
});

/* ============================================== 003 · K Closest Points ===== */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'K Closest Points to Origin', short: 'K Closest Points',
  idea: 'Max-heap of size k, keyed by NEGATIVE squared distance (never call sqrt — squared distance has the same order). Farthest of the current top-k sits at the root, ready to be evicted.',
  complexity: 'Time O(n log k) · Space O(k)',
  input: '3,3 5,-1 -2,4;2', hint: 'points as "x,y" separated by spaces ; k',
  code: [
    'def kClosest(points, k):',
    '    heap = []',
    '    for i, (x, y) in enumerate(points):',
    '        d2 = x*x + y*y',
    '        if len(heap) < k:',
    '            heapq.heappush(heap, (-d2, i, [x, y]))',
    '        elif -d2 > heap[0][0]:',
    '            heapq.heapreplace(heap, (-d2, i, [x, y]))',
    '    return [pt for _, _, pt in heap]',
  ],
  parse(s) {
    const [ptStr, kStr] = avParts(s);
    const toks = String(ptStr || '').trim().split(/\s+/).filter(Boolean);
    if (!toks.length) throw new Error('Enter at least one point, e.g. "3,3 5,-1"');
    if (toks.length > 7) throw new Error('Use at most 7 points');
    const points = toks.map(t => {
      const m = t.match(/^(-?\d+),(-?\d+)$/);
      if (!m) throw new Error(`"${t}" should look like x,y`);
      return [+m[1], +m[2]];
    });
    const k = avNum(kStr, 'k');
    if (!Number.isInteger(k) || k < 1 || k > points.length) throw new Error(`k must be an integer from 1 to ${points.length}`);
    return { points, k };
  },
  buildStates({ points, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let heap = [];
    const fmt = h => h.map(([nd, i, p]) => [-nd, `#${i}(${p[0]},${p[1]})`]);
    domPushState(seq, { line: 1, color: 'default', heap: [], k, cur: null,
      explTitle: 'Start', explText: `Heap starts empty, capacity ${k}.`, pause: true }, ctx);
    points.forEach(([x, y], i) => {
      const d2 = x * x + y * y;
      domPushState(seq, { line: 4, color: 'blue', heap: fmt(heap), k, cur: { i, x, y, d2 },
        explTitle: `Point #${i} = (${x}, ${y})`, explText: `Squared distance = ${x}² + ${y}² = ${d2}.` }, ctx);
      if (heap.length < k) {
        hqPush(heap, [-d2, i, [x, y]]);
        domPushState(seq, { line: 6, color: 'emerald', heap: fmt(heap), k, cur: { i, x, y, d2 },
          explTitle: 'Heap has room', explText: `Push (${x},${y}) straight in — heap not yet at capacity ${k}.` }, ctx);
      } else if (-d2 > heap[0][0]) {
        domPushState(seq, { line: 7, color: 'amber', heap: fmt(heap), k, cur: { i, x, y, d2 },
          explTitle: 'Closer than the farthest kept point', explText: `d²=${d2} is smaller than the current farthest kept distance ${-heap[0][0]} — evict the root, admit this point.` }, ctx);
        hqReplace(heap, [-d2, i, [x, y]]);
        domPushState(seq, { line: 8, color: 'emerald', heap: fmt(heap), k, cur: { i, x, y, d2 },
          explTitle: 'Replaced', explText: `Farthest point evicted, (${x},${y}) admitted.` }, ctx);
      } else {
        domPushState(seq, { line: 7, color: 'rose', heap: fmt(heap), k, cur: { i, x, y, d2 },
          explTitle: 'Not closer', explText: `d²=${d2} is not smaller than the current farthest kept distance ${-heap[0][0]} — discard (${x},${y}).` }, ctx);
      }
    });
    domPushState(seq, { line: 9, color: 'emerald', heap: fmt(heap), k, cur: null, result: heap.map(([, , p]) => `(${p[0]},${p[1]})`),
      explTitle: 'Done', explText: `The heap now holds exactly the ${k} closest points: ${heap.map(([, , p]) => `(${p[0]},${p[1]})`).join(', ')}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Max-heap (size ${s.k}, by squared distance)</span>
                      <span style="color:var(--accent);">${s.cur ? `examining #${s.cur.i} (${s.cur.x},${s.cur.y}) d²=${s.cur.d2}` : (s.result ? `closest: ${s.result.join(', ')}` : '')}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => v[1], cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
    </div>`;
  }
});

/* ============================================== 004 · Kth Largest in Array = */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Kth Largest Element in an Array', short: 'Kth Largest (Array)',
  idea: 'Min-heap of size k holding the k largest elements seen so far; heap[0] is always the smallest of that set — the k-th largest overall.',
  complexity: 'Time O(n log k) · Space O(k)',
  input: '3,2,1,5,6,4;2', hint: 'nums ; k',
  code: [
    'def findKthLargest(nums, k):',
    '    heap = nums[:k]',
    '    heapq.heapify(heap)',
    '    for x in nums[k:]:',
    '        if x > heap[0]:',
    '            heapq.heapreplace(heap, x)',
    '    return heap[0]',
  ],
  parse(s) {
    const [numStr, kStr] = avParts(s);
    const nums = avNums(numStr, 10, 'numbers');
    const k = avNum(kStr, 'k');
    if (!Number.isInteger(k) || k < 1 || k > nums.length) throw new Error(`k must be an integer from 1 to ${nums.length}`);
    return { nums, k };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let heap = nums.slice(0, k);
    domPushState(seq, { line: 2, color: 'default', heap: heap.slice(), k, cur: null,
      explTitle: 'Seed the heap', explText: `Take the first k=${k} numbers as a starting heap.`, pause: true }, ctx);
    hqify(heap);
    domPushState(seq, { line: 3, color: 'blue', heap: heap.slice(), k, cur: null,
      explTitle: 'Heapify', explText: `Heapify in O(k): heap[0] = ${heap[0]} is the smallest of the first k.` }, ctx);
    nums.slice(k).forEach(x => {
      domPushState(seq, { line: 4, color: 'blue', heap: heap.slice(), k, cur: x,
        explTitle: `Next: ${x}`, explText: `Compare ${x} against the current root ${heap[0]}.` }, ctx);
      if (x > heap[0]) {
        domPushState(seq, { line: 5, color: 'amber', heap: heap.slice(), k, cur: x,
          explTitle: 'Bigger than the root', explText: `${x} > ${heap[0]} — it belongs in the top-${k}.` }, ctx);
        hqReplace(heap, x);
        domPushState(seq, { line: 6, color: 'emerald', heap: heap.slice(), k, cur: null,
          explTitle: 'Replaced', explText: `heapreplace popped the old root and pushed ${x} in one sift. New root: ${heap[0]}.` }, ctx);
      } else {
        domPushState(seq, { line: 5, color: 'rose', heap: heap.slice(), k, cur: x,
          explTitle: 'Not bigger', explText: `${x} <= ${heap[0]} — it can never be in the top-${k}, discard in O(1).` }, ctx);
      }
    });
    domPushState(seq, { line: 7, color: 'emerald', heap: heap.slice(), k, cur: null, result: heap[0],
      explTitle: 'Done', explText: `heap[0] = ${heap[0]} is the ${k}-th largest element.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Min-heap (size ${s.k})</span>
                      <span style="color:var(--emerald);">${s.result !== undefined ? `k-th largest = ${s.result}` : (s.cur !== null ? `examining ${s.cur}` : '')}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">heap array</div>
                  <div class="array-track">${heapArrayStripHTML(s.heap, { cls: (v, i) => i === 0 ? 'active-k' : '' })}</div>
              </div>
    </div>`;
  }
});

/* ============================================== 005 · Task Scheduler ======= */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Task Scheduler', short: 'Task Scheduler',
  idea: 'Always run whichever available task currently has the most remaining occurrences (max-heap of counts). Just-run tasks sit in a cooldown queue for n ticks before re-entering the heap.',
  complexity: 'Time O(total_time) with a tiny log-26 constant · Space O(26)',
  input: 'AAABBB;2', hint: 'task letters (A-Z) ; cooldown n',
  code: [
    'counts = Counter(tasks)',
    'heap = [-c for c in counts.values()]',
    'heapq.heapify(heap)',
    'elapsed, cooldown = 0, deque()',
    'while heap or cooldown:',
    '    elapsed += 1',
    '    if heap:',
    '        remaining = -heapq.heappop(heap) - 1',
    '        if remaining > 0:',
    '            cooldown.append((elapsed + n, -remaining))',
    '    if cooldown and cooldown[0][0] == elapsed:',
    '        heapq.heappush(heap, cooldown.popleft()[1])',
    'return elapsed',
  ],
  parse(s) {
    const [taskStr, nStr] = avParts(s);
    const tasks = String(taskStr || '').toUpperCase().replace(/[^A-Z]/g, '');
    if (!tasks.length) throw new Error('Enter task letters, e.g. AAABBB');
    if (tasks.length > 12) throw new Error('Use at most 12 tasks so the timeline stays short');
    const n = avNum(nStr, 'n');
    if (!Number.isInteger(n) || n < 0 || n > 5) throw new Error('n (cooldown) must be an integer from 0 to 5');
    return { tasks: [...tasks], n };
  },
  buildStates({ tasks, n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const counts = new Map();
    tasks.forEach(t => counts.set(t, (counts.get(t) || 0) + 1));
    let heap = [...counts.values()].map(c => -c);
    hqify(heap);
    domPushState(seq, { line: 3, color: 'default', heap: heap.slice(), cooldown: [], elapsed: 0,
      explTitle: 'Count and heapify', explText: `Counts: ${[...counts.entries()].map(([c, v]) => `${c}=${v}`).join(', ')}. Negate into a max-heap.`, pause: true }, ctx);
    let elapsed = 0;
    const cooldown = [];
    while (heap.length || cooldown.length) {
      elapsed++;
      if (heap.length) {
        const remaining = -hqPop(heap) - 1;
        domPushState(seq, { line: 8, color: 'amber', heap: heap.slice(), cooldown: cooldown.map(([r, c]) => [r, -c]), elapsed,
          explTitle: `Tick ${elapsed}: run a task`, explText: `Pop the most frequent remaining task and run it. ${remaining} occurrence(s) left of it.` }, ctx);
        if (remaining > 0) {
          cooldown.push([elapsed + n, -remaining]);
          domPushState(seq, { line: 10, color: 'blue', heap: heap.slice(), cooldown: cooldown.map(([r, c]) => [r, -c]), elapsed,
            explTitle: 'Bench it', explText: `It still has ${remaining} left — bench it until tick ${elapsed + n}, exactly n=${n} ticks away.` }, ctx);
        }
      } else {
        domPushState(seq, { line: 6, color: 'rose', heap: heap.slice(), cooldown: cooldown.map(([r, c]) => [r, -c]), elapsed,
          explTitle: `Tick ${elapsed}: idle`, explText: `Nothing available right now — the CPU sits idle this tick.` }, ctx);
      }
      if (cooldown.length && cooldown[0][0] === elapsed) {
        const [, negRemaining] = cooldown.shift();
        hqPush(heap, negRemaining);
        domPushState(seq, { line: 12, color: 'emerald', heap: heap.slice(), cooldown: cooldown.map(([r, c]) => [r, -c]), elapsed,
          explTitle: 'Cooldown over', explText: `A benched task's cooldown just ended — it re-enters the heap.` }, ctx);
      }
    }
    domPushState(seq, { line: 13, color: 'emerald', heap: [], cooldown: [], elapsed, result: elapsed,
      explTitle: 'Done', explText: `Total ticks elapsed = ${elapsed}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Max-heap (remaining counts)</span>
                      <span style="color:var(--accent);">elapsed = ${s.elapsed}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => -v, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">cooldown queue (ready-tick : remaining)</div>
                  ${chipRow(s.cooldown.map(([r, c]) => `@${r}: ${c} left`))}
              </div>
    </div>`;
  }
});

/* ============================================== 006 · Design Twitter ======= */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Design Twitter', short: 'Design Twitter',
  idea: 'getNewsFeed is a k-way merge: take the tail of every followee’s tweet list, then heapq.nlargest picks the top 10 by timestamp — a size-10 max-heap sweep under the hood.',
  complexity: 'postTweet/follow/unfollow O(1) amortized · getNewsFeed O(F log 10)',
  input: 'post 1 5, follow 1 2, post 2 6, feed 1, unfollow 1 2, feed 1', hint: 'ops: post u t | follow a b | unfollow a b | feed u',
  code: [
    'def postTweet(u, tid):',
    '    tweets[u].append((clock, tid)); clock += 1',
    'def follow(a, b): follows[a].add(b)',
    'def unfollow(a, b): follows[a].discard(b)',
    'def getNewsFeed(u):',
    '    users = follows[u] | {u}',
    '    cand = [t for uid in users for t in tweets[uid][-10:]]',
    '    top = heapq.nlargest(10, cand, key=lambda t: t[0])',
    '    return [tid for _, tid in top]',
  ],
  parse(s) {
    const ops = String(s || '').split(',').map(x => x.trim()).filter(Boolean);
    if (!ops.length) throw new Error('Enter at least one operation');
    if (ops.length > 10) throw new Error('Use at most 10 operations');
    const parsed = ops.map(op => {
      const t = op.split(/\s+/);
      if (t[0] === 'post' && t.length === 3) return { op: 'post', u: +t[1], tid: +t[2] };
      if (t[0] === 'follow' && t.length === 3) return { op: 'follow', a: +t[1], b: +t[2] };
      if (t[0] === 'unfollow' && t.length === 3) return { op: 'unfollow', a: +t[1], b: +t[2] };
      if (t[0] === 'feed' && t.length === 2) return { op: 'feed', u: +t[1] };
      throw new Error(`"${op}" — use "post u t", "follow a b", "unfollow a b" or "feed u"`);
    });
    return { ops: parsed };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const FEED = 10;
    const tweets = new Map(), follows = new Map();
    let clock = 0;
    const tw = u => tweets.get(u) || [];
    domPushState(seq, { line: 1, color: 'default', tweets: new Map(), follows: new Map(), feed: null, op: null,
      explTitle: 'Start', explText: `No tweets, no follows yet.`, pause: true }, ctx);
    ops.forEach(o => {
      if (o.op === 'post') {
        if (!tweets.has(o.u)) tweets.set(o.u, []);
        tweets.get(o.u).push([clock, o.tid]);
        clock++;
        domPushState(seq, { line: 2, color: 'blue', tweets: new Map(tweets), follows: new Map(follows), feed: null,
          op: `post(${o.u}, ${o.tid})`, explTitle: `User ${o.u} tweets`, explText: `Tweet ${o.tid} appended to user ${o.u}'s list with timestamp ${clock - 1}.` }, ctx);
      } else if (o.op === 'follow') {
        if (!follows.has(o.a)) follows.set(o.a, new Set());
        follows.get(o.a).add(o.b);
        domPushState(seq, { line: 3, color: 'blue', tweets: new Map(tweets), follows: new Map(follows), feed: null,
          op: `follow(${o.a}, ${o.b})`, explTitle: `User ${o.a} follows ${o.b}`, explText: `${o.a}'s follow set now includes ${o.b}.` }, ctx);
      } else if (o.op === 'unfollow') {
        follows.get(o.a)?.delete(o.b);
        domPushState(seq, { line: 4, color: 'rose', tweets: new Map(tweets), follows: new Map(follows), feed: null,
          op: `unfollow(${o.a}, ${o.b})`, explTitle: `User ${o.a} unfollows ${o.b}`, explText: `${o.a} no longer follows ${o.b}.` }, ctx);
      } else {
        const users = new Set([...(follows.get(o.u) || []), o.u]);
        const cand = [];
        users.forEach(uid => cand.push(...tw(uid).slice(-FEED)));
        domPushState(seq, { line: 7, color: 'amber', tweets: new Map(tweets), follows: new Map(follows), feed: null,
          op: `feed(${o.u})`, explTitle: 'Gather candidates', explText: `Take the last ${FEED} tweets from ${o.u} and each followee: ${cand.length} candidate tweet(s).` }, ctx);
        const top = [...cand].sort((a, b) => b[0] - a[0]).slice(0, FEED).map(t => t[1]);
        domPushState(seq, { line: 8, color: 'emerald', tweets: new Map(tweets), follows: new Map(follows), feed: top,
          op: `feed(${o.u})`, explTitle: 'nlargest by timestamp', explText: `heapq.nlargest keeps only the newest ${FEED}: [${top.join(', ')}].`, pause: true }, ctx);
      }
    });
    return seq;
  },
  renderDOM(container, s, spec) {
    const users = [...s.tweets.keys()].sort((a, b) => a - b);
    const rows = users.map(u => `
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:6px;">
        <div style="width:70px; font-weight:bold; color:var(--text-dim);">user ${u}</div>
        ${chipRow(s.tweets.get(u).map(([, tid]) => tid))}
      </div>`).join('') || `<div style="color:var(--text-dim); padding:8px;">(no tweets yet)</div>`;
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Tweets by user</span><span style="color:var(--accent);">${s.op || ''}</span>
                  </div>
                  ${rows}
              </div>
              ${s.feed ? `<div class="glass-panel arrays-container">
                  <div class="panel-heading">news feed (newest first)</div>
                  ${chipRow(s.feed, { cls: () => 'active-k' })}
              </div>` : ''}
    </div>`;
  }
});

/* ============================================== 007 · Reorganize String ==== */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Reorganize String', short: 'Reorganize String',
  idea: "Task Scheduler with cooldown fixed at 1: always place the currently most frequent character, then bench it for exactly one slot so it can't repeat immediately.",
  complexity: 'Time O(n log 26) · Space O(26 + n)',
  input: 'aab', hint: 'a lowercase string',
  code: [
    'counts = Counter(s)',
    'if max(counts.values()) > (len(s)+1)//2: return ""',
    'heap = [(-c, ch) for ch, c in counts.items()]',
    'heapq.heapify(heap)',
    'result, prev_count, prev_char = [], 0, ""',
    'while heap:',
    '    count, ch = heapq.heappop(heap)',
    '    result.append(ch); count += 1',
    '    if prev_count < 0:',
    '        heapq.heappush(heap, (prev_count, prev_char))',
    '    prev_count, prev_char = count, ch',
    'return "".join(result)',
  ],
  parse(s) {
    const str = String(s || '').toLowerCase().replace(/[^a-z]/g, '');
    if (!str.length) throw new Error('Enter a lowercase string, e.g. aab');
    if (str.length > 12) throw new Error('Use at most 12 characters');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const counts = new Map();
    [...str].forEach(c => counts.set(c, (counts.get(c) || 0) + 1));
    const maxCount = Math.max(...counts.values());
    if (maxCount > Math.ceil(str.length / 2)) {
      domPushState(seq, { line: 2, color: 'rose', heap: [], result: '', str,
        explTitle: 'Infeasible', explText: `The most frequent character appears ${maxCount} times, more than half of ${str.length} characters allow — return "".`, pause: true }, ctx);
      return seq;
    }
    let heap = [...counts.entries()].map(([ch, c]) => [-c, ch]);
    hqify(heap);
    domPushState(seq, { line: 4, color: 'default', heap: heap.slice(), result: '', str,
      explTitle: 'Heapify by count', explText: `Counts: ${[...counts.entries()].map(([c, v]) => `${c}=${v}`).join(', ')}.`, pause: true }, ctx);
    let result = [], prevCount = 0, prevChar = '';
    while (heap.length) {
      let [count, ch] = hqPop(heap);
      domPushState(seq, { line: 7, color: 'amber', heap: heap.slice(), result: result.join(''), str, placing: ch,
        explTitle: `Place '${ch}'`, explText: `Most frequent remaining character is '${ch}' (${-count} left).` }, ctx);
      result.push(ch);
      count += 1;
      if (prevCount < 0) {
        hqPush(heap, [prevCount, prevChar]);
        domPushState(seq, { line: 10, color: 'blue', heap: heap.slice(), result: result.join(''), str, placing: null,
          explTitle: 'Un-bench previous', explText: `The previously benched '${prevChar}' still has ${-prevCount} left — it re-enters the heap now.` }, ctx);
      }
      prevCount = count; prevChar = ch;
      domPushState(seq, { line: 11, color: 'emerald', heap: heap.slice(), result: result.join(''), str, placing: null,
        explTitle: 'Bench', explText: `'${ch}' is benched for one slot (won't be eligible next round) with ${-count} left.` }, ctx);
    }
    domPushState(seq, { line: 12, color: 'emerald', heap: [], result: result.join(''), str, placing: null,
      explTitle: 'Done', explText: `Result: "${result.join('')}" — no two adjacent characters are equal.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Max-heap (count, char)</span>
                      <span style="color:var(--accent);">${s.placing ? `placing '${s.placing}'` : ''}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => `${v[1]}:${-v[0]}`, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">result</div>
                  <div class="array-track">${heapArrayStripHTML([...s.result], { cls: () => 'merged' })}</div>
              </div>
    </div>`;
  }
});

/* ============================================== 008 · Single-Threaded CPU == */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Single-Threaded CPU', short: 'Single-Threaded CPU',
  idea: 'Sort tasks by enqueue time and sweep a pointer forward; maintain a min-heap of (processingTime, index) for everyone currently available. When idle, jump the clock to the next enqueue time instead of ticking.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '1,2 2,4 3,2 4,1', hint: '"enqueueTime,processingTime" pairs',
  code: [
    'order = sorted(range(n), key=lambda i: tasks[i][0])',
    'result, heap, clock, i = [], [], 0, 0',
    'while len(result) < n:',
    '    while i < n and tasks[order[i]][0] <= clock:',
    '        heapq.heappush(heap, (tasks[order[i]][1], order[i])); i += 1',
    '    if not heap:',
    '        clock = tasks[order[i]][0]; continue',
    '    proc, idx = heapq.heappop(heap)',
    '    result.append(idx); clock += proc',
    'return result',
  ],
  parse(s) {
    const toks = String(s || '').trim().split(/\s+/).filter(Boolean);
    if (!toks.length) throw new Error('Enter tasks as "enqueue,processing" pairs');
    if (toks.length > 8) throw new Error('Use at most 8 tasks');
    const tasks = toks.map(t => {
      const m = t.match(/^(\d+),(\d+)$/);
      if (!m) throw new Error(`"${t}" should look like enqueueTime,processingTime`);
      return [+m[1], +m[2]];
    });
    return { tasks };
  },
  buildStates({ tasks }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = tasks.length;
    const order = [...tasks.keys()].sort((a, b) => tasks[a][0] - tasks[b][0]);
    domPushState(seq, { line: 1, color: 'default', heap: [], result: [], clock: 0, i: 0,
      explTitle: 'Sort by enqueue time', explText: `Processing order by enqueueTime: [${order.join(', ')}].`, pause: true }, ctx);
    let heap = [], clock = 0, i = 0, result = [];
    while (result.length < n) {
      while (i < n && tasks[order[i]][0] <= clock) {
        const idx = order[i];
        hqPush(heap, [tasks[idx][1], idx]);
        domPushState(seq, { line: 5, color: 'blue', heap: heap.slice(), result: result.slice(), clock, i,
          explTitle: `Task #${idx} becomes available`, explText: `enqueueTime ${tasks[idx][0]} <= clock ${clock} — push (processing=${tasks[idx][1]}, idx=${idx}).` }, ctx);
        i++;
      }
      if (!heap.length) {
        const jump = tasks[order[i]][0];
        domPushState(seq, { line: 7, color: 'rose', heap: [], result: result.slice(), clock, i,
          explTitle: 'CPU idle', explText: `Nothing available yet — jump the clock from ${clock} straight to ${jump}.` }, ctx);
        clock = jump;
        continue;
      }
      const [proc, idx] = hqPop(heap);
      result.push(idx);
      domPushState(seq, { line: 9, color: 'amber', heap: heap.slice(), result: result.slice(), clock,
        explTitle: `Run task #${idx}`, explText: `Shortest available processing time = ${proc}. Clock advances to ${clock + proc}.` }, ctx);
      clock += proc;
    }
    domPushState(seq, { line: 10, color: 'emerald', heap: [], result: result.slice(), clock,
      explTitle: 'Done', explText: `Execution order: [${result.join(', ')}].`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Min-heap of available tasks (proc, idx)</span>
                      <span style="color:var(--accent);">clock = ${s.clock}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => `#${v[1]}:${v[0]}`, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">execution order</div>
                  ${chipRow(s.result.map(idx => `#${idx}`), { cls: () => 'merged' })}
              </div>
    </div>`;
  }
});

/* ============================================== 009 · Median from Stream === */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Find Median from Data Stream', short: 'Median from Stream',
  idea: 'Split the stream across two heaps that always straddle the median: lo (max-heap) holds the smaller half, hi (min-heap) the larger half, kept within one of each other in size.',
  complexity: 'addNum O(log n) · findMedian O(1)',
  input: '1,2,3,4,5', hint: 'numbers to add, one per step',
  code: [
    'lo, hi = [], []   # lo: max-heap (negated); hi: min-heap',
    'def addNum(num):',
    '    heapq.heappush(lo, -heapq.heappushpop(hi, num))',
    '    if len(lo) > len(hi) + 1:',
    '        heapq.heappush(hi, -heapq.heappop(lo))',
    'def findMedian():',
    '    if len(lo) > len(hi): return -lo[0]',
    '    return (-lo[0] + hi[0]) / 2',
  ],
  parse(s) {
    const nums = avNums(s, 10, 'numbers');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let lo = [], hi = [];
    domPushState(seq, { line: 1, color: 'default', lo: [], hi: [], median: null, cur: null,
      explTitle: 'Start', explText: `Both heaps empty.`, pause: true }, ctx);
    nums.forEach(num => {
      domPushState(seq, { line: 3, color: 'blue', lo: lo.slice(), hi: hi.slice(), median: null, cur: num,
        explTitle: `addNum(${num})`, explText: `Route ${num} through hi first via heappushpop, then move hi's new minimum into lo.` }, ctx);
      const moved = -hqPushPop(hi, num);
      hqPush(lo, moved);
      domPushState(seq, { line: 3, color: 'emerald', lo: lo.slice(), hi: hi.slice(), median: null, cur: null,
        explTitle: 'Moved across the boundary', explText: `${moved * -1} moved into lo (negated to ${moved}). Every value in lo is now <= every value in hi.` }, ctx);
      if (lo.length > hi.length + 1) {
        const moved2 = -hqPop(lo);
        hqPush(hi, moved2);
        domPushState(seq, { line: 5, color: 'amber', lo: lo.slice(), hi: hi.slice(), median: null, cur: null,
          explTitle: 'Rebalance', explText: `lo grew more than one bigger than hi — move lo's max (${moved2}) back to hi.` }, ctx);
      }
      const median = lo.length > hi.length ? -lo[0] : (-lo[0] + hi[0]) / 2;
      domPushState(seq, { line: 7, color: 'emerald', lo: lo.slice(), hi: hi.slice(), median, cur: null,
        explTitle: 'findMedian', explText: `sizes lo=${lo.length}, hi=${hi.length} → median = ${median}.`, pause: true }, ctx);
    });
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div style="display:flex; gap:15px; flex-wrap:wrap;">
                  <div class="glass-panel arrays-container" style="flex:1; min-width:200px;">
                      <div class="panel-heading">lo — max-heap (lower half)</div>
                      ${heapTreeHTML(s.lo, { label: v => -v, width: 220 })}
                  </div>
                  <div class="glass-panel arrays-container" style="flex:1; min-width:200px;">
                      <div class="panel-heading">hi — min-heap (upper half)</div>
                      ${heapTreeHTML(s.hi, { width: 220 })}
                  </div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>${s.cur !== null ? `adding ${s.cur}` : 'median'}</span>
                      <span style="color:var(--emerald);">${s.median !== null ? s.median : ''}</span>
                  </div>
              </div>
    </div>`;
  }
});

/* ============================================== 010 · Min Interval to Include Each Query */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Minimum Interval to Include Each Query', short: 'Min Interval / Query',
  idea: 'Sweep queries in ascending order. Admit newly-eligible intervals into a min-heap keyed by size, and lazily pop intervals whose right end has already expired — the surviving root is the answer.',
  complexity: 'Time O((n + q) log n) · Space O(n + q)',
  input: '1,4 2,4 3,6 4,4;2,3,4,5', hint: '"left,right" intervals ; queries',
  code: [
    'ivs = sorted(intervals, key=lambda iv: iv[0])',
    'order = sorted(range(len(q)), key=lambda i: q[i])',
    'ans, heap, i = [-1]*len(q), [], 0',
    'for qi in order:',
    '    v = q[qi]',
    '    while i < len(ivs) and ivs[i][0] <= v:',
    '        l, r = ivs[i]; heapq.heappush(heap, (r-l+1, r)); i += 1',
    '    while heap and heap[0][1] < v:',
    '        heapq.heappop(heap)',
    '    if heap: ans[qi] = heap[0][0]',
    'return ans',
  ],
  parse(s) {
    const [ivStr, qStr] = avParts(s);
    const ivToks = String(ivStr || '').trim().split(/\s+/).filter(Boolean);
    if (!ivToks.length) throw new Error('Enter intervals as "left,right" pairs');
    if (ivToks.length > 6) throw new Error('Use at most 6 intervals');
    const intervals = ivToks.map(t => {
      const m = t.match(/^(\d+),(\d+)$/);
      if (!m) throw new Error(`"${t}" should look like left,right`);
      if (+m[1] > +m[2]) throw new Error(`"${t}": left must be <= right`);
      return [+m[1], +m[2]];
    });
    const queries = avNums(qStr, 6, 'queries');
    return { intervals, queries };
  },
  buildStates({ intervals, queries }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const ivs = [...intervals].sort((a, b) => a[0] - b[0]);
    const order = [...queries.keys()].sort((a, b) => queries[a] - queries[b]);
    const answers = queries.map(() => -1);
    domPushState(seq, { line: 1, color: 'default', heap: [], answers: answers.slice(), q: null,
      explTitle: 'Sort both', explText: `Intervals sorted by left; queries answered in ascending order [${order.map(i => queries[i]).join(', ')}].`, pause: true }, ctx);
    let heap = [], i = 0;
    order.forEach(qi => {
      const v = queries[qi];
      while (i < ivs.length && ivs[i][0] <= v) {
        const [l, r] = ivs[i];
        hqPush(heap, [r - l + 1, r]);
        domPushState(seq, { line: 7, color: 'blue', heap: heap.slice(), answers: answers.slice(), q: v,
          explTitle: `Admit [${l},${r}]`, explText: `left ${l} <= query ${v} — this interval (size ${r - l + 1}) is now active.` }, ctx);
        i++;
      }
      while (heap.length && heap[0][1] < v) {
        const expired = hqPop(heap);
        domPushState(seq, { line: 9, color: 'rose', heap: heap.slice(), answers: answers.slice(), q: v,
          explTitle: 'Expire', explText: `Interval with right end ${expired[1]} < query ${v} can never contain this or any larger query — discard it.` }, ctx);
      }
      if (heap.length) answers[qi] = heap[0][0];
      domPushState(seq, { line: 10, color: 'emerald', heap: heap.slice(), answers: answers.slice(), q: v,
        explTitle: `Answer for query ${v}`, explText: heap.length ? `Smallest surviving active interval has size ${heap[0][0]}.` : `No active interval contains ${v} — answer -1.`, pause: true }, ctx);
    });
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Min-heap of active intervals (size, right)</span>
                      <span style="color:var(--accent);">${s.q !== null ? `query = ${s.q}` : ''}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => `${v[0]}|r${v[1]}`, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">answers so far</div>
                  ${chipRow(s.answers, { cls: v => v === -1 ? '' : 'merged' })}
              </div>
    </div>`;
  }
});

/* ============================================== 011 · IPO =================== */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'IPO', short: 'IPO',
  idea: 'Capital only grows, so sweep projects sorted by required capital and push newly-affordable profits into a max-heap; each round take the best affordable profit.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '2;0;1,2,3;0,1,1', hint: 'k ; initial capital w ; profits ; capital requirements',
  code: [
    'projects = sorted(zip(capital, profits))',
    'heap, i = [], 0',
    'for _ in range(k):',
    '    while i < n and projects[i][0] <= w:',
    '        heapq.heappush(heap, -projects[i][1]); i += 1',
    '    if not heap:',
    '        break',
    '    w -= heapq.heappop(heap)',
    'return w',
  ],
  parse(s) {
    const [kStr, wStr, pStr, cStr] = avParts(s);
    const k = avNum(kStr, 'k');
    const w = avNum(wStr, 'w');
    const profits = avNums(pStr, 8, 'profits');
    const capital = avNums(cStr, 8, 'capital requirements');
    if (profits.length !== capital.length) throw new Error('profits and capital must have the same length');
    if (!Number.isInteger(k) || k < 1 || k > profits.length) throw new Error(`k must be an integer from 1 to ${profits.length}`);
    return { k, w, profits, capital };
  },
  buildStates({ k, w, profits, capital }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const projects = profits.map((p, idx) => [capital[idx], p]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    domPushState(seq, { line: 1, color: 'default', heap: [], w, round: 0, k,
      explTitle: 'Sort by capital', explText: `Projects sorted by required capital: ${projects.map(([c, p]) => `(cap ${c}, profit ${p})`).join(', ')}.`, pause: true }, ctx);
    let heap = [], i = 0;
    for (let round = 1; round <= k; round++) {
      while (i < projects.length && projects[i][0] <= w) {
        const [, profit] = projects[i];
        hqPush(heap, -profit);
        domPushState(seq, { line: 5, color: 'blue', heap: heap.slice(), w, round, k,
          explTitle: `Round ${round}: newly affordable`, explText: `capital ${projects[i][0]} <= w=${w} — profit ${profit} becomes available.` }, ctx);
        i++;
      }
      if (!heap.length) {
        domPushState(seq, { line: 7, color: 'rose', heap: [], w, round, k,
          explTitle: 'Nothing affordable', explText: `No project is affordable at w=${w} — capital can never grow further. Stop early.`, pause: true }, ctx);
        break;
      }
      const best = -hqPop(heap);
      w += best;
      domPushState(seq, { line: 8, color: 'emerald', heap: heap.slice(), w, round, k,
        explTitle: `Round ${round}: take the best`, explText: `Pop the largest affordable profit (${best}). Capital grows to ${w}.` }, ctx);
    }
    domPushState(seq, { line: 9, color: 'emerald', heap: heap.slice(), w, round: k, k, result: w,
      explTitle: 'Done', explText: `Final maximized capital = ${w}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Max-heap of affordable profits</span>
                      <span style="color:var(--emerald);">w = ${s.w}${s.round ? ` (round ${s.round}/${s.k})` : ''}</span>
                  </div>
                  ${heapTreeHTML(s.heap, { label: v => -v, cls: (v, i) => i === 0 ? 'active-k' : '' })}
              </div>
    </div>`;
  }
});

/* ============================================== 012 · Sliding Window Median  */
defineAlgoDom('12_heap_priority_queue', {
  type: 'dom',
  title: 'Sliding Window Median', short: 'Sliding Window Median',
  idea: 'Two heaps (small/large) straddling the window median, plus LAZY DELETION: an outgoing value is just marked delayed and physically removed only once it reaches a heap top.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '1,3,-1,-3,5;3', hint: 'nums ; window size k',
  code: [
    'def insert(x):',
    '    if not small or x <= -small[0]: heappush(small, -x)',
    '    else: heappush(large, x)',
    '    balance()',
    'def erase(x):',
    '    delayed[x] += 1',
    '    prune the top of whichever heap x lives in',
    '    balance()',
    'def median():',
    '    return -small[0] if k odd else (-small[0]+large[0])/2',
  ],
  parse(s) {
    const [numStr, kStr] = avParts(s);
    const nums = avNums(numStr, 9, 'numbers');
    const k = avNum(kStr, 'k');
    if (!Number.isInteger(k) || k < 1 || k > nums.length) throw new Error(`k must be an integer from 1 to ${nums.length}`);
    return { nums, k };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const dh = dhMake(k);
    const fmtDelayed = () => [...dh.delayed.entries()].filter(([, c]) => c > 0).map(([v, c]) => `${v}×${c}`);
    domPushState(seq, { line: 1, color: 'default', small: [], large: [], delayed: [], median: null, window: [], cur: null,
      explTitle: 'Start', explText: `Build the first window of size k=${k}.`, pause: true }, ctx);
    nums.slice(0, k).forEach(x => {
      dhInsert(dh, x);
      domPushState(seq, { line: 2, color: 'blue', small: hqClone(dh.small), large: hqClone(dh.large), delayed: fmtDelayed(),
        median: null, window: nums.slice(0, k).slice(0, nums.indexOf(x) + 1), cur: x,
        explTitle: `insert(${x})`, explText: `Route ${x} to small or large by comparing against small's top, then rebalance.` }, ctx);
    });
    let out = [dhMedian(dh)];
    domPushState(seq, { line: 9, color: 'emerald', small: hqClone(dh.small), large: hqClone(dh.large), delayed: fmtDelayed(),
      median: out[0], window: nums.slice(0, k), cur: null,
      explTitle: 'First median', explText: `Window [${nums.slice(0, k).join(', ')}] → median = ${out[0]}.`, pause: true }, ctx);
    for (let i = k; i < nums.length; i++) {
      dhInsert(dh, nums[i]);
      domPushState(seq, { line: 2, color: 'blue', small: hqClone(dh.small), large: hqClone(dh.large), delayed: fmtDelayed(),
        median: null, window: nums.slice(i - k + 1, i + 1), cur: nums[i],
        explTitle: `insert(${nums[i]})`, explText: `${nums[i]} enters the window.` }, ctx);
      dhErase(dh, nums[i - k]);
      domPushState(seq, { line: 6, color: 'rose', small: hqClone(dh.small), large: hqClone(dh.large), delayed: fmtDelayed(),
        median: null, window: nums.slice(i - k + 1, i + 1), cur: null,
        explTitle: `erase(${nums[i - k]})`, explText: `${nums[i - k]} leaves the window — mark it delayed rather than searching the heap for it.` }, ctx);
      const med = dhMedian(dh);
      out.push(med);
      domPushState(seq, { line: 10, color: 'emerald', small: hqClone(dh.small), large: hqClone(dh.large), delayed: fmtDelayed(),
        median: med, window: nums.slice(i - k + 1, i + 1), cur: null,
        explTitle: 'Median', explText: `Window [${nums.slice(i - k + 1, i + 1).join(', ')}] → median = ${med}.`, pause: true }, ctx);
    }
    return seq;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">current window</div>
                  <div class="array-track">${heapArrayStripHTML(s.window, { cls: (v) => v === s.cur ? 'active-k' : '' })}</div>
              </div>
              <div style="display:flex; gap:15px; flex-wrap:wrap;">
                  <div class="glass-panel arrays-container" style="flex:1; min-width:200px;">
                      <div class="panel-heading">small — max-heap</div>
                      ${heapTreeHTML(s.small, { label: v => -v, width: 220 })}
                  </div>
                  <div class="glass-panel arrays-container" style="flex:1; min-width:200px;">
                      <div class="panel-heading">large — min-heap</div>
                      ${heapTreeHTML(s.large, { width: 220 })}
                  </div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>delayed (marked for removal): ${s.delayed.length ? s.delayed.join(', ') : '(none)'}</span>
                      <span style="color:var(--emerald);">${s.median !== null ? `median = ${s.median}` : ''}</span>
                  </div>
              </div>
    </div>`;
  }
});
