/* ============================================================================
   Visualizations for 26_segment_tree_fenwick — the 5 problems that had no
   exact animation (002, 003, 004, 005, 006). Problem 001 (Range Sum Query -
   Mutable) already had a canvas-engine segment-tree spec in dsa-viz3.js —
   left untouched.
   ========================================================================= */
'use strict';

/* ============================================================ 002 · Range Sum Query 2D - Mutable */
defineAlgoDom('26_segment_tree_fenwick', {
  type: 'dom',
  title: 'Range Sum Query 2D - Mutable', short: 'BIT 2D',
  idea: '2D Binary Indexed Tree. Each cell (i, j) of the tree holds the sum of a small rectangle; <code>i += i &amp; -i</code> walks to the next rectangle that also covers this row, and the same trick runs on columns. An update touches O(log m · log n) tree cells instead of one; a region sum is four prefix-rectangle queries combined by inclusion–exclusion.',
  complexity: 'update / sumRegion O(log m · log n) · Space O(m·n)',
  input: '1,2,3;4,5,6;7,8,9 | 1,1=10 | 0,0,2,2', hint: 'matrix rows (;) cells (,) | row,col=newVal | r1,c1,r2,c2',
  code: [
    'def update(row, col, val):',
    '    delta = val - matrix[row][col]',
    '    matrix[row][col] = val',
    '    i = row + 1',
    '    while i <= m:',
    '        j = col + 1',
    '        while j <= n:',
    '            tree[i][j] += delta',
    '            j += j & (-j)',
    '        i += i & (-i)',
    '',
    'def _prefix(row, col):        # sum of rect (0,0)..(row-1,col-1)',
    '    s, i = 0, row',
    '    while i > 0:',
    '        j = col',
    '        while j > 0:',
    '            s += tree[i][j]',
    '            j -= j & (-j)',
    '        i -= i & (-i)',
    '    return s',
    '',
    '# sumRegion = prefix(r2+1,c2+1) - prefix(r1,c2+1) - prefix(r2+1,c1) + prefix(r1,c1)',
  ],
  parse(s) {
    const [a, u, q] = String(s || '').split('|').map(x => x.trim());
    const grid = agParseIntGrid(a, { max: 4 });
    const m = grid.length, n = grid[0].length;
    const um = u && u.match(/^(\d+)\s*,\s*(\d+)\s*=\s*(-?\d+)$/);
    if (!um) throw new Error('The update looks like "row,col=value"');
    const upd = { r: +um[1], c: +um[2], v: +um[3] };
    if (upd.r >= m || upd.c >= n) throw new Error(`The update cell must fit inside the ${m}x${n} matrix`);
    const qm = q && q.match(/^(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)$/);
    if (!qm) throw new Error('The query looks like "r1,c1,r2,c2"');
    const query = { r1: +qm[1], c1: +qm[2], r2: +qm[3], c2: +qm[4] };
    if (query.r1 > query.r2 || query.c1 > query.c2 || query.r2 >= m || query.c2 >= n) throw new Error('The query rectangle must fit inside the matrix and not be reversed');
    return { grid, m, n, upd, query };
  },
  buildStates({ grid, m, n, upd, query }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const cur = grid.map(r => [...r]);
    const tree = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    const bitAdd = (row, col, delta) => {
      let i = row + 1;
      while (i <= m) { let j = col + 1; while (j <= n) { tree[i][j] += delta; j += j & (-j); } i += i & (-i); }
    };
    for (let r = 0; r < m; r++) for (let c = 0; c < n; c++) bitAdd(r, c, grid[r][c]);
    domPushState(seq, {
      m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: null, path: [], query: null, line: 1, color: 'default',
      explTitle: 'Built', explText: `Every cell was inserted with update(), so the BIT already holds every partial rectangle sum.`, pause: true
    }, ctx);

    const delta = upd.v - cur[upd.r][upd.c];
    cur[upd.r][upd.c] = upd.v;
    domPushState(seq, {
      m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: [upd.r, upd.c], path: [], query: null, line: 2, color: 'amber',
      explTitle: 'Update', explText: `Set (${upd.r}, ${upd.c}) to ${upd.v} — a delta of ${delta >= 0 ? '+' : ''}${delta}.`
    }, ctx);
    {
      let i = upd.r + 1; const path = [];
      while (i <= m) {
        let j = upd.c + 1;
        while (j <= n) {
          tree[i][j] += delta; path.push([i, j]);
          domPushState(seq, {
            m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: [upd.r, upd.c], path: [...path], query: null, line: 8, color: 'blue',
            explTitle: `tree[${i}][${j}] += ${delta}`, explText: `Now ${tree[i][j]}. j += j & -j walks to the next column-range that also covers this cell.`
          }, ctx);
          j += j & (-j);
        }
        i += i & (-i);
      }
      domPushState(seq, {
        m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: [upd.r, upd.c], path: [...path], query: null, line: 10, color: 'emerald',
        explTitle: 'Update complete', explText: `${path.length} BIT cells touched instead of recomputing every row/column sum.`, pause: true
      }, ctx);
    }

    const prefix = (row, col) => {
      let sum = 0, i = row; const touched = [];
      while (i > 0) { let j = col; while (j > 0) { sum += tree[i][j]; touched.push([i, j]); j -= j & (-j); } i -= i & (-i); }
      return { sum, touched };
    };
    const corners = [
      { label: `(${query.r2 + 1},${query.c2 + 1})`, sign: 1, row: query.r2 + 1, col: query.c2 + 1 },
      { label: `(${query.r1},${query.c2 + 1})`, sign: -1, row: query.r1, col: query.c2 + 1 },
      { label: `(${query.r2 + 1},${query.c1})`, sign: -1, row: query.r2 + 1, col: query.c1 },
      { label: `(${query.r1},${query.c1})`, sign: 1, row: query.r1, col: query.c1 },
    ];
    let total = 0;
    corners.forEach(cnr => {
      const { sum, touched } = prefix(cnr.row, cnr.col);
      total += cnr.sign * sum;
      domPushState(seq, {
        m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: null, path: touched, query, line: 12, color: cnr.sign > 0 ? 'emerald' : 'rose',
        explTitle: `prefix${cnr.label} = ${sum}`, explText: `${cnr.sign > 0 ? 'Add' : 'Subtract'} the rectangle (0,0)..${cnr.label} — this is one of the four inclusion–exclusion terms.`
      }, ctx);
    });
    domPushState(seq, {
      m, n, matrix: cur.map(r => [...r]), tree: tree.map(r => [...r]), hi: null, path: [], query, answer: total, line: 21, color: 'emerald',
      explTitle: 'Region sum', explText: `sumRegion(${query.r1},${query.c1},${query.r2},${query.c2}) = ${total}.`, pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const cellStyle = (grid, r, c, hiCell, pathSet) => {
      const isHi = hiCell && hiCell[0] === r && hiCell[1] === c;
      const onPath = pathSet.has(`${r},${c}`);
      return { bg: isHi ? 'var(--accent-dim, #3b82f633)' : onPath ? 'var(--emerald-dim, #10b98133)' : undefined, border: isHi ? 'var(--accent)' : onPath ? 'var(--emerald)' : undefined };
    };
    const pathSet = new Set((s.path || []).map(([i, j]) => `${i},${j}`));
    const matrixGrid = ggGridHTML(s.matrix, (v, r, c) => cellStyle(s.matrix, r, c, s.hi, new Set()));
    const treeRows = [];
    for (let i = 1; i <= s.m; i++) { const row = []; for (let j = 1; j <= s.n; j++) row.push(s.tree[i][j]); treeRows.push(row); }
    const treeGrid = ggGridHTML(treeRows, (v, r, c) => cellStyle(null, r + 1, c + 1, null, pathSet));
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel(`matrix (current values)${s.answer !== undefined ? ` — sumRegion = ${s.answer}` : ''}`, matrixGrid)}
        ${ggPanel('BIT tree[1..m][1..n]', treeGrid)}
      </div>`;
  }
});

/* ============================================================ 003 · Reverse Pairs */
defineAlgoDom('26_segment_tree_fenwick', {
  type: 'dom',
  title: 'Reverse Pairs', short: 'Reverse Pairs',
  idea: 'Modified merge sort. Recurse on both halves first — now each half is sorted. Count cross-pairs with a second pointer <code>j</code> that only ever moves forward (both halves are sorted, so it never needs to backtrack), <b>then</b> do the ordinary merge. The counting comparison (<code>arr[i] &gt; 2·arr[j]</code>) is deliberately different from the merge comparison — conflating them is the classic bug.',
  complexity: 'Time O(n log n) · Space O(n) — sorts a copy',
  input: '1,3,2,3,1', hint: 'up to 8 numbers',
  code: [
    'def merge_count(arr, lo, hi):',
    '    if lo >= hi: return 0',
    '    mid = (lo + hi) // 2',
    '    count = merge_count(arr, lo, mid) + merge_count(arr, mid+1, hi)',
    '    j = mid + 1',
    '    for i in range(lo, mid + 1):',
    '        while j <= hi and arr[i] > 2 * arr[j]:',
    '            j += 1',
    '        count += j - (mid + 1)',
    '    # standard merge-sort merge (different comparison) follows',
    '    merged = []',
    '    left, right = lo, mid + 1',
    '    while left <= mid and right <= hi:',
    '        if arr[left] <= arr[right]: merged.append(arr[left]); left += 1',
    '        else: merged.append(arr[right]); right += 1',
    '    merged += arr[left:mid+1] + arr[right:hi+1]',
    '    arr[lo:hi+1] = merged',
    '    return count',
  ],
  parse(s) {
    const nums = avNums(s, 8, 'numbers');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const arr = [...nums];
    domPushState(seq, {
      arr: [...arr], lo: 0, hi: arr.length - 1, mid: null, i: null, j: null, pairs: 0, total: null, line: 1, color: 'default',
      explTitle: 'Start', explText: `Copy the array so the caller's list is never mutated, then recursively split and merge.`, pause: true
    }, ctx);

    const mergeCount = (lo, hi) => {
      if (lo >= hi) return 0;
      const mid = lo + ((hi - lo) >> 1);
      domPushState(seq, {
        arr: [...arr], lo, hi, mid, i: null, j: null, pairs: 0, total: null, line: 3, color: 'blue',
        explTitle: `Split [${lo}, ${hi}]`, explText: `Recurse on the left half [${lo}, ${mid}] and the right half [${mid + 1}, ${hi}] before counting anything.`
      }, ctx);
      let count = mergeCount(lo, mid) + mergeCount(mid + 1, hi);
      let j = mid + 1;
      for (let i = lo; i <= mid; i++) {
        domPushState(seq, {
          arr: [...arr], lo, hi, mid, i, j, pairs: count, total: null, line: 6, color: 'amber',
          explTitle: `i = ${i} (value ${arr[i]})`, explText: `Both halves are sorted here, so j only ever moves forward — advance it while arr[i] &gt; 2 × arr[j].`
        }, ctx);
        while (j <= hi && arr[i] > 2 * arr[j]) {
          j++;
          domPushState(seq, {
            arr: [...arr], lo, hi, mid, i, j, pairs: count, total: null, line: 7, color: 'amber',
            explTitle: `Advance j to ${j}`, explText: j <= hi ? `arr[${i}]=${arr[i]} &gt; 2×arr[${j}]=${2 * arr[j]} — still inside the reverse-pair window.` : `j has run past the right half — every remaining element pairs with i.`
          }, ctx);
        }
        const found = j - (mid + 1);
        count += found;
        domPushState(seq, {
          arr: [...arr], lo, hi, mid, i, j, pairs: count, total: null, line: 8, color: 'rose',
          explTitle: `+${found} pair${found === 1 ? '' : 's'}`, explText: `Every arr[k] for k in [${mid + 1}, ${j - 1}] forms a reverse pair with arr[${i}] — running count in this range is now ${count}.`
        }, ctx);
      }
      const merged = [];
      let left = lo, right = mid + 1;
      while (left <= mid && right <= hi) { if (arr[left] <= arr[right]) merged.push(arr[left++]); else merged.push(arr[right++]); }
      while (left <= mid) merged.push(arr[left++]);
      while (right <= hi) merged.push(arr[right++]);
      for (let k = 0; k < merged.length; k++) arr[lo + k] = merged[k];
      domPushState(seq, {
        arr: [...arr], lo, hi, mid, i: null, j: null, pairs: count, total: null, line: 16, color: 'emerald',
        explTitle: `Merged [${lo}, ${hi}]`, explText: `Both halves are now one sorted run — a different comparison than the counting step above.`
      }, ctx);
      return count;
    };
    const total = mergeCount(0, arr.length - 1);
    domPushState(seq, {
      arr: [...arr], lo: 0, hi: arr.length - 1, mid: null, i: null, j: null, pairs: total, total, line: 17, color: 'emerald',
      explTitle: 'Done', explText: `Total reverse pairs = ${total}.`, pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const cells = s.arr.map((v, idx) => {
      const inRange = idx >= s.lo && idx <= s.hi;
      const leftHalf = s.mid !== null && idx <= s.mid && idx >= s.lo;
      const rightHalf = s.mid !== null && idx > s.mid && idx <= s.hi;
      let cls = !inRange ? 'merged' : idx === s.i ? 'active-k' : idx === s.j ? 'active-1' : leftHalf ? 'active-1' : rightHalf ? '' : '';
      let bg = leftHalf && idx !== s.i ? 'background:color-mix(in srgb, var(--blue) 12%, transparent);' : rightHalf && idx !== s.j ? 'background:color-mix(in srgb, var(--accent) 10%, transparent);' : '';
      return `
            <div class="array-node ${cls}" style="${bg}">
                ${idx === s.i ? '<div class="pointer" style="color:#34d399">↓ i</div>' : ''}
                ${idx === s.j ? '<div class="pointer" style="color:#3b82f6">↓ j</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
    }).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>arr</span>
                      <span>pairs so far in this range: ${s.pairs}${s.total !== null ? ` · total: ${s.total}` : ''}</span>
                  </div>
                  <div class="array-track">${cells}</div>
              </div>
    </div>`;
  }
});

/* ============================================================ 004 · Count of Range Sum */
defineAlgoDom('26_segment_tree_fenwick', {
  type: 'dom',
  title: 'Count of Range Sum', short: 'Range Sum Count',
  idea: 'Build the prefix-sum array first — now a subarray sum is just <code>prefix[j] - prefix[i]</code>. Count qualifying pairs with a merge sort over the prefix array: for each left-half prefix, the right-half prefixes that satisfy <code>lower ≤ prefix[j] - prefix[i] ≤ upper</code> form one contiguous, only-ever-forward-moving window <code>[lo_ptr, hi_ptr)</code> — because both halves are sorted.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '-2,5,-1 | -2 2', hint: 'numbers | lower upper',
  code: [
    'prefix = [0] * (len(nums) + 1)',
    'for i, v in enumerate(nums): prefix[i+1] = prefix[i] + v',
    '',
    'def merge_count(arr, lo, hi):',
    '    if lo >= hi: return 0',
    '    mid = (lo + hi) // 2',
    '    count = merge_count(arr, lo, mid) + merge_count(arr, mid+1, hi)',
    '    lo_ptr = hi_ptr = mid + 1',
    '    for i in range(lo, mid + 1):',
    '        while lo_ptr <= hi and arr[lo_ptr] - arr[i] < lower: lo_ptr += 1',
    '        while hi_ptr <= hi and arr[hi_ptr] - arr[i] <= upper: hi_ptr += 1',
    '        count += hi_ptr - lo_ptr',
    '    # standard merge-sort merge follows',
    '    return count',
  ],
  parse(s) {
    const [a, b] = String(s || '').split('|').map(x => x.trim());
    const nums = avNums(a, 7, 'numbers');
    const bm = b && b.match(/^(-?\d+)\s+(-?\d+)$/);
    if (!bm) throw new Error('Add "lower upper" after the "|"');
    const lower = +bm[1], upper = +bm[2];
    if (lower > upper) throw new Error('lower must be ≤ upper');
    return { nums, lower, upper };
  },
  buildStates({ nums, lower, upper }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const prefix = [0];
    for (const v of nums) prefix.push(prefix[prefix.length - 1] + v);
    domPushState(seq, {
      arr: [...prefix], lo: 0, hi: prefix.length - 1, mid: null, i: null, loPtr: null, hiPtr: null, count: 0, total: null, phase: 'prefix', line: 1, color: 'default',
      explTitle: 'Build prefix sums', explText: `prefix[k] = sum of nums[0..k-1], so any subarray sum is prefix[j] - prefix[i].`, pause: true
    }, ctx);

    const arr = [...prefix];
    const mergeCount = (lo, hi) => {
      if (lo >= hi) return 0;
      const mid = lo + ((hi - lo) >> 1);
      domPushState(seq, {
        arr: [...arr], lo, hi, mid, i: null, loPtr: null, hiPtr: null, count: 0, total: null, phase: 'split', line: 5, color: 'blue',
        explTitle: `Split [${lo}, ${hi}]`, explText: `Recurse on both halves of the prefix array before counting anything.`
      }, ctx);
      let count = mergeCount(lo, mid) + mergeCount(mid + 1, hi);
      let loPtr = mid + 1, hiPtr = mid + 1;
      for (let i = lo; i <= mid; i++) {
        while (loPtr <= hi && arr[loPtr] - arr[i] < lower) loPtr++;
        while (hiPtr <= hi && arr[hiPtr] - arr[i] <= upper) hiPtr++;
        const found = hiPtr - loPtr;
        count += found;
        domPushState(seq, {
          arr: [...arr], lo, hi, mid, i, loPtr, hiPtr, count, total: null, phase: 'count', line: 12,
          color: found ? 'emerald' : 'default',
          explTitle: `i = ${i} (prefix ${arr[i]})`, explText: `Window [${loPtr}, ${hiPtr}) holds every prefix[j] with lower ≤ prefix[j]-prefix[i] ≤ upper — +${found} range${found === 1 ? '' : 's'}.`
        }, ctx);
      }
      const merged = [];
      let left = lo, right = mid + 1;
      while (left <= mid && right <= hi) { if (arr[left] <= arr[right]) merged.push(arr[left++]); else merged.push(arr[right++]); }
      while (left <= mid) merged.push(arr[left++]);
      while (right <= hi) merged.push(arr[right++]);
      for (let k = 0; k < merged.length; k++) arr[lo + k] = merged[k];
      domPushState(seq, {
        arr: [...arr], lo, hi, mid, i: null, loPtr: null, hiPtr: null, count, total: null, phase: 'merged', line: 13, color: 'emerald',
        explTitle: `Merged [${lo}, ${hi}]`, explText: `Both halves are now one sorted run of prefix sums.`
      }, ctx);
      return count;
    };
    const total = mergeCount(0, arr.length - 1);
    domPushState(seq, {
      arr: [...arr], lo: 0, hi: arr.length - 1, mid: null, i: null, loPtr: null, hiPtr: null, count: total, total, phase: 'done', line: 13, color: 'emerald',
      explTitle: 'Done', explText: `Total ranges with sum in [${lower}, ${upper}] = ${total}.`, pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const cells = s.arr.map((v, idx) => {
      const inRange = idx >= s.lo && idx <= s.hi;
      const leftHalf = s.mid !== null && idx <= s.mid && idx >= s.lo;
      const rightHalf = s.mid !== null && idx > s.mid && idx <= s.hi;
      const inWindow = s.loPtr !== null && idx >= s.loPtr && idx < s.hiPtr;
      let cls = !inRange ? 'merged' : idx === s.i ? 'active-k' : inWindow ? 'active-1' : '';
      let bg = leftHalf && idx !== s.i ? 'background:color-mix(in srgb, var(--blue) 12%, transparent);' : rightHalf && !inWindow ? 'background:color-mix(in srgb, var(--accent) 10%, transparent);' : '';
      return `
            <div class="array-node ${cls}" style="${bg}">
                ${idx === s.i ? '<div class="pointer" style="color:#34d399">↓ i</div>' : ''}
                ${idx === s.loPtr ? '<div class="pointer" style="color:#3b82f6">↓ lo_ptr</div>' : ''}
                ${idx === s.hiPtr ? '<div class="pointer" style="color:#3b82f6">↓ hi_ptr</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
    }).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>prefix sums</span>
                      <span>count so far in this range: ${s.count}${s.total !== null ? ` · total: ${s.total}` : ''}</span>
                  </div>
                  <div class="array-track">${cells}</div>
              </div>
    </div>`;
  }
});

/* ============================================================ 005 · Falling Squares */
defineAlgo('26_segment_tree_fenwick', {
  title: 'Falling Squares', short: 'Falling Squares',
  idea: 'Coordinate-compress every left/right edge into leaf intervals of a segment tree that supports range-MAX query and range-ASSIGN update with lazy propagation. Each square queries the max height already under its footprint, lands on top of that, then unconditionally assigns its new top height across that whole footprint — assignment (not add) is safe here because a square always covers its landing spot completely.',
  complexity: 'Time O(n log n) · Space O(n) — read-only after building',
  input: '1,2;2,3;6,1', hint: 'left,size ; left,size ; ...',
  code: [
    'def falling_squares(positions):',
    '    coords = sorted({x for l, sz in positions for x in (l, l+sz)})',
    '    seg = SegTreeMaxAssign(len(coords) - 1)',
    '    result, running_max = [], 0',
    '    for left, size in positions:',
    '        right = left + size',
    '        l_idx, r_idx = bisect(coords, left), bisect(coords, right) - 1',
    '        base = seg.query(l_idx, r_idx)         # tallest stack already there',
    '        landing = base + size',
    '        seg.update(l_idx, r_idx, landing)       # unconditional ASSIGN, with lazy push-down',
    '        running_max = max(running_max, landing)',
    '        result.append(running_max)',
    '    return result',
  ],
  parse(s) {
    const parts = String(s || '').split(';').map(x => x.trim()).filter(Boolean);
    if (!parts.length) throw new Error('Enter at least one square as left,size');
    if (parts.length > 5) throw new Error('Use at most 5 squares so the tree stays readable');
    return {
      positions: parts.map(p => {
        const m = p.match(/^(-?\d+)\s*,\s*(\d+)$/);
        if (!m) throw new Error(`"${p}" should look like left,size`);
        const left = +m[1], size = +m[2];
        if (size <= 0) throw new Error('size must be positive');
        return [left, size];
      })
    };
  },
  run({ positions }) {
    const { F, snap } = avRecorder();
    const coordSet = new Set();
    positions.forEach(([l, sz]) => { coordSet.add(l); coordSet.add(l + sz); });
    const coords = [...coordSet].sort((a, b) => a - b);
    const leafN = coords.length - 1;
    snap(2, `Coordinate-compress every edge: ${coords.length} distinct x's → ${leafN} leaf interval${leafN === 1 ? '' : 's'}.`, { positions, coords, ranges: {}, tree: {}, lazy: {}, cur: null, kind: null, result: [], running: 0 });

    /* visualization keys are 1-indexed (root=1, children 2k/2k+1) regardless
       of the real solution's 0-indexed array layout — same recursive shape. */
    const ranges = {}, tree = {}, lazy = {};
    const initRange = (key, l, r) => { ranges[key] = [l, r]; tree[key] = 0; lazy[key] = 0; if (l < r) { const mid = (l + r) >> 1; initRange(2 * key, l, mid); initRange(2 * key + 1, mid + 1, r); } };
    if (leafN >= 1) initRange(1, 0, leafN - 1);
    const S = (extra = {}) => ({ positions, coords, ranges: { ...ranges }, tree: { ...tree }, lazy: { ...lazy }, result: [...result], running, squareIdx: null, ...extra });

    const pushDown = key => { if (lazy[key]) { for (const kid of [2 * key, 2 * key + 1]) { tree[kid] = lazy[key]; lazy[kid] = lazy[key]; } lazy[key] = 0; } };
    const bisectLeft = x => { let lo = 0, hi = coords.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (coords[mid] < x) lo = mid + 1; else hi = mid; } return lo; };

    const query = (l, r, key, s, e) => {
      if (r < s || e < l) { snap(8, `Node [${s},${e}] is outside the query — return 0.`, S({ cur: key, kind: 'out', qLo: l, qHi: r })); return 0; }
      if (l <= s && e <= r) { snap(8, `Node [${s},${e}] fully inside the query — return its stored max ${tree[key]}.`, S({ cur: key, kind: 'in', qLo: l, qHi: r })); return tree[key]; }
      pushDown(key);
      snap(8, `Node [${s},${e}] partly overlaps — push any pending lazy value down, then split.`, S({ cur: key, kind: 'partial', qLo: l, qHi: r }));
      const mid = (s + e) >> 1;
      return Math.max(query(l, r, 2 * key, s, mid), query(l, r, 2 * key + 1, mid + 1, e));
    };
    const update = (l, r, val, key, s, e) => {
      if (r < s || e < l) return;
      if (l <= s && e <= r) { tree[key] = val; lazy[key] = val; snap(10, `Node [${s},${e}] fully inside the update — assign ${val} and mark it lazy (children updated only if we ever visit them).`, S({ cur: key, kind: 'assign', qLo: l, qHi: r })); return; }
      pushDown(key);
      const mid = (s + e) >> 1;
      update(l, r, val, 2 * key, s, mid); update(l, r, val, 2 * key + 1, mid + 1, e);
      tree[key] = Math.max(tree[2 * key], tree[2 * key + 1]);
      snap(10, `On the way back up: node [${s},${e}] becomes max(children) = ${tree[key]}.`, S({ cur: key, kind: 'combine', qLo: l, qHi: r }));
    };

    const result = []; let running = 0;
    positions.forEach(([left, size], idx) => {
      const right = left + size;
      const lIdx = bisectLeft(left), rIdx = bisectLeft(right) - 1;
      snap(6, `Square ${idx + 1}: [${left}, ${right}) covers leaf interval [${lIdx}, ${rIdx}].`, S({ cur: null, kind: 'start', qLo: lIdx, qHi: rIdx, squareIdx: idx, result: [...result], running }));
      const base = leafN >= 1 ? query(lIdx, rIdx, 1, 0, leafN - 1) : 0;
      const landing = base + size;
      snap(9, `Base height under the footprint is ${base}, so this square lands at height ${landing}.`, S({ cur: null, kind: 'landed', qLo: lIdx, qHi: rIdx, squareIdx: idx, result: [...result], running }));
      if (leafN >= 1) update(lIdx, rIdx, landing, 1, 0, leafN - 1);
      running = Math.max(running, landing);
      result.push(running);
      snap(12, `running_max = max(${running}, previous) → result[${idx}] = ${running}.`, S({ cur: null, kind: null, qLo: null, qHi: null, squareIdx: idx, result: [...result], running }));
    });
    snap(13, `Final heights after each square lands: [${result.join(', ')}].`, S({ cur: null, kind: null, qLo: null, qHi: null, squareIdx: null, result: [...result], running }));
    return F;
  },
  height: (w, last) => 70 + (Math.max(1, Math.ceil(Math.log2(Math.max(2, Object.keys(last.ranges).length)))) + 1) * 50 + 90,
  draw(ctx, c, f, P) {
    const keys = Object.keys(f.ranges).map(Number);
    if (!keys.length) { D.text(ctx, '(no leaf intervals yet)', c.w / 2, 40, { color: P.faint, size: 13, align: 'center' }); return; }
    const levels = {};
    keys.forEach(k => { const d = Math.floor(Math.log2(k)); (levels[d] ??= []).push(k); });
    Object.values(levels).forEach(l => l.sort((a, b) => f.ranges[a][0] - f.ranges[b][0]));
    const xy = {};
    Object.entries(levels).forEach(([d, list]) => list.forEach((node, i) => { xy[node] = [24 + (i + .5) * (c.w - 48) / list.length, 34 + (+d) * 50]; }));
    keys.forEach(node => { const parent = node >> 1; if (node > 1 && xy[parent]) D.line(ctx, xy[parent][0], xy[parent][1] + 13, xy[node][0], xy[node][1] - 13, P.strong, 1.1); });
    const wNode = Math.min(52, (c.w - 48) / Math.max(...Object.values(levels).map(l => l.length)) - 6);
    keys.forEach(node => {
      const [x, y] = xy[node], [l, r] = f.ranges[node];
      const isCur = node === f.cur;
      ctx.fillStyle = isCur ? P.alpha(f.kind === 'in' || f.kind === 'assign' ? 'ok' : f.kind === 'out' ? 'err' : 'accent', .38) : f.lazy[node] ? P.alpha('accent', .12) : P.surface2;
      D.rrect(ctx, x - wNode / 2, y - 14, wNode, 28, 7); ctx.fill();
      ctx.strokeStyle = isCur ? (f.kind === 'out' ? P.err : P.ok) : P.strong; ctx.lineWidth = isCur ? 2.2 : 1; ctx.stroke();
      D.text(ctx, String(f.tree[node]), x, y - 2, { color: P.text, size: 12, align: 'center', mono: true, weight: 700 });
      D.text(ctx, l === r ? `[${l}]` : `${l}-${r}`, x, y + 9, { color: P.faint, size: 9, align: 'center', mono: true });
    });
    const bottom = 34 + Object.keys(levels).length * 50 + 20;
    D.text(ctx, f.squareIdx != null ? `square ${f.squareIdx + 1} of ${f.positions.length} — footprint leaves [${f.qLo}, ${f.qHi}]` : 'segment tree over compressed x-coordinates', 20, bottom, { color: P.dim, size: 12, weight: 650 });
    D.text(ctx, `heights after each square lands: [${f.result.join(', ')}]${f.result.length < f.positions.length ? ' …' : ''}`, 20, bottom + 20, { color: P.ok, size: 12.5, weight: 700, mono: true });
    D.text(ctx, `running_max = ${f.running}`, 20, bottom + 40, { color: P.accent, size: 12, weight: 650, mono: true });
  },
});

/* ============================================================ 006 · The Skyline Problem */
defineAlgo('26_segment_tree_fenwick', {
  title: 'The Skyline Problem', short: 'Skyline',
  idea: 'Sweep left to right over every building edge. A max-heap holds the "live" buildings at the current x, keyed by (-height, right edge) — the top is always the tallest live building. At each x: push any buildings starting here, lazily pop any that have already ended, then the new skyline height is whatever is left on top (or 0). A key point is only recorded when that height actually changes.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '2,9,10;3,7,15;5,12,12;15,20,10;19,24,8', hint: 'left,right,height ; ...',
  code: [
    'starts = defaultdict(list)   # left edge -> [(height, right), ...]',
    'xs = sorted({x for l, r, h in buildings for x in (l, r)})',
    'live = []                    # max-heap via (-height, right)',
    'result = []',
    'for x in xs:',
    '    for height, right in starts[x]:',
    '        heappush(live, (-height, right))',
    '    while live and live[0][1] <= x:',
    '        heappop(live)                       # lazy deletion of expired buildings',
    '    cur_max = -live[0][0] if live else 0',
    '    if not result or result[-1][1] != cur_max:',
    '        result.append([x, cur_max])',
  ],
  parse(s) {
    const parts = String(s || '').split(';').map(x => x.trim()).filter(Boolean);
    if (!parts.length) throw new Error('Enter at least one building as left,right,height');
    if (parts.length > 6) throw new Error('Use at most 6 buildings so the animation stays readable');
    return {
      buildings: parts.map(p => {
        const m = p.match(/^(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)$/);
        if (!m) throw new Error(`"${p}" should look like left,right,height`);
        const left = +m[1], right = +m[2], height = +m[3];
        if (left >= right) throw new Error('left must be less than right');
        if (height <= 0) throw new Error('height must be positive');
        return { left, right, height };
      })
    };
  },
  run({ buildings }) {
    const { F, snap } = avRecorder();
    const starts = {};
    const xsSet = new Set();
    buildings.forEach(b => { (starts[b.left] ??= []).push({ height: b.height, right: b.right }); xsSet.add(b.left); xsSet.add(b.right); });
    const xs = [...xsSet].sort((a, b) => a - b);
    let live = [];
    const result = [];
    snap(2, `Collect every left edge's buildings, and every edge into the sweep set of x's: [${xs.join(', ')}].`, { buildings, xs, x: null, live: [], result: [...result] });
    xs.forEach(x => {
      (starts[x] || []).forEach(({ height, right }) => {
        live.push([height, right]);
        live.sort((a, b) => b[0] - a[0]);
        snap(6, `New building starts at x=${x}: push (height ${height}, ends at ${right}) — the live set stays sorted so the top is the tallest.`, { buildings, xs, x, live: live.map(v => [...v]), result: [...result] });
      });
      while (live.length && live[0][1] <= x) {
        const popped = live.shift();
        snap(8, `Building (height ${popped[0]}, ends at ${popped[1]}) has already ended at x=${x} — pop it (lazy deletion).`, { buildings, xs, x, live: live.map(v => [...v]), result: [...result] });
      }
      const curMax = live.length ? live[0][0] : 0;
      const changed = !result.length || result[result.length - 1][1] !== curMax;
      if (changed) result.push([x, curMax]);
      snap(11, changed ? `Height changed to ${curMax} — record key point (${x}, ${curMax}).` : `Height is still ${curMax} — no new key point.`,
        { buildings, xs, x, live: live.map(v => [...v]), result: [...result], justAdded: changed });
    });
    snap(11, `Skyline complete — ${result.length} key point${result.length === 1 ? '' : 's'}.`, { buildings, xs, x: null, live: [], result: [...result], done: true });
    return F;
  },
  height: () => 340,
  draw(ctx, c, f, P) {
    const minX = Math.min(...f.buildings.map(b => b.left)), maxX = Math.max(...f.buildings.map(b => b.right));
    const maxH = Math.max(...f.buildings.map(b => b.height));
    const v = D.view(c, { x0: minX, x1: maxX, y0: 0, y1: maxH * 1.15, pad: 24, padB: 90 });
    f.buildings.forEach(b => {
      const live = f.live.some(([h, r]) => h === b.height && r === b.right) || (f.x != null && f.x >= b.left && f.x < b.right);
      ctx.fillStyle = P.alpha('accent', live ? .28 : .1);
      D.rrect(ctx, v.sx(b.left), v.sy(b.height), v.sx(b.right) - v.sx(b.left), v.sy(0) - v.sy(b.height), 3); ctx.fill();
      ctx.strokeStyle = P.alpha('accent', live ? .8 : .3); ctx.lineWidth = 1.4;
      D.rrect(ctx, v.sx(b.left), v.sy(b.height), v.sx(b.right) - v.sx(b.left), v.sy(0) - v.sy(b.height), 3); ctx.stroke();
    });
    if (f.result.length) {
      ctx.save(); ctx.strokeStyle = P.ok; ctx.lineWidth = 2.4; ctx.beginPath();
      let prevY = v.sy(0);
      ctx.moveTo(v.sx(f.result[0][0]), prevY);
      f.result.forEach(([x, h]) => { ctx.lineTo(v.sx(x), prevY); ctx.lineTo(v.sx(x), v.sy(h)); prevY = v.sy(h); });
      const endX = f.x != null ? f.x : f.buildings.reduce((m, b) => Math.max(m, b.right), minX);
      ctx.lineTo(v.sx(endX), prevY);
      ctx.stroke(); ctx.restore();
      f.result.forEach(([x, h]) => D.dot(ctx, v.sx(x), v.sy(h), 3.4, P.ok));
    }
    if (f.x != null) D.line(ctx, v.sx(f.x), v.sy(0) + 4, v.sx(f.x), v.sy(maxH * 1.15), P.err, 1.6, [4, 4]);
    D.text(ctx, f.x != null ? `sweeping x = ${f.x}` : f.done ? 'done' : 'ready', 20, 16, { color: P.dim, size: 12, weight: 650, mono: true });
    const liveLabel = f.live.length ? `live (tallest first): ${f.live.map(([h, r]) => `${h}@${r}`).join(', ')}` : 'live: (empty)';
    D.text(ctx, liveLabel, 20, v.sy(0) + 34, { color: P.accent, size: 12, weight: 650, mono: true });
    D.text(ctx, `skyline so far: [${f.result.map(p => `(${p[0]},${p[1]})`).join(', ')}]`, 20, v.sy(0) + 54, { color: P.ok, size: 11.5, mono: true });
  },
});
