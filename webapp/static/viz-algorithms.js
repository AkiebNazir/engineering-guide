'use strict';

const ALGOS_ALGORITHMS = '27_algorithms';

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Shuffle an Array', short: 'Shuffle',
  idea: 'Fisher-Yates shuffle: walk the array backwards, swap each element with a randomly chosen element from the un-shuffled portion.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 2, 3, 4, 5', hint: 'numbers',
  code: [
    'def shuffle(self) -> list[int]:',
    '    arr = self._array',
    '    n = len(arr)',
    '    for i in range(n - 1, 0, -1):',
    '        j = random.randint(0, i)',
    '        arr[i], arr[j] = arr[j], arr[i]',
    '    return arr'
  ],
  parse(s) { return { nums: avNums(s, 14) }; },
  buildStates({ nums }) {
    const seq = [];
    const arr = [...nums];
    const n = arr.length;
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 2, color: 'default',
      arr: [...arr], i: -1, j: -1,
      explTitle: 'Initialization',
      explText: 'Start with the original array.',
      pause: true
    });
    
    for(let i = n - 1; i > 0; i--) {
        pushState({
          kind: 'loop', line: 4, color: 'default',
          arr: [...arr], i, j: -1,
          explTitle: `Step i = ${i}`,
          explText: `At index ${i}, choose a random index in [0, ${i}].`
        });
        
        // Random for the visualization
        let j = 0;
        // Seeded random so it doesn't change during stepping back and forth?
        // Actually buildStates is called once, so the sequence is fixed.
        j = Math.floor(Math.random() * (i + 1));
        
        pushState({
          kind: 'pick-j', line: 5, color: 'amber',
          arr: [...arr], i, j,
          explTitle: `Random j = ${j}`,
          explText: `Randomly picked index ${j} from the range [0, ${i}].`
        });
        
        const temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
        
        pushState({
          kind: 'swap', line: 6, color: 'emerald',
          arr: [...arr], i, j,
          explTitle: 'Swap',
          explText: `Swapped arr[${i}] and arr[${j}]. Index ${i} is now final.`,
          pause: true
        });
    }
    
    pushState({
      kind: 'done', line: 7, color: 'default',
      arr: [...arr], i: -1, j: -1,
      explTitle: 'Done',
      explText: 'The array is fully shuffled.',
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = () => s.arr.map((v, idx) => {
      const isI = idx === s.i;
      const isJ = idx === s.j;
      const isFinal = s.i !== -1 && idx > s.i;
      let cls = '';
      if (isI || isJ) cls = 'active-k';
      else if (isFinal) cls = 'merged';
      
      let ptr = '';
      if (isI && isJ) ptr = '<div class="pointer" style="color:var(--accent)">↓ i, j</div>';
      else if (isI) ptr = '<div class="pointer" style="color:var(--accent)">↓ i</div>';
      else if (isJ) ptr = '<div class="pointer" style="color:#fb7185">↓ j</div>';
      
      return `<div class="array-node ${cls}" style="${isFinal ? 'opacity:0.5' : ''}">
        ${ptr}
        ${v}<div class="node-index">${idx}</div></div>`;
    }).join('');
    
    container.innerHTML = `
      <div class="glass-panel arrays-container"><div>
        <div class="panel-heading" style="color:var(--accent);">Array</div>
        <div class="array-track" style="padding-bottom:24px;">${getArrayHTML()}</div>
      </div></div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Random Pick Index', short: 'Pick Index',
  idea: 'Reservoir sampling: scan the array. When we see the target for the k-th time, we keep this new index with probability 1/k. This ensures all target occurrences have equal probability of being picked without storing them in a list.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 3, 3 ; 3', hint: 'numbers ; target',
  code: [
    'def pick(self, target: int) -> int:',
    '    count = 0',
    '    result = -1',
    '    for i, value in enumerate(self.nums):',
    '        if value == target:',
    '            count += 1',
    '            if random.randint(1, count) == 1:',
    '                result = i',
    '    return result'
  ],
  parse(s) { const [a, t] = avParts(s); return { nums: avNums(a, 14), target: avNum(t, 'target') }; },
  buildStates({ nums, target }) {
    const seq = [];
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 2, color: 'default',
      nums, target, count: 0, result: -1, i: -1, value: null, rand: null,
      explTitle: 'Initialization',
      explText: `We are looking for target = ${target}. Initialize count = 0, result = -1.`,
      pause: true
    });
    
    let count = 0;
    let result = -1;
    
    for(let i = 0; i < nums.length; i++) {
        const value = nums[i];
        pushState({
          kind: 'loop', line: 4, color: 'default',
          nums, target, count, result, i, value, rand: null,
          explTitle: `Index ${i}`,
          explText: `Look at nums[${i}] = ${value}.`
        });
        
        if (value === target) {
            count += 1;
            pushState({
              kind: 'match', line: 6, color: 'blue',
              nums, target, count, result, i, value, rand: null,
              explTitle: 'Match Found',
              explText: `Value matches target! This is match #${count}.`
            });
            
            // Random visualization
            // Pick randomly? Or hardcode for visualization?
            // To make the visualizer useful, let's just use pseudo-random that can be played
            const rand = Math.floor(Math.random() * count) + 1;
            const keep = rand === 1;
            
            pushState({
              kind: 'random', line: 7, color: keep ? 'emerald' : 'amber',
              nums, target, count, result, i, value, rand,
              explTitle: 'Coin Flip',
              explText: `Draw a random number from 1 to ${count}. We got ${rand}. ` +
                        (keep ? `Since it is 1, we KEEP this index.` : `Since it is not 1, we DO NOT keep it.`)
            });
            
            if (keep) {
                result = i;
                pushState({
                  kind: 'keep', line: 8, color: 'emerald',
                  nums, target, count, result, i, value, rand,
                  explTitle: 'Update Result',
                  explText: `Result is now ${result}.`,
                  pause: true
                });
            }
        } else {
            pushState({
              kind: 'no-match', line: 4, color: 'default',
              nums, target, count, result, i, value, rand: null,
              explTitle: 'No Match',
              explText: `Value ${value} does not match target ${target}. Skip.`
            });
        }
    }
    
    pushState({
      kind: 'done', line: 9, color: 'default',
      nums, target, count, result, i: -1, value: null, rand: null,
      explTitle: 'Done',
      explText: `Finished scanning. Returning result = ${result}.`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = () => s.nums.map((v, idx) => {
      const isI = idx === s.i;
      const isRes = idx === s.result;
      const isTarget = v === s.target;
      
      let cls = '';
      if (isI) cls = 'active-1';
      if (isRes) cls += ' active-k'; // might override, we can use merged
      if (!isI && !isRes && !isTarget) cls = 'merged';
      
      let ptr = '';
      if (isRes) ptr += '<div class="pointer" style="color:#10b981; bottom:-20px; top:auto;">↑ res</div>';
      if (isI) ptr += '<div class="pointer" style="color:var(--accent)">↓ i</div>';
      
      return `<div class="array-node ${cls}" style="${(!isI && !isRes && !isTarget) ? 'opacity:0.4' : ''}; border-color:${isTarget ? 'var(--accent)' : ''}">
        ${ptr}
        ${v}<div class="node-index">${idx}</div></div>`;
    }).join('');
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">nums (target = ${s.target})</div>
          <div class="array-track" style="padding-bottom:24px;">${getArrayHTML()}</div>
        </div>
      </div>
      <div class="glass-panel">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Match Count</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:var(--text);">${s.count}</div>
            </div>
            <div style="text-align:center; opacity:${s.rand ? 1 : 0.3};">
                <div style="font-size:0.8rem; color:var(--text-dim);">Random (1 to count)</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.rand === 1 ? '#10b981' : '#fb7185'};">${s.rand || '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Result</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.result !== -1 ? '#10b981' : 'var(--text)'};">${s.result}</div>
            </div>
        </div>
      </div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Random Pick with Weight', short: 'Pick Weight',
  idea: 'Prefix sums + Binary search: imagine laying the weights out end-to-end like segments on a ruler. Pick a random point on the ruler, then binary search to find which segment it landed in.',
  complexity: 'Time O(log n) per pick · Space O(n)',
  input: '1, 3, 2, 4', hint: 'weights',
  code: [
    'def pickIndex(self) -> int:',
    '    target = random.randint(1, self.total)',
    '    # prefix sum array e.g., [1, 4, 6, 10]',
    '    lo, hi = 0, len(self.prefix) - 1',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if self.prefix[mid] < target:',
    '            lo = mid + 1',
    '        else:',
    '            hi = mid',
    '    return lo'
  ],
  parse(s) { return { w: avNums(s, 10) }; },
  buildStates({ w }) {
    const seq = [];
    const prefix = [];
    let running = 0;
    for (let x of w) {
        running += x;
        prefix.push(running);
    }
    const total = running;
    
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      w, prefix, total, target: null, lo: 0, hi: prefix.length - 1, mid: null, result: null,
      explTitle: 'Initialization',
      explText: `We have precomputed the prefix sums: [${prefix.join(', ')}]. Total sum is ${total}.`,
      pause: true
    });
    
    const target = Math.floor(Math.random() * total) + 1;
    let lo = 0;
    let hi = prefix.length - 1;
    
    pushState({
      kind: 'target', line: 2, color: 'amber',
      w, prefix, total, target, lo, hi, mid: null, result: null,
      explTitle: 'Random Target',
      explText: `Randomly picked target ${target} from range [1, ${total}]. Now we binary search.`
    });
    
    while (lo < hi) {
        const mid = Math.floor((lo + hi) / 2);
        pushState({
          kind: 'binary-search', line: 5, color: 'default',
          w, prefix, total, target, lo, hi, mid, result: null,
          explTitle: 'Calculate Mid',
          explText: `lo = ${lo}, hi = ${hi}. mid = ${mid}. prefix[mid] = ${prefix[mid]}.`
        });
        
        if (prefix[mid] < target) {
            pushState({
              kind: 'go-right', line: 7, color: 'blue',
              w, prefix, total, target, lo, hi, mid, result: null,
              explTitle: 'Search Right',
              explText: `prefix[mid] (${prefix[mid]}) < target (${target}), so we go right.`
            });
            lo = mid + 1;
        } else {
            pushState({
              kind: 'go-left', line: 9, color: 'blue',
              w, prefix, total, target, lo, hi, mid, result: null,
              explTitle: 'Search Left',
              explText: `prefix[mid] (${prefix[mid]}) >= target (${target}), so we go left (include mid).`
            });
            hi = mid;
        }
    }
    
    pushState({
      kind: 'done', line: 10, color: 'emerald',
      w, prefix, total, target, lo, hi, mid: null, result: lo,
      explTitle: 'Done',
      explText: `lo == hi == ${lo}. Target ${target} falls into segment ${lo}. Returning ${lo}.`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getPrefixHTML = () => s.prefix.map((v, idx) => {
      const inRange = idx >= s.lo && idx <= s.hi;
      const isMid = idx === s.mid;
      const isRes = idx === s.result;
      
      let cls = '';
      if (isRes) cls = 'active-k';
      else if (isMid) cls = 'active-1';
      else if (inRange) cls = '';
      else cls = 'merged';
      
      let ptr = '';
      if (idx === s.lo) ptr += '<div class="pointer" style="color:var(--accent); top:-20px;">↓ lo</div>';
      if (idx === s.hi) ptr += '<div class="pointer" style="color:var(--accent); top:-35px;">↓ hi</div>';
      if (isMid) ptr += '<div class="pointer" style="color:#fb7185; bottom:-20px; top:auto;">↑ mid</div>';
      if (isRes) ptr += '<div class="pointer" style="color:#10b981; bottom:-20px; top:auto;">↑ res</div>';
      
      return `<div class="array-node ${cls}" style="${!inRange && !isRes ? 'opacity:0.3' : ''};">
        ${ptr}
        ${v}<div class="node-index">${idx} (w:${s.w[idx]})</div></div>`;
    }).join('');
    
    container.innerHTML = `
      <div class="glass-panel" style="text-align:center; padding:10px;">
        <span style="color:var(--text-dim); margin-right:10px;">Target (1 to ${s.total}):</span>
        <span style="font-size:1.5rem; font-family:var(--mono); color:${s.target ? '#fb7185' : 'var(--text)'};">${s.target || '-'}</span>
      </div>
      <div class="glass-panel arrays-container" style="margin-top:10px;">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Prefix Sum Array</div>
          <div class="array-track" style="padding-top:24px; padding-bottom:24px;">${getPrefixHTML()}</div>
        </div>
      </div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Linked List Random Node', short: 'List Random',
  idea: 'Reservoir sampling over a stream: as we traverse the linked list, when we are at the k-th node, we replace our chosen value with the current node\'s value with probability 1/k.',
  complexity: 'Time O(n) · Space O(1)',
  input: '10, 20, 30, 40, 50', hint: 'list values',
  code: [
    'def getRandom(self) -> int:',
    '    result = None',
    '    count = 0',
    '    node = self.head',
    '    while node is not None:',
    '        count += 1',
    '        if random.randint(1, count) == 1:',
    '            result = node.val',
    '        node = node.next',
    '    return result'
  ],
  parse(s) { return { vals: avNums(s, 10) }; },
  buildStates({ vals }) {
    const seq = [];
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 2, color: 'default',
      vals, count: 0, result: null, i: -1, rand: null,
      explTitle: 'Initialization',
      explText: 'Start with count = 0, result = None. We traverse the linked list.',
      pause: true
    });
    
    let count = 0;
    let result = null;
    
    for(let i = 0; i < vals.length; i++) {
        const val = vals[i];
        pushState({
          kind: 'loop', line: 5, color: 'default',
          vals, count, result, i, rand: null,
          explTitle: `Node ${i + 1}`,
          explText: `Current node value is ${val}.`
        });
        
        count += 1;
        const rand = Math.floor(Math.random() * count) + 1;
        const keep = rand === 1;
        
        pushState({
          kind: 'random', line: 7, color: keep ? 'emerald' : 'amber',
          vals, count, result, i, rand,
          explTitle: 'Coin Flip',
          explText: `Node is the ${count}-th node. Draw random number from 1 to ${count}. We got ${rand}.`
        });
        
        if (keep) {
            result = val;
            pushState({
              kind: 'keep', line: 8, color: 'emerald',
              vals, count, result, i, rand,
              explTitle: 'Update Result',
              explText: `Random number is 1, so we KEEP this node's value. Result = ${result}.`,
              pause: true
            });
        }
        
        pushState({
          kind: 'next', line: 9, color: 'default',
          vals, count, result, i, rand: null,
          explTitle: 'Move to Next',
          explText: 'node = node.next'
        });
    }
    
    pushState({
      kind: 'done', line: 10, color: 'default',
      vals, count, result, i: -1, rand: null,
      explTitle: 'Done',
      explText: `Reached end of list. Returning ${result}.`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getListHTML = () => s.vals.map((v, idx) => {
      const isI = idx === s.i;
      
      let cls = '';
      if (isI) cls = 'active-1';
      else cls = 'merged';
      
      let ptr = '';
      if (isI) ptr += '<div class="pointer" style="color:var(--accent)">↓ node</div>';
      
      const isRes = v === s.result;
      const boxStyle = isRes ? 'border: 2px solid #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);' : '';
      
      const nodeHtml = `<div class="array-node ${cls}" style="${idx > s.i && s.i !== -1 ? 'opacity:0.4' : ''}; ${boxStyle}">
        ${ptr}
        ${v}</div>`;
        
      if (idx < s.vals.length - 1) {
          return nodeHtml + `<div style="display:flex; align-items:center; color:var(--text-dim); margin:0 4px;">→</div>`;
      }
      return nodeHtml;
    }).join('');
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Linked List</div>
          <div class="array-track" style="padding-bottom:24px; padding-top:24px;">${getListHTML()}</div>
        </div>
      </div>
      <div class="glass-panel">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Match Count</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:var(--text);">${s.count}</div>
            </div>
            <div style="text-align:center; opacity:${s.rand ? 1 : 0.3};">
                <div style="font-size:0.8rem; color:var(--text-dim);">Random (1 to count)</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.rand === 1 ? '#10b981' : '#fb7185'};">${s.rand || '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Result</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.result !== null ? '#10b981' : 'var(--text)'};">${s.result === null ? 'None' : s.result}</div>
            </div>
        </div>
      </div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Random Pick with Blacklist', short: 'Pick Blacklist',
  idea: 'Remap blacklisted indices in the valid range to available whitelisted indices at the end of the range. Then simply draw a random number in the valid range and apply the remap if needed.',
  complexity: 'Time O(B) init, O(1) pick · Space O(B)',
  input: '7 ; 2, 3, 5', hint: 'N ; blacklist',
  code: [
    'def pick(self) -> int:',
    '    r = random.randint(0, self.whitelist_size - 1)',
    '    if r in self.remap:',
    '        return self.remap[r]',
    '    return r'
  ],
  parse(s) { const [nStr, bStr] = avParts(s); return { n: avNum(nStr, 'N'), blacklist: avNums(bStr || '100', 14) }; },
  buildStates({ n, blacklist }) {
    const seq = [];
    const bSet = new Set(blacklist);
    const wSize = n - blacklist.length;
    const remap = {};
    
    function pushState(s) { seq.push(s); }
    
    // Compute remap map
    let last = n - 1;
    for (let b of blacklist) {
        if (b < wSize) {
            while (bSet.has(last)) {
                last--;
            }
            remap[b] = last;
            last--;
        }
    }
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      n, blacklist, wSize, remap, r: null, result: null,
      explTitle: 'Initialization',
      explText: `N = ${n}, Blacklist = [${blacklist.join(', ')}]. Whitelist size = ${wSize}. Remap map computed: ${JSON.stringify(remap)}.`,
      pause: true
    });
    
    const r = Math.floor(Math.random() * wSize);
    
    pushState({
      kind: 'pick', line: 2, color: 'amber',
      n, blacklist, wSize, remap, r, result: null,
      explTitle: 'Random Draw',
      explText: `Draw a random index from [0, ${wSize - 1}]. We got ${r}.`
    });
    
    if (r in remap) {
        pushState({
          kind: 'remap', line: 4, color: 'blue',
          n, blacklist, wSize, remap, r, result: remap[r],
          explTitle: 'Remap Applied',
          explText: `${r} is blacklisted, so we use its remapped value: ${remap[r]}.`
        });
    } else {
        pushState({
          kind: 'no-remap', line: 5, color: 'emerald',
          n, blacklist, wSize, remap, r, result: r,
          explTitle: 'No Remap',
          explText: `${r} is not blacklisted in the valid range. We keep it.`
        });
    }
    
    pushState({
      kind: 'done', line: -1, color: 'emerald',
      n, blacklist, wSize, remap, r, result: r in remap ? remap[r] : r,
      explTitle: 'Done',
      explText: `Final result is ${r in remap ? remap[r] : r}.`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = () => {
        let html = '';
        for (let idx = 0; idx < s.n; idx++) {
            const isBlacklisted = s.blacklist.includes(idx);
            const inValidRange = idx < s.wSize;
            const isR = idx === s.r;
            const isRes = idx === s.result;
            
            let cls = '';
            if (isRes) cls = 'active-k';
            else if (isR) cls = 'active-1';
            else if (!inValidRange && !isRes) cls = 'merged';
            
            let ptr = '';
            if (isR) ptr += '<div class="pointer" style="color:var(--accent)">↓ r</div>';
            if (isRes) ptr += '<div class="pointer" style="color:#10b981; bottom:-20px; top:auto;">↑ res</div>';
            
            let boxStyle = isBlacklisted ? 'background: rgba(251, 113, 133, 0.1); border-color: #fb7185; color: #fb7185;' : '';
            if (isRes && isBlacklisted) boxStyle += 'border: 2px solid #10b981; color: var(--text);';
            else if (isRes) boxStyle += 'border: 2px solid #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);';
            
            let remapLabel = '';
            if (s.remap[idx] !== undefined) {
                remapLabel = `<div style="position:absolute; top:-25px; left:50%; transform:translateX(-50%); font-size:10px; color:var(--text-dim); white-space:nowrap;">→ ${s.remap[idx]}</div>`;
            }
            
            html += `<div class="array-node ${cls}" style="${!inValidRange && !isRes ? 'opacity:0.4' : ''}; ${boxStyle} position:relative;">
              ${remapLabel}
              ${ptr}
              ${idx}
              ${isBlacklisted ? '<div style="font-size:10px;">(X)</div>' : ''}
              </div>`;
              
            if (idx === s.wSize - 1 && idx < s.n - 1) {
                html += `<div style="border-right: 2px dashed var(--border); margin: 0 10px; height: 40px;"></div>`;
            }
        }
        return html;
    };
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Indices (0 to ${s.n - 1})</div>
          <div class="array-track" style="padding-bottom:24px; padding-top:24px;">${getArrayHTML()}</div>
        </div>
      </div>
      <div class="glass-panel">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Valid Range</div>
                <div style="font-size:1.1rem; font-family:var(--mono); color:var(--text);">0 to ${s.wSize - 1}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Random r</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.r !== null ? '#3b82f6' : 'var(--text)'};">${s.r !== null ? s.r : '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Result</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.result !== null ? '#10b981' : 'var(--text)'};">${s.result !== null ? s.result : '-'}</div>
            </div>
        </div>
      </div>
    `;
  }
});


defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Find the Kth Largest Integer in a String', short: 'Kth Largest Str',
  idea: 'String numbers can be compared by length first, then lexicographically if lengths are equal. This avoids converting massive strings to ints. We can use QuickSelect to find the Kth largest element in O(n) average time.',
  complexity: 'Time O(n) average · Space O(n)',
  input: '3, 6, 7, 10 ; 4', hint: 'nums (comma separated) ; k',
  code: [
    'def compare(a: str, b: str) -> int:',
    '    if len(a) != len(b):',
    '        return 1 if len(a) > len(b) else -1',
    '    if a == b:',
    '        return 0',
    '    return 1 if a > b else -1',
    '',
    '# ... used in QuickSelect or Sorting ...'
  ],
  parse(s) { 
      const [nStr, kStr] = avParts(s); 
      const nums = String(nStr || '').split(/[\s,]+/).filter(Boolean);
      return { nums, k: avNum(kStr, 'k') }; 
  },
  buildStates({ nums, k }) {
    const seq = [];
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      nums, k, a: null, b: null, result: null,
      explTitle: 'Initialization',
      explText: `We want to find the ${k}th largest element. Let's see how comparing two strings works.`,
      pause: true
    });
    
    if (nums.length >= 2) {
        const a = nums[0];
        const b = nums[1];
        
        pushState({
          kind: 'compare-len', line: 2, color: 'blue',
          nums, k, a, b, result: null,
          explTitle: 'Compare Lengths',
          explText: `Comparing "${a}" (len ${a.length}) and "${b}" (len ${b.length}).`
        });
        
        if (a.length !== b.length) {
            const res = a.length > b.length ? 1 : -1;
            pushState({
              kind: 'len-diff', line: 3, color: 'emerald',
              nums, k, a, b, result: res,
              explTitle: 'Different Lengths',
              explText: `Lengths differ. "${a}" is ${res === 1 ? 'larger' : 'smaller'} than "${b}".`
            });
        } else {
            pushState({
              kind: 'lexicographical', line: 6, color: 'emerald',
              nums, k, a, b, result: a > b ? 1 : (a < b ? -1 : 0),
              explTitle: 'Same Length',
              explText: `Lengths are equal. We compare lexicographically character by character.`
            });
        }
    }
    
    // Sort array just to show the final result
    const sorted = [...nums].sort((a, b) => {
        if (a.length !== b.length) return b.length - a.length;
        return a < b ? 1 : (a > b ? -1 : 0);
    });
    const ans = sorted[k - 1];
    
    pushState({
      kind: 'done', line: 7, color: 'default',
      nums: sorted, k, a: null, b: null, result: ans,
      explTitle: 'Result (Sorted Array)',
      explText: `The ${k}th largest element (index ${k-1}) is "${ans}".`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = () => s.nums.map((v, idx) => {
      const isAns = s.kind === 'done' && idx === s.k - 1;
      
      let cls = '';
      if (isAns) cls = 'active-k';
      else cls = 'merged';
      
      let ptr = '';
      if (isAns) ptr += '<div class="pointer" style="color:#10b981; bottom:-20px; top:auto;">↑ ans</div>';
      
      return `<div class="array-node ${cls}" style="${isAns ? 'border: 2px solid #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);' : ''}">
        ${ptr}
        ${v}</div>`;
    }).join('');
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Strings Array ${s.kind === 'done' ? '(Sorted Descending)' : ''}</div>
          <div class="array-track" style="padding-bottom:24px; padding-top:24px;">${getArrayHTML()}</div>
        </div>
      </div>
      ${s.a !== null ? `<div class="glass-panel">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">String A</div>
                <div style="font-size:1.2rem; font-family:var(--mono); color:var(--text);">"${s.a}" (len ${s.a.length})</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Result</div>
                <div style="font-size:1.2rem; font-family:var(--mono); color:#10b981;">${s.result !== null ? s.result : '?'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">String B</div>
                <div style="font-size:1.2rem; font-family:var(--mono); color:var(--text);">"${s.b}" (len ${s.b.length})</div>
            </div>
        </div>
      </div>` : ''}
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Wiggle Sort II', short: 'Wiggle Sort II',
  idea: 'Virtual Indexing: By mapping indices to (1 + 2*i) % (n|1), we can put all elements larger than median in odd indices and elements smaller than median in even indices.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 5, 1, 1, 6, 4', hint: 'numbers',
  code: [
    'def A(i, n):',
    '    # Map i to virtual index',
    '    return (1 + 2 * i) % (n | 1)',
    '',
    '# Then run three-way partition over A(i)'
  ],
  parse(s) { return { nums: avNums(s, 10) }; },
  buildStates({ nums }) {
    const seq = [];
    function pushState(s) { seq.push(s); }
    const n = nums.length;
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      nums, n, i: -1, virtual: -1,
      explTitle: 'Initialization',
      explText: `We have array of size ${n}. Virtual indexing maps i to (1 + 2*i) % (n|1).`,
      pause: true
    });
    
    for (let i = 0; i < n; i++) {
        const virtual = (1 + 2 * i) % (n | 1);
        pushState({
          kind: 'map', line: 3, color: 'emerald',
          nums, n, i, virtual,
          explTitle: `Index ${i}`,
          explText: `i = ${i} maps to virtual index ${virtual}.`
        });
    }
    
    pushState({
      kind: 'done', line: -1, color: 'default',
      nums, n, i: -1, virtual: -1,
      explTitle: 'Done',
      explText: `All indices mapped. Odd slots get filled first, then even slots.`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = () => {
        let html = '';
        for (let idx = 0; idx < s.n; idx++) {
            const isI = idx === s.i;
            let cls = isI ? 'active-1' : 'merged';
            
            html += `<div class="array-node ${cls}">
              ${isI ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
              ${idx}</div>`;
        }
        return html;
    };
    
    const getVirtualHTML = () => {
        let html = '';
        for (let idx = 0; idx < s.n; idx++) {
            const isV = idx === s.virtual;
            let cls = isV ? 'active-k' : 'merged';
            let boxStyle = isV ? 'border: 2px solid #10b981;' : '';
            
            html += `<div class="array-node ${cls}" style="${boxStyle}">
              ${isV ? '<div class="pointer" style="color:#10b981; bottom:-20px; top:auto;">↑ virtual</div>' : ''}
              ${idx}</div>`;
        }
        return html;
    };
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Real Indices i</div>
          <div class="array-track" style="padding-bottom:24px; padding-top:24px;">${getArrayHTML()}</div>
        </div>
      </div>
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Virtual Indices A(i)</div>
          <div class="array-track" style="padding-bottom:24px; padding-top:24px;">${getVirtualHTML()}</div>
        </div>
      </div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Different Ways to Add Parentheses', short: 'Add Parentheses',
  idea: 'Divide and conquer with memoization. Split at every operator, solve recursively, and combine. Memoize by substring to avoid recomputing overlapping subproblems.',
  complexity: 'Time O(C_n) · Space O(C_n) where C_n is Catalan number',
  input: '2-1-1', hint: 'expression',
  code: [
    'def diffWaysToCompute(expr):',
    '    if expr in memo:',
    '        return memo[expr]',
    '    if expr.isdigit():',
    '        return [int(expr)]',
    '    res = []',
    '    for i, c in enumerate(expr):',
    '        if c in "+-*":',
    '            # split and recurse',
    '    memo[expr] = res',
    '    return res'
  ],
  parse(s) { return { expr: s.trim() }; },
  buildStates({ expr }) {
    const seq = [];
    function pushState(s) { seq.push(s); }
    
    const memo = {};
    function solve(e) {
        if (memo[e]) {
            pushState({
              kind: 'memo', line: 3, color: 'blue',
              expr: e, memo: {...memo},
              explTitle: 'Memo Hit',
              explText: `Expression "${e}" is already in memo.`
            });
            return memo[e];
        }
        
        if (!isNaN(e)) {
            pushState({
              kind: 'base', line: 5, color: 'emerald',
              expr: e, memo: {...memo},
              explTitle: 'Base Case',
              explText: `Expression "${e}" is a number. Return [${e}].`
            });
            return [parseInt(e)];
        }
        
        let res = [];
        for (let i = 0; i < e.length; i++) {
            const c = e[i];
            if (c === '+' || c === '-' || c === '*') {
                pushState({
                  kind: 'split', line: 8, color: 'amber',
                  expr: e, memo: {...memo},
                  explTitle: 'Split',
                  explText: `Splitting "${e}" at '${c}'. Left: "${e.substring(0, i)}", Right: "${e.substring(i+1)}".`
                });
                
                const left = solve(e.substring(0, i));
                const right = solve(e.substring(i+1));
                
                for (let l of left) {
                    for (let r of right) {
                        if (c === '+') res.push(l + r);
                        else if (c === '-') res.push(l - r);
                        else if (c === '*') res.push(l * r);
                    }
                }
            }
        }
        memo[e] = res;
        pushState({
          kind: 'memo-save', line: 10, color: 'emerald',
          expr: e, memo: {...memo},
          explTitle: 'Memoize',
          explText: `Saved results for "${e}" -> [${res.join(', ')}].`
        });
        return res;
    }
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      expr, memo: {},
      explTitle: 'Initialization',
      explText: `Start solving expression "${expr}".`,
      pause: true
    });
    
    solve(expr);
    
    pushState({
      kind: 'done', line: 11, color: 'default',
      expr, memo,
      explTitle: 'Done',
      explText: `Final answer for "${expr}" is [${memo[expr].join(', ')}].`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getMemoHTML = () => {
        let html = '';
        for (let key in s.memo) {
            html += `<div style="display:inline-block; padding:8px 12px; margin:4px; border-radius:6px; background:var(--surface); border:1px solid var(--border);">
              <span style="color:var(--accent); font-family:var(--mono);">"${key}"</span> → [${s.memo[key].join(', ')}]
            </div>`;
        }
        if (!html) html = '<div style="color:var(--text-dim); font-size:0.9rem;">(Empty)</div>';
        return html;
    };
    
    container.innerHTML = `
      <div class="glass-panel" style="text-align:center; padding:10px;">
        <span style="color:var(--text-dim); margin-right:10px;">Current Expression:</span>
        <span style="font-size:1.5rem; font-family:var(--mono); color:var(--text);">${s.expr}</span>
      </div>
      <div class="glass-panel" style="margin-top:10px;">
        <div class="panel-heading" style="color:var(--accent); margin-bottom:10px;">Memoization Table</div>
        <div>${getMemoHTML()}</div>
      </div>
    `;
  }
});

defineAlgoDom(ALGOS_ALGORITHMS, {
  type: 'dom',
  title: 'Implement Rand10() Using Rand7()', short: 'Rand10()',
  idea: 'Rejection Sampling: generate a number uniformly between 1 and 49 using two rand7() calls. If the number is <= 40, map it to 1..10. If it\'s > 40, reject and roll again.',
  complexity: 'Time O(1) expected · Space O(1)',
  input: 'Run', hint: 'Just run to generate a single Rand10()',
  code: [
    'def rand10():',
    '    while True:',
    '        row = rand7()',
    '        col = rand7()',
    '        idx = (row - 1) * 7 + col',
    '        ',
    '        if idx <= 40:',
    '            return (idx - 1) % 10 + 1'
  ],
  parse() { return { dummy: 1 }; },
  buildStates() {
    const seq = [];
    function pushState(s) { seq.push(s); }
    
    pushState({
      kind: 'init', line: 1, color: 'default',
      row: null, col: null, idx: null, result: null,
      explTitle: 'Initialization',
      explText: 'Begin infinite loop for rejection sampling.',
      pause: true
    });
    
    let result = null;
    let attempts = 0;
    while (true) {
        attempts++;
        const row = Math.floor(Math.random() * 7) + 1;
        const col = Math.floor(Math.random() * 7) + 1;
        
        pushState({
          kind: 'roll', line: 4, color: 'amber',
          row, col, idx: null, result: null, attempts,
          explTitle: `Attempt ${attempts}`,
          explText: `Rolled row = ${row}, col = ${col} using rand7().`
        });
        
        const idx = (row - 1) * 7 + col;
        
        pushState({
          kind: 'idx', line: 5, color: 'blue',
          row, col, idx, result: null, attempts,
          explTitle: 'Calculate Index',
          explText: `Mapped to a 1-49 range: (row - 1) * 7 + col = ${idx}`
        });
        
        if (idx <= 40) {
            result = ((idx - 1) % 10) + 1;
            pushState({
              kind: 'accept', line: 8, color: 'emerald',
              row, col, idx, result, attempts,
              explTitle: 'Accept and Map',
              explText: `${idx} <= 40! We map it to 1..10: (${idx} - 1) % 10 + 1 = ${result}.`
            });
            break;
        } else {
            pushState({
              kind: 'reject', line: 6, color: 'rose',
              row, col, idx, result: null, attempts,
              explTitle: 'Reject',
              explText: `${idx} > 40! We reject this number and roll again.`,
              pause: true
            });
        }
    }
    
    pushState({
      kind: 'done', line: -1, color: 'emerald',
      row: null, col: null, idx: null, result, attempts,
      explTitle: 'Done',
      explText: `Successfully generated Rand10() = ${result} in ${attempts} attempt(s).`,
      pause: true
    });
    
    return seq;
  },
  renderDOM(container, s) {
    const getGrid = () => {
        let html = '';
        for (let r = 1; r <= 7; r++) {
            html += `<div style="display:flex; justify-content:center;">`;
            for (let c = 1; c <= 7; c++) {
                const i = (r - 1) * 7 + c;
                const isSelected = s.row === r && s.col === c;
                const isReject = i > 40;
                
                let bg = isReject ? 'rgba(251,113,133,0.1)' : 'rgba(16,185,129,0.1)';
                let border = isReject ? '#fb7185' : '#10b981';
                if (isSelected) {
                    bg = isReject ? '#fb7185' : '#10b981';
                    border = 'var(--text)';
                }
                
                html += `<div style="width:36px; height:36px; margin:2px; display:flex; align-items:center; justify-content:center; border-radius:4px; font-size:12px; border:1px solid ${border}; background:${bg}; color:${isSelected ? '#fff' : 'var(--text)'}; transition:all 0.2s;">
                    ${i}
                </div>`;
            }
            html += `</div>`;
        }
        return html;
    };
    
    container.innerHTML = `
      <div class="glass-panel">
        <div class="panel-heading" style="color:var(--accent);">7x7 Grid (1 to 49)</div>
        <div style="padding:10px;">${getGrid()}</div>
      </div>
      <div class="glass-panel" style="margin-top:10px;">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Row (rand7)</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:var(--text);">${s.row || '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Col (rand7)</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:var(--text);">${s.col || '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Mapped idx</div>
                <div style="font-size:1.5rem; font-family:var(--mono); color:${s.idx > 40 ? '#fb7185' : (s.idx ? '#10b981' : 'var(--text)')};">${s.idx || '-'}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:var(--text-dim);">Result</div>
                <div style="font-size:1.8rem; font-family:var(--mono); color:#10b981;">${s.result || '-'}</div>
            </div>
        </div>
      </div>
    `;
  }
});
