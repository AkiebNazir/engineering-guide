/* ============================================================================
   Visualizations for 05_binary_search — the 8 problems that had no exact
   animation (005, 006, 007, 008, 009, 010, 011, 012). Problems 001 (Binary
   Search), 002 (Search Insert Position), 003 (First Bad Version) and 004
   (Guess Number Higher or Lower) already had DOM-engine specs elsewhere —
   left untouched.
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
/* A horizontal array of boxes with l/r/mid pointers and optional per-index
   dimming / highlight coloring. `style(idx, v)` -> {cls, dim, pointerLabel}. */
function bsArrayHTML(arr, style) {
  return arr.map((v, idx) => {
    const st = style(idx, v) || {};
    return `
    <div class="array-node ${st.cls || ''}" style="${st.dim ? 'opacity:0.3' : ''}">
        ${st.pointer || ''}
        ${v}
        <div class="node-index">${idx}</div>
    </div>`;
  }).join('');
}
function bsPointerHTML(label, color) {
  return `<div class="pointer" style="color:${color}">↓ ${label}</div>`;
}

/* ============================================= 005 · Search a 2D Matrix == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Search a 2D Matrix', short: 'Search a 2D Matrix',
  idea: 'Each row is sorted and the first value of every row is greater than the last value of the row before it — so the whole grid, read row by row, is really one sorted array. Binary search over the flattened index `mid`, then map it back to `(row, col) = divmod(mid, cols)`.',
  complexity: 'Time O(log(rows·cols)) · Space O(1)',
  input: '1,3,5,7|10,11,16,20|23,30,34,60 ; 3', hint: 'rows separated by "|", cells by "," ; target',
  code: [
    'def searchMatrix(matrix, target):',
    '    rows, cols = len(matrix), len(matrix[0])',
    '    lo, hi = 0, rows * cols - 1',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        r, c = divmod(mid, cols)',
    '        val = matrix[r][c]',
    '        if val == target:',
    '            return True',
    '        elif val < target:',
    '            lo = mid + 1',
    '        else:',
    '            hi = mid - 1',
    '    return False',
  ],
  parse(s) {
    const [gridStr, t] = String(s || '').split(';').map(x => (x || '').trim());
    if (!gridStr) throw new Error('Enter a matrix and a target, e.g. "1,3,5,7|10,11,16,20 ; 3"');
    const rows = gridStr.split('|').map(r => r.trim()).filter(Boolean);
    if (!rows.length) throw new Error('Enter at least one row');
    if (rows.length > 6) throw new Error('Keep to at most 6 rows for visualization');
    const matrix = rows.map(r => r.split(',').map(x => {
      const n = Number(x.trim());
      if (!Number.isFinite(n)) throw new Error(`"${x}" is not a number`);
      return n;
    }));
    const cols = matrix[0].length;
    if (matrix.some(r => r.length !== cols)) throw new Error('Every row must have the same length');
    if (cols > 8) throw new Error('Keep to at most 8 columns for visualization');
    if (!t) throw new Error('Add a target after the ";"');
    const target = Number(t);
    if (!Number.isFinite(target)) throw new Error('Enter a numeric target after the ";"');
    return { matrix, target };
  },
  buildStates({ matrix, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const rows = matrix.length, cols = matrix[0].length;
    let lo = 0, hi = rows * cols - 1;
    domPushState(seq, {
      matrix, target, lo, hi, r: -1, c: -1, val: null, found: false,
      explTitle: 'Initialization',
      explText: `Treat the grid as one flattened sorted array of ${rows * cols} values. lo = 0, hi = ${hi}.`,
      pause: true,
    }, ctx);
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      const r = Math.floor(mid / cols), c = mid % cols;
      const val = matrix[r][c];
      domPushState(seq, {
        matrix, target, lo, hi, r, c, val, found: false, mid,
        explTitle: 'Map flat index to (row, col)',
        explText: `mid = ${mid} → row ${r}, col ${c}. matrix[${r}][${c}] = ${val}.`,
      }, ctx);
      if (val === target) {
        domPushState(seq, {
          matrix, target, lo, hi, r, c, val, found: true, mid,
          explTitle: 'Found it', explText: `${val} == ${target}. Return True.`, pause: true,
        }, ctx);
        return seq;
      } else if (val < target) {
        domPushState(seq, {
          matrix, target, lo, hi, r, c, val, found: false, mid,
          explTitle: 'Too small', explText: `${val} < ${target} — discard everything up to and including this cell. lo = ${mid + 1}.`,
        }, ctx);
        lo = mid + 1;
      } else {
        domPushState(seq, {
          matrix, target, lo, hi, r, c, val, found: false, mid,
          explTitle: 'Too big', explText: `${val} > ${target} — discard this cell onward. hi = ${mid - 1}.`,
        }, ctx);
        hi = mid - 1;
      }
    }
    domPushState(seq, {
      matrix, target, lo, hi, r: -1, c: -1, val: null, found: false,
      explTitle: 'Not found', explText: `lo (${lo}) > hi (${hi}). ${target} is not in the matrix. Return False.`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const cols = s.matrix[0].length;
    const grid = ggGridHTML(s.matrix, (v, ri, ci) => {
      const idx = ri * cols + ci;
      const isCur = ri === s.r && ci === s.c;
      const outOfRange = idx < s.lo || idx > s.hi;
      return {
        content: v,
        bg: s.found && isCur ? 'var(--emerald)' : isCur ? 'var(--accent)' : undefined,
        color: (s.found && isCur) || isCur ? '#04110b' : undefined,
        opacity: outOfRange ? 0.3 : 1,
      };
    });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>matrix (read as one flat sorted array)</span>
                      <span style="color:var(--text-bright);">Target: ${s.target}</span>
                  </div>
                  ${grid}
              </div>
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px; color:var(--text-dim);">
                  lo = ${s.lo} · hi = ${s.hi}${s.r >= 0 ? ` · mid → (row ${s.r}, col ${s.c}) = ${s.val}` : ''}
              </div>
      </div>`;
  },
});

/* ============================================ 006 · Koko Eating Bananas == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Koko Eating Bananas', short: 'Koko Eating Bananas',
  idea: 'Binary search on the ANSWER, not the array. The eating speed k is monotonic: if a speed works within h hours, every faster speed also works. So binary search over candidate speeds 1..max(piles), using a feasibility check — total hours at speed k — to decide which half survives.',
  complexity: 'Time O(n log(max(piles))) · Space O(1)',
  input: '3,6,7,11 ; 8', hint: 'pile sizes ; hours limit h',
  code: [
    'def minEatingSpeed(piles, h):',
    '    def feasible(k):',
    '        hours = 0',
    '        for p in piles:',
    '            hours += -(-p // k)   # ceil(p / k)',
    '        return hours <= h',
    '',
    '    lo, hi = 1, max(piles)',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if feasible(mid):',
    '            hi = mid',
    '        else:',
    '            lo = mid + 1',
    '    return lo',
  ],
  parse(s) {
    const [a, hStr] = avParts(s);
    const piles = avNums(a, 10, 'pile sizes');
    if (piles.some(p => p <= 0)) throw new Error('Pile sizes must be positive');
    const h = avNum(hStr, 'h');
    if (h < piles.length) throw new Error('h must be at least the number of piles');
    return { piles, h };
  },
  buildStates({ piles, h }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const ceilDiv = (p, k) => Math.ceil(p / k);
    let lo = 1, hi = Math.max(...piles);
    domPushState(seq, {
      piles, h, lo, hi, mid: -1, hours: [], total: null, feasible: null,
      explTitle: 'Initialization',
      explText: `The slowest useful speed is 1; the fastest worth trying is max(piles) = ${hi} (any faster finishes every pile in one hour anyway).`,
      pause: true,
    }, ctx);
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      const hours = piles.map(p => ceilDiv(p, mid));
      const total = hours.reduce((a, b) => a + b, 0);
      const feasible = total <= h;
      domPushState(seq, {
        piles, h, lo, hi, mid, hours, total, feasible,
        explTitle: `Try speed ${mid}`,
        explText: `At speed ${mid}, Koko needs ⌈p/${mid}⌉ hours per pile → total ${total} hours. ${feasible ? `${total} ≤ ${h}, so ${mid} works — try slower.` : `${total} > ${h}, too slow — need a faster speed.`}`,
      }, ctx);
      if (feasible) hi = mid; else lo = mid + 1;
    }
    domPushState(seq, {
      piles, h, lo, hi, mid: lo, hours: piles.map(p => ceilDiv(p, lo)), total: null, feasible: true,
      explTitle: 'Converged', explText: `lo == hi == ${lo}. That is the minimum feasible eating speed.`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const arr = bsArrayHTML(s.piles, (idx, v) => ({}));
    const hoursChips = s.hours.length
      ? chipRow(s.hours.map((h, i) => `pile ${s.piles[i]} → ${h}h`))
      : `<div style="color:var(--text-dim); font-size:12px; padding:6px;">(pick a candidate speed to see per-pile hours)</div>`;
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">piles</div>
                  <div class="array-track">${arr}</div>
              </div>
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px; color:var(--text-dim);">
                  candidate speeds: lo = ${s.lo} · hi = ${s.hi}${s.mid >= 0 ? ` · trying k = ${s.mid}` : ''}${s.total !== null ? ` · total hours = ${s.total} (limit h = ${s.h})` : ''}
              </div>
              <div class="glass-panel">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>hours needed at this speed</span>
                      ${s.feasible !== null ? `<span style="color:${s.feasible ? '#10b981' : '#ef4444'}">${s.feasible ? 'feasible' : 'too slow'}</span>` : ''}
                  </div>
                  ${hoursChips}
              </div>
      </div>`;
  },
});

/* ================================ 007 · Find Minimum in Rotated Array === */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Find Minimum in Rotated Sorted Array', short: 'Find Min in Rotated',
  idea: 'The array is two sorted runs glued together at the rotation point. Compare nums[mid] to nums[hi]: if nums[mid] > nums[hi], the minimum is strictly to the right of mid (the rotation point is ahead); otherwise mid could BE the minimum, so keep it in range.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '4, 5, 6, 7, 0, 1, 2', hint: 'a rotated sorted array, no duplicates',
  code: [
    'def findMin(nums):',
    '    lo, hi = 0, len(nums) - 1',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if nums[mid] > nums[hi]:',
    '            lo = mid + 1',
    '        else:',
    '            hi = mid',
    '    return nums[lo]',
  ],
  parse(s) {
    const nums = avNums(s, 14, 'rotated sorted array');
    if (nums.length < 1) throw new Error('Enter at least one number');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let lo = 0, hi = nums.length - 1;
    domPushState(seq, {
      nums, lo, hi, mid: -1, done: false,
      explTitle: 'Initialization', explText: `lo = 0, hi = ${hi}.`, pause: true,
    }, ctx);
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      const rotated = nums[mid] > nums[hi];
      domPushState(seq, {
        nums, lo, hi, mid, done: false,
        explTitle: `Compare nums[mid] to nums[hi]`,
        explText: `nums[${mid}] = ${nums[mid]}, nums[${hi}] = ${nums[hi]}. ${rotated ? `${nums[mid]} > ${nums[hi]} — the rotation point (and the minimum) is to the right of mid. lo = ${mid + 1}.` : `${nums[mid]} ≤ ${nums[hi]} — this half is already sorted, but mid could still be the minimum. hi = ${mid}.`}`,
      }, ctx);
      if (rotated) lo = mid + 1; else hi = mid;
    }
    domPushState(seq, {
      nums, lo, hi, mid: lo, done: true,
      explTitle: 'Converged', explText: `lo == hi == ${lo}. nums[${lo}] = ${nums[lo]} is the minimum.`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const arr = bsArrayHTML(s.nums, (idx, v) => {
      const cls = s.done && idx === s.lo ? 'active-k' : idx === s.mid ? 'active-1' : '';
      const dim = idx < s.lo || idx > s.hi;
      let pointer = '';
      if (idx === s.lo) pointer += bsPointerHTML('lo', 'var(--accent)');
      if (idx === s.hi) pointer += bsPointerHTML('hi', '#f59e0b');
      if (idx === s.mid && s.mid !== s.lo && s.mid !== s.hi) pointer += bsPointerHTML('mid', '#3b82f6');
      return { cls, dim, pointer };
    });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums (rotated sorted)</div>
                  <div class="array-track">${arr}</div>
              </div>
      </div>`;
  },
});

/* ====================================== 008 · Search in Rotated Array === */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Search in Rotated Sorted Array', short: 'Search in Rotated Array',
  idea: 'One of the two halves around mid is always properly sorted, even in a rotated array. Figure out which half is sorted by comparing nums[lo] to nums[mid], then check whether the target falls inside that sorted half\'s range — if so, search there; if not, search the other half.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '4, 5, 6, 7, 0, 1, 2 ; 0', hint: 'rotated sorted array ; target',
  code: [
    'def search(nums, target):',
    '    lo, hi = 0, len(nums) - 1',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        if nums[mid] == target:',
    '            return mid',
    '        if nums[lo] <= nums[mid]:        # left half sorted',
    '            if nums[lo] <= target < nums[mid]:',
    '                hi = mid - 1',
    '            else:',
    '                lo = mid + 1',
    '        else:                            # right half sorted',
    '            if nums[mid] < target <= nums[hi]:',
    '                lo = mid + 1',
    '            else:',
    '                hi = mid - 1',
    '    return -1',
  ],
  parse(s) {
    const [a, t] = avParts(s);
    const nums = avNums(a, 14, 'rotated sorted array');
    return { nums, target: avNum(t, 'target') };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let lo = 0, hi = nums.length - 1;
    domPushState(seq, {
      nums, target, lo, hi, mid: -1, found: -1, sortedHalf: null,
      explTitle: 'Initialization', explText: `Looking for ${target}. lo = 0, hi = ${hi}.`, pause: true,
    }, ctx);
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (nums[mid] === target) {
        domPushState(seq, {
          nums, target, lo, hi, mid, found: mid, sortedHalf: null,
          explTitle: 'Found it', explText: `nums[${mid}] == ${target}. Return ${mid}.`, pause: true,
        }, ctx);
        return seq;
      }
      const leftSorted = nums[lo] <= nums[mid];
      domPushState(seq, {
        nums, target, lo, hi, mid, found: -1, sortedHalf: leftSorted ? 'left' : 'right',
        explTitle: leftSorted ? 'Left half is sorted' : 'Right half is sorted',
        explText: leftSorted
          ? `nums[${lo}] (${nums[lo]}) ≤ nums[${mid}] (${nums[mid]}), so [${lo}..${mid}] is the sorted half.`
          : `nums[${lo}] (${nums[lo]}) > nums[${mid}] (${nums[mid]}), so [${mid}..${hi}] is the sorted half.`,
      }, ctx);
      if (leftSorted) {
        const inLeft = nums[lo] <= target && target < nums[mid];
        domPushState(seq, {
          nums, target, lo, hi, mid, found: -1, sortedHalf: 'left',
          explTitle: inLeft ? 'Target is in the sorted left half' : 'Target is not in the sorted left half',
          explText: inLeft ? `${nums[lo]} ≤ ${target} < ${nums[mid]} — search [${lo}..${mid - 1}].` : `${target} is outside [${nums[lo]}, ${nums[mid]}) — search [${mid + 1}..${hi}] instead.`,
        }, ctx);
        if (inLeft) hi = mid - 1; else lo = mid + 1;
      } else {
        const inRight = nums[mid] < target && target <= nums[hi];
        domPushState(seq, {
          nums, target, lo, hi, mid, found: -1, sortedHalf: 'right',
          explTitle: inRight ? 'Target is in the sorted right half' : 'Target is not in the sorted right half',
          explText: inRight ? `${nums[mid]} < ${target} ≤ ${nums[hi]} — search [${mid + 1}..${hi}].` : `${target} is outside (${nums[mid]}, ${nums[hi]}] — search [${lo}..${mid - 1}] instead.`,
        }, ctx);
        if (inRight) lo = mid + 1; else hi = mid - 1;
      }
    }
    domPushState(seq, {
      nums, target, lo, hi, mid: -1, found: -1, sortedHalf: null,
      explTitle: 'Not found', explText: `lo (${lo}) > hi (${hi}). ${target} is not in the array. Return -1.`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const arr = bsArrayHTML(s.nums, (idx, v) => {
      const dim = idx < s.lo || idx > s.hi;
      const cls = idx === s.found ? 'active-k' : idx === s.mid ? 'active-1' : '';
      let pointer = '';
      if (idx === s.lo) pointer += bsPointerHTML('lo', 'var(--accent)');
      if (idx === s.hi) pointer += bsPointerHTML('hi', '#f59e0b');
      if (idx === s.mid) pointer += bsPointerHTML('mid', '#3b82f6');
      return { cls, dim, pointer };
    });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>nums (rotated sorted)</span>
                      <span style="color:var(--text-bright);">Target: ${s.target}${s.sortedHalf ? ` · sorted half: ${s.sortedHalf}` : ''}</span>
                  </div>
                  <div class="array-track">${arr}</div>
              </div>
      </div>`;
  },
});

/* ==================================== 009 · Time Based Key-Value Store == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Time Based Key-Value Store', short: 'Time Based Key-Value Store',
  idea: 'set() always appends — timestamps arrive strictly increasing per key, so each key\'s list stays sorted with zero extra work. get() then bisects that one key\'s (timestamp, value) list for the rightmost entry whose timestamp is ≤ the query.',
  complexity: 'set: O(1) amortized · get: O(log m) where m = entries for that key',
  input: 'set foo bar 1, set foo bar2 4, get foo 2, get foo 5, get foo 0', hint: 'comma-separated ops: set key val ts | get key ts',
  code: [
    'def set(key, value, timestamp):',
    '    store[key].append((timestamp, value))',
    '',
    'def get(key, timestamp):',
    '    entries = store.get(key)',
    '    if not entries: return ""',
    '    lo, hi = 0, len(entries) - 1',
    '    ans = ""',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        if entries[mid][0] <= timestamp:',
    '            ans = entries[mid][1]',
    '            lo = mid + 1',
    '        else:',
    '            hi = mid - 1',
    '    return ans',
  ],
  parse(s) {
    const ops = String(s || '').split(',').map(x => x.trim()).filter(Boolean);
    if (!ops.length) throw new Error('Enter at least one operation');
    if (ops.length > 10) throw new Error('Use at most 10 operations for visualization');
    const parsed = ops.map(op => {
      const parts = op.split(/\s+/);
      if (parts[0] === 'set' && parts.length === 4) {
        const ts = Number(parts[3]);
        if (!Number.isFinite(ts)) throw new Error(`"${op}" — timestamp must be a number`);
        return { kind: 'set', key: parts[1], value: parts[2], ts };
      }
      if (parts[0] === 'get' && parts.length === 3) {
        const ts = Number(parts[2]);
        if (!Number.isFinite(ts)) throw new Error(`"${op}" — timestamp must be a number`);
        return { kind: 'get', key: parts[1], ts };
      }
      throw new Error(`"${op}" should look like "set key value ts" or "get key ts"`);
    });
    return { ops: parsed };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const store = {};
    const snapshot = extra => ({ store: Object.fromEntries(Object.entries(store).map(([k, v]) => [k, [...v]])), ...extra });
    domPushState(seq, {
      ...snapshot({ curKey: null, lo: -1, hi: -1, mid: -1, ans: null, op: null }),
      explTitle: 'Initialization', explText: 'One append-only list of (timestamp, value) pairs per key.', pause: true,
    }, ctx);
    for (const op of ops) {
      if (op.kind === 'set') {
        (store[op.key] ??= []).push([op.ts, op.value]);
        domPushState(seq, {
          ...snapshot({ curKey: op.key, lo: -1, hi: -1, mid: -1, ans: null, op: `set(${op.key}, ${op.value}, ${op.ts})` }),
          explTitle: `set(${op.key}, ${op.value}, ${op.ts})`,
          explText: `Append (${op.ts}, "${op.value}") to the list for "${op.key}". Timestamps arrive increasing, so no sorting is needed.`,
        }, ctx);
      } else {
        const entries = store[op.key] || [];
        let lo = 0, hi = entries.length - 1, ans = '';
        domPushState(seq, {
          ...snapshot({ curKey: op.key, lo, hi, mid: -1, ans: null, op: `get(${op.key}, ${op.ts})` }),
          explTitle: `get(${op.key}, ${op.ts})`,
          explText: entries.length ? `Bisect the ${entries.length} entries for "${op.key}" for the rightmost timestamp ≤ ${op.ts}.` : `No entries exist for "${op.key}" yet. Return "".`,
        }, ctx);
        while (lo <= hi) {
          const mid = Math.floor((lo + hi) / 2);
          const fits = entries[mid][0] <= op.ts;
          domPushState(seq, {
            ...snapshot({ curKey: op.key, lo, hi, mid, ans, op: `get(${op.key}, ${op.ts})` }),
            explTitle: `Check entry ${mid}`,
            explText: `entries[${mid}] = (${entries[mid][0]}, "${entries[mid][1]}"). ${fits ? `${entries[mid][0]} ≤ ${op.ts} — candidate answer, but look for a later one. lo = ${mid + 1}.` : `${entries[mid][0]} > ${op.ts} — too late. hi = ${mid - 1}.`}`,
          }, ctx);
          if (fits) { ans = entries[mid][1]; lo = mid + 1; } else hi = mid - 1;
        }
        domPushState(seq, {
          ...snapshot({ curKey: op.key, lo, hi, mid: -1, ans, op: `get(${op.key}, ${op.ts})` }),
          explTitle: 'Result', explText: `get(${op.key}, ${op.ts}) → "${ans}"`, pause: true,
        }, ctx);
      }
    }
    return seq;
  },
  renderDOM(container, s) {
    const keys = Object.keys(s.store);
    const keyPanels = keys.length ? keys.map(k => {
      const entries = s.store[k];
      const isCur = k === s.curKey;
      const arr = entries.length ? bsArrayHTML(entries.map(([ts, v]) => `${ts}:${v}`), (idx) => {
        if (!isCur) return {};
        let pointer = '';
        if (idx === s.lo) pointer += bsPointerHTML('lo', 'var(--accent)');
        if (idx === s.hi) pointer += bsPointerHTML('hi', '#f59e0b');
        if (idx === s.mid) pointer += bsPointerHTML('mid', '#3b82f6');
        return { pointer };
      }) : `<div style="color:var(--text-dim); padding:10px;">(empty)</div>`;
      return `<div class="glass-panel arrays-container" style="${isCur ? 'border-color:var(--accent);' : ''}">
        <div class="panel-heading">key: "${k}"</div>
        <div class="array-track">${arr}</div>
      </div>`;
    }).join('') : `<div class="glass-panel" style="padding:15px; color:var(--text-dim);">(no keys set yet)</div>`;
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px;">
                  ${s.op || '(start)'}${s.ans !== null ? ` → "${s.ans}"` : ''}
              </div>
              ${keyPanels}
      </div>`;
  },
});

/* ============================= 010 · Capacity To Ship Packages in D Days == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Capacity To Ship Packages Within D Days', short: 'Capacity To Ship Packages',
  idea: 'Same shape as Koko Eating Bananas: binary search on the ANSWER (ship capacity). A capacity works if a greedy left-to-right loading (start a new day whenever the next package would overflow) needs at most D days — that feasibility is monotonic in capacity.',
  complexity: 'Time O(n log(Σweights)) · Space O(1)',
  input: '1,2,3,4,5,6,7,8,9,10 ; 5', hint: 'package weights ; days D',
  code: [
    'def shipWithinDays(weights, days):',
    '    def feasible(cap):',
    '        day_count, load = 1, 0',
    '        for w in weights:',
    '            if load + w > cap:',
    '                day_count += 1',
    '                load = 0',
    '            load += w',
    '        return day_count <= days',
    '',
    '    lo, hi = max(weights), sum(weights)',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if feasible(mid):',
    '            hi = mid',
    '        else:',
    '            lo = mid + 1',
    '    return lo',
  ],
  parse(s) {
    const [a, dStr] = avParts(s);
    const weights = avNums(a, 12, 'package weights');
    if (weights.some(w => w <= 0)) throw new Error('Weights must be positive');
    const days = avNum(dStr, 'D');
    if (days < 1 || days > weights.length) throw new Error('D must be between 1 and the number of packages');
    return { weights, days };
  },
  buildStates({ weights, days }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const groupsFor = cap => {
      const groups = [[]]; let load = 0;
      for (const w of weights) {
        if (load + w > cap) { groups.push([]); load = 0; }
        groups[groups.length - 1].push(w); load += w;
      }
      return groups;
    };
    let lo = Math.max(...weights), hi = weights.reduce((a, b) => a + b, 0);
    domPushState(seq, {
      weights, days, lo, hi, mid: -1, groups: [], feasible: null,
      explTitle: 'Initialization',
      explText: `Capacity must be at least the heaviest package (${lo}) and never needs to exceed the total (${hi}).`,
      pause: true,
    }, ctx);
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      const groups = groupsFor(mid);
      const feasible = groups.length <= days;
      domPushState(seq, {
        weights, days, lo, hi, mid, groups, feasible,
        explTitle: `Try capacity ${mid}`,
        explText: `Greedily loading each day up to capacity ${mid} needs ${groups.length} day${groups.length === 1 ? '' : 's'}. ${feasible ? `${groups.length} ≤ ${days}, so ${mid} works — try smaller.` : `${groups.length} > ${days}, too small — need more capacity.`}`,
      }, ctx);
      if (feasible) hi = mid; else lo = mid + 1;
    }
    domPushState(seq, {
      weights, days, lo, hi, mid: lo, groups: groupsFor(lo), feasible: true,
      explTitle: 'Converged', explText: `lo == hi == ${lo}. That is the minimum feasible capacity.`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const dayColors = ['#3b82f6', '#f59e0b', '#10b981', '#a855f7', '#ec4899', '#14b8a6', '#f97316', '#84cc16'];
    let wi = 0;
    const groupChips = s.groups.length
      ? s.groups.map((g, gi) => chipRow(g.map(w => `${w}`), {})).map((row, gi) =>
          `<div style="display:flex; align-items:center; gap:8px;"><span style="font-size:11px; color:${dayColors[gi % dayColors.length]}; min-width:48px;">day ${gi + 1}</span>${row}</div>`
        ).join('')
      : `<div style="color:var(--text-dim); font-size:12px; padding:6px;">(pick a candidate capacity to see the day-by-day loading)</div>`;
    const arr = bsArrayHTML(s.weights, () => ({}));
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">weights</div>
                  <div class="array-track">${arr}</div>
              </div>
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px; color:var(--text-dim);">
                  candidate capacity: lo = ${s.lo} · hi = ${s.hi}${s.mid >= 0 ? ` · trying cap = ${s.mid}` : ''} · limit D = ${s.days}
              </div>
              <div class="glass-panel">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>greedy day-by-day loading at this capacity</span>
                      ${s.feasible !== null ? `<span style="color:${s.feasible ? '#10b981' : '#ef4444'}">${s.groups.length} day${s.groups.length === 1 ? '' : 's'} · ${s.feasible ? 'feasible' : 'too tight'}</span>` : ''}
                  </div>
                  ${groupChips}
              </div>
      </div>`;
  },
});

/* ====================================== 011 · Split Array Largest Sum == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Split Array Largest Sum', short: 'Split Array Largest Sum',
  idea: 'Same shape again: binary search on the ANSWER (the cap on any one piece\'s sum). A cap works if a greedy left-to-right cut (start a new piece whenever the running sum would exceed the cap) needs at most k pieces — monotonic in the cap, so binary search finds the smallest feasible one.',
  complexity: 'Time O(n log(Σnums)) · Space O(1)',
  input: '7,2,5,10,8 ; 2', hint: 'array ; number of pieces k',
  code: [
    'def splitArray(nums, k):',
    '    def feasible(cap):',
    '        pieces, cur = 1, 0',
    '        for x in nums:',
    '            if cur + x > cap:',
    '                pieces += 1',
    '                cur = 0',
    '            cur += x',
    '        return pieces <= k',
    '',
    '    lo, hi = max(nums), sum(nums)',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if feasible(mid):',
    '            hi = mid',
    '        else:',
    '            lo = mid + 1',
    '    return lo',
  ],
  parse(s) {
    const [a, kStr] = avParts(s);
    const nums = avNums(a, 12, 'array');
    if (nums.some(x => x < 0)) throw new Error('Values must be non-negative');
    const k = avNum(kStr, 'k');
    if (k < 1 || k > nums.length) throw new Error('k must be between 1 and the array length');
    return { nums, k };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const piecesFor = cap => {
      const groups = [[]]; let cur = 0;
      for (const x of nums) {
        if (cur + x > cap) { groups.push([]); cur = 0; }
        groups[groups.length - 1].push(x); cur += x;
      }
      return groups;
    };
    let lo = Math.max(...nums), hi = nums.reduce((a, b) => a + b, 0);
    domPushState(seq, {
      nums, k, lo, hi, mid: -1, groups: [], feasible: null,
      explTitle: 'Initialization',
      explText: `The cap must be at least the largest single element (${lo}) — a smaller cap could never fit it in any piece — and never needs to exceed the total (${hi}).`,
      pause: true,
    }, ctx);
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      const groups = piecesFor(mid);
      const feasible = groups.length <= k;
      domPushState(seq, {
        nums, k, lo, hi, mid, groups, feasible,
        explTitle: `Try cap ${mid}`,
        explText: `Greedily cutting whenever a piece would exceed ${mid} needs ${groups.length} piece${groups.length === 1 ? '' : 's'}. ${feasible ? `${groups.length} ≤ ${k}, so ${mid} works — try smaller.` : `${groups.length} > ${k}, too many pieces — need a larger cap.`}`,
      }, ctx);
      if (feasible) hi = mid; else lo = mid + 1;
    }
    domPushState(seq, {
      nums, k, lo, hi, mid: lo, groups: piecesFor(lo), feasible: true,
      explTitle: 'Converged', explText: `lo == hi == ${lo}. That is the smallest possible "largest piece sum".`, pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const pieceColors = ['#3b82f6', '#f59e0b', '#10b981', '#a855f7', '#ec4899', '#14b8a6', '#f97316', '#84cc16'];
    const groupChips = s.groups.length
      ? s.groups.map((g, gi) => {
          const sum = g.reduce((a, b) => a + b, 0);
          return `<div style="display:flex; align-items:center; gap:8px;"><span style="font-size:11px; color:${pieceColors[gi % pieceColors.length]}; min-width:70px;">piece ${gi + 1} (Σ${sum})</span>${chipRow(g.map(String))}</div>`;
        }).join('')
      : `<div style="color:var(--text-dim); font-size:12px; padding:6px;">(pick a candidate cap to see the greedy cuts)</div>`;
    const arr = bsArrayHTML(s.nums, () => ({}));
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums</div>
                  <div class="array-track">${arr}</div>
              </div>
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px; color:var(--text-dim);">
                  candidate cap: lo = ${s.lo} · hi = ${s.hi}${s.mid >= 0 ? ` · trying cap = ${s.mid}` : ''} · limit k = ${s.k}
              </div>
              <div class="glass-panel">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>greedy pieces at this cap</span>
                      ${s.feasible !== null ? `<span style="color:${s.feasible ? '#10b981' : '#ef4444'}">${s.groups.length} piece${s.groups.length === 1 ? '' : 's'} · ${s.feasible ? 'feasible' : 'too many'}</span>` : ''}
                  </div>
                  ${groupChips}
              </div>
      </div>`;
  },
});

/* ==================================== 012 · Median of Two Sorted Arrays == */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Median of Two Sorted Arrays', short: 'Median of Two Sorted Arrays',
  idea: 'Binary search on the PARTITION POINT of the shorter array, not on any value. Cut A at index i and B at index j = half − i so the left side holds exactly half the combined elements. The correct cut is the one where every left-side value ≤ every right-side value — check that with just 4 border values.',
  complexity: 'Time O(log(min(m,n))) · Space O(1)',
  input: '1,3 ; 2', hint: 'array A ; array B (both sorted)',
  code: [
    'def findMedianSortedArrays(A, B):',
    '    if len(A) > len(B): A, B = B, A       # A is the shorter array',
    '    m, n = len(A), len(B)',
    '    half = (m + n + 1) // 2',
    '    lo, hi = 0, m',
    '    while lo <= hi:',
    '        i = (lo + hi) // 2                 # cut A after i elements',
    '        j = half - i                       # cut B after j elements',
    '        aL = A[i-1] if i > 0 else -inf',
    '        aR = A[i]   if i < m else inf',
    '        bL = B[j-1] if j > 0 else -inf',
    '        bR = B[j]   if j < n else inf',
    '        if aL <= bR and bL <= aR:',
    '            if (m + n) % 2:',
    '                return max(aL, bL)',
    '            return (max(aL, bL) + min(aR, bR)) / 2',
    '        if aL > bR: hi = i - 1',
    '        else:       lo = i + 1',
  ],
  parse(s) {
    const [aStr, bStr] = avParts(s);
    const A0 = avNums(aStr, 8, 'array A');
    const B0 = avNums(bStr, 8, 'array B');
    const sorted = arr => arr.every((x, i) => i === 0 || x >= arr[i - 1]);
    if (!sorted(A0) || !sorted(B0)) throw new Error('Both arrays must already be sorted');
    return { A0, B0 };
  },
  buildStates({ A0, B0 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let A = A0, B = B0, swapped = false;
    if (A.length > B.length) { [A, B] = [B, A]; swapped = true; }
    const m = A.length, n = B.length;
    const half = Math.floor((m + n + 1) / 2);
    const INF = Infinity, NINF = -Infinity;
    let lo = 0, hi = m;
    domPushState(seq, {
      A, B, swapped, i: -1, j: -1, aL: null, aR: null, bL: null, bR: null, median: null,
      explTitle: 'Initialization',
      explText: `A is the shorter array${swapped ? ' (swapped so it is)' : ''} — length ${m}, vs B's ${n}. The left half of the merged array should hold ${half} elements.`,
      pause: true,
    }, ctx);
    while (lo <= hi) {
      const i = Math.floor((lo + hi) / 2);
      const j = half - i;
      const aL = i > 0 ? A[i - 1] : NINF, aR = i < m ? A[i] : INF;
      const bL = j > 0 ? B[j - 1] : NINF, bR = j < n ? B[j] : INF;
      domPushState(seq, {
        A, B, swapped, i, j, aL, aR, bL, bR, median: null,
        explTitle: `Try cutting A after ${i} element${i === 1 ? '' : 's'}`,
        explText: `Then B must be cut after j = ${half} − ${i} = ${j}. Left borders: A[${i - 1}]=${aL === NINF ? '−∞' : aL}, B[${j - 1}]=${bL === NINF ? '−∞' : bL}. Right borders: A[${i}]=${aR === INF ? '+∞' : aR}, B[${j}]=${bR === INF ? '+∞' : bR}.`,
      }, ctx);
      if (aL <= bR && bL <= aR) {
        const median = (m + n) % 2 ? Math.max(aL, bL) : (Math.max(aL, bL) + Math.min(aR, bR)) / 2;
        domPushState(seq, {
          A, B, swapped, i, j, aL, aR, bL, bR, median,
          explTitle: 'Valid partition found',
          explText: `Every left value ≤ every right value. ${(m + n) % 2 ? `Odd total length — median is max(left) = ${median}.` : `Even total length — median is the average of max(left) and min(right) = ${median}.`}`,
          pause: true,
        }, ctx);
        return seq;
      }
      if (aL > bR) {
        domPushState(seq, {
          A, B, swapped, i, j, aL, aR, bL, bR, median: null,
          explTitle: 'A took too much', explText: `A[${i - 1}] = ${aL} > B[${j}] = ${bR} — cut A earlier. hi = ${i - 1}.`,
        }, ctx);
        hi = i - 1;
      } else {
        domPushState(seq, {
          A, B, swapped, i, j, aL, aR, bL, bR, median: null,
          explTitle: 'A took too little', explText: `B[${j - 1}] = ${bL} > A[${i}] = ${aR} — cut A later. lo = ${i + 1}.`,
        }, ctx);
        lo = i + 1;
      }
    }
    return seq;
  },
  renderDOM(container, s) {
    const track = (arr, cut) => bsArrayHTML(arr, (idx) => ({
      cls: idx < cut ? 'merged' : '',
      pointer: idx === cut ? bsPointerHTML('cut', 'var(--accent)') : '',
    })) + (cut === arr.length ? `<div class="array-node" style="opacity:0.5; border-style:dashed;">${bsPointerHTML('cut', 'var(--accent)')}·</div>` : '');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">A (shorter array)</div>
                  <div class="array-track">${track(s.A, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">B</div>
                  <div class="array-track">${track(s.B, s.j)}</div>
              </div>
              <div class="glass-panel" style="padding:10px 15px; font-family:var(--mono); font-size:13px; color:var(--text-dim);">
                  ${s.i >= 0 ? `left borders: aL=${s.aL === -Infinity ? '−∞' : s.aL}, bL=${s.bL === -Infinity ? '−∞' : s.bL} · right borders: aR=${s.aR === Infinity ? '+∞' : s.aR}, bR=${s.bR === Infinity ? '+∞' : s.bR}` : ''}
                  ${s.median !== null ? `<div style="margin-top:6px; color:var(--text-bright); font-weight:600;">median = ${s.median}</div>` : ''}
              </div>
      </div>`;
  },
});
