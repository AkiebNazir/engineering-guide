/* ============================================================================
   Visualizations for 09_recursion_backtracking (Part 2 - Permutations & Combinations)
   ========================================================================= */
"use strict";

/* ================================ 09 · Permutations ======================== */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Permutations', short: 'Permutations',
  idea: 'At each node, choose any UNUSED element. Use a boolean array `used` to track which elements are in the current path.',
  complexity: 'Time O(n * n!) · Space O(n)',
  input: '1, 2, 3', hint: 'list of unique numbers',
  code: [
    'def permute(nums):',
    '    results, path, used = [], [], [False]*len(nums)',
    '    def backtrack():',
    '        if len(path) == len(nums):',
    '            results.append(path[:])',
    '            return',
    '        for i in range(len(nums)):',
    '            if used[i]: continue',
    '            used[i] = True',
    '            path.append(nums[i])',
    '            backtrack()',
    '            path.pop()',
    '            used[i] = False',
    '    backtrack()',
    '    return results'
  ],
  parse(s) {
    const nums = avNums(s, 5, 'nums');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let results = [];
    let path = [];
    let n = nums.length;
    let used = new Array(n).fill(false);
    
    function snapshot(kind, line, color, title, text, i = -1) {
        domPushState(seq, {
            kind, line, color,
            nums, results: JSON.parse(JSON.stringify(results)), path: [...path], used: [...used],
            i,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 2, 'default', 'Initialization', 'Empty results, path, and used=[False, ...]');
    
    function backtrack() {
        if (path.length === n) {
            results.push([...path]);
            snapshot('record', 5, 'emerald', 'Record Permutation', `Path length is ${n}. Appended [${path.join(', ')}] to results.`, -1);
            return;
        }
        
        for (let i = 0; i < n; i++) {
            snapshot('loop', 7, 'default', `Loop: i = ${i}`, `Considering nums[${i}] = ${nums[i]}. Is it used?`, i);
            
            if (used[i]) {
                snapshot('skip', 8, 'amber', `Skip Used`, `nums[${i}] = ${nums[i]} is already in the path. Skipping.`, i);
                continue;
            }
            
            used[i] = true;
            path.push(nums[i]);
            snapshot('choose', 10, 'blue', `Choose ${nums[i]}`, `Marked used[${i}] = True. Appended ${nums[i]} to path. Calling backtrack().`, i);
            
            backtrack();
            
            let popped = path.pop();
            used[i] = false;
            snapshot('unchoose', 13, 'amber', `Unchoose ${popped}`, `Popped ${popped} from path. Marked used[${i}] = False.`, i);
        }
    }
    
    backtrack();
    snapshot('done', 15, 'emerald', 'Complete', `Generated all ${results.length} permutations.`, -1);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getNumsHTML = (nums, used, currI) => {
        return nums.map((val, idx) => {
            let cls = '';
            let ptrs = [];
            
            if (idx === currI) {
                cls = s.kind === 'skip' ? 'active-red' : 'active-k';
                ptrs.push(`<div class="pointer" style="color:var(--amber); top:-25px;">↓ i</div>`);
            }
            if (used[idx]) {
                cls = cls || 'merged';
                ptrs.push(`<div style="position:absolute; bottom:-20px; font-size:10px; color:var(--text-dim);">used</div>`);
            }
            
            return `
            <div class="array-node ${cls}" style="position:relative; opacity: ${used[idx] && idx !== currI ? 0.5 : 1};">
                ${ptrs.join('')}
                ${val}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getPathHTML = (path) => {
        if (path.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return path.map(val => `
            <div class="array-node active-1" style="background:var(--blue); color:white; border-color:white;">
                ${val}
            </div>
        `).join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${p.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums & used[]</div>
                  <div class="array-track" style="margin-bottom:15px; margin-top:15px;">${getNumsHTML(s.nums, s.used, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (path)</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:180px;">
                  <div class="panel-heading">Results (${s.results.length} permutations)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 09 · Permutations II ===================== */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Permutations II', short: 'Permutations II',
  idea: 'Sort first to group duplicates. Skip a candidate if it is identical to the previous sibling and the previous sibling was NOT used in the current ancestor path.',
  complexity: 'Time up to O(n * n!) · Space O(n)',
  input: '1, 1, 2', hint: 'list of numbers (can have duplicates)',
  code: [
    'def permuteUnique(nums):',
    '    nums.sort()',
    '    results, path, used = [], [], [False]*len(nums)',
    '    def backtrack():',
    '        if len(path) == len(nums):',
    '            results.append(path[:]); return',
    '        for i in range(len(nums)):',
    '            if used[i]: continue',
    '            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:',
    '                continue # Skip duplicate sibling',
    '            used[i] = True',
    '            path.append(nums[i])',
    '            backtrack()',
    '            path.pop()',
    '            used[i] = False',
    '    backtrack()',
    '    return results'
  ],
  parse(s) {
    const origNums = avNums(s, 5, 'nums');
    return { origNums };
  },
  buildStates({ origNums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let nums = [...origNums];
    let results = [];
    let path = [];
    let n = nums.length;
    let used = new Array(n).fill(false);
    
    function snapshot(kind, line, color, title, text, i = -1) {
        domPushState(seq, {
            kind, line, color,
            nums: [...nums], results: JSON.parse(JSON.stringify(results)), path: [...path], used: [...used],
            i,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 1, 'default', 'Initialization', `Original array: [${origNums.join(', ')}]. We must sort it first.`);
    
    nums.sort((a, b) => a - b);
    
    snapshot('sort', 2, 'amber', 'Sorted Array', `Sorted array: [${nums.join(', ')}]. Now identical elements are adjacent.`);
    
    function backtrack() {
        if (path.length === n) {
            results.push([...path]);
            snapshot('record', 6, 'emerald', 'Record Permutation', `Path length is ${n}. Appended [${path.join(', ')}] to results.`, -1);
            return;
        }
        
        for (let i = 0; i < n; i++) {
            snapshot('loop', 7, 'default', `Loop: i = ${i}`, `Considering nums[${i}] = ${nums[i]}. Is it used?`, i);
            
            if (used[i]) {
                snapshot('skip', 8, 'amber', `Skip Used`, `nums[${i}] = ${nums[i]} is already in the path. Skipping.`, i);
                continue;
            }
            
            if (i > 0 && nums[i] === nums[i-1] && !used[i-1]) {
                snapshot('skip-dup', 10, 'red', `Skip Duplicate Sibling`, `nums[${i}] == nums[${i-1}] AND used[${i-1}] is false. The previous identical sibling finished its subtree. Exploring again would duplicate permutations. Skipping!`, i);
                continue;
            }
            
            used[i] = true;
            path.push(nums[i]);
            snapshot('choose', 12, 'blue', `Choose ${nums[i]}`, `Marked used[${i}] = True. Appended ${nums[i]} to path. Calling backtrack().`, i);
            
            backtrack();
            
            let popped = path.pop();
            used[i] = false;
            snapshot('unchoose', 15, 'amber', `Unchoose ${popped}`, `Popped ${popped} from path. Marked used[${i}] = False.`, i);
        }
    }
    
    backtrack();
    snapshot('done', 17, 'emerald', 'Complete', `Generated all ${results.length} distinct permutations.`, -1);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getNumsHTML = (nums, used, currI) => {
        return nums.map((val, idx) => {
            let cls = '';
            let ptrs = [];
            let isSkipped = (s.kind === 'skip' || s.kind === 'skip-dup') && idx === currI;
            
            if (idx === currI) {
                cls = isSkipped ? 'active-red' : 'active-k';
                ptrs.push(`<div class="pointer" style="color:${isSkipped ? 'var(--red)' : 'var(--amber)'}; top:-25px;">↓ i</div>`);
            }
            if (used[idx]) {
                cls = cls || 'merged';
                ptrs.push(`<div style="position:absolute; bottom:-20px; font-size:10px; color:var(--text-dim);">used</div>`);
            }
            
            return `
            <div class="array-node ${cls}" style="position:relative; opacity: ${used[idx] && idx !== currI ? 0.5 : 1};">
                ${ptrs.join('')}
                ${val}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getPathHTML = (path) => {
        if (path.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return path.map(val => `
            <div class="array-node active-1" style="background:var(--blue); color:white; border-color:white;">
                ${val}
            </div>
        `).join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${p.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums & used[]</div>
                  <div class="array-track" style="margin-bottom:15px; margin-top:15px;">${getNumsHTML(s.nums, s.used, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (path)</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:180px;">
                  <div class="panel-heading">Results (${s.results.length} permutations)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 09 · Combinations ======================== */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Combinations', short: 'Combinations',
  idea: 'To pick k items out of n where order does not matter, enforce a STRICTLY INCREASING rule: only pick elements larger than the one just picked. This prevents duplicate sets like [1,2] and [2,1]. Pruning bound: `n - need + 1`.',
  complexity: 'Time O(k * C(n,k)) · Space O(k)',
  input: '4, 2', hint: 'n, k (e.g. 4, 2)',
  code: [
    'def combine(n, k):',
    '    results, path = [], []',
    '    def backtrack(start):',
    '        if len(path) == k:',
    '            results.append(path[:])',
    '            return',
    '        need = k - len(path)',
    '        bound = n - need + 1 # PRUNE dead ends',
    '        for i in range(start, bound + 1):',
    '            path.append(i)',
    '            backtrack(i + 1)',
    '            path.pop()',
    '    backtrack(1)',
    '    return results'
  ],
  parse(s) {
    const parsed = avNums(s, 2, 'n, k');
    if (parsed.length < 2) throw new Error('Provide n and k (e.g., 4, 2)');
    const n = parsed[0];
    const k = parsed[1];
    if (n < 1 || k < 0 || k > n) throw new Error('Invalid n or k');
    return { n, k };
  },
  buildStates({ n, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let results = [];
    let path = [];
    
    function snapshot(kind, line, color, title, text, start = -1, bound = -1, i = -1) {
        domPushState(seq, {
            kind, line, color,
            n, k, results: JSON.parse(JSON.stringify(results)), path: [...path],
            start, bound, i,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 2, 'default', 'Initialization', `n=${n}, k=${k}. Empty results and path.`);
    
    function backtrack(start) {
        if (path.length === k) {
            results.push([...path]);
            snapshot('record', 5, 'emerald', 'Record Combination', `Path length is ${k}. Appended [${path.join(', ')}] to results.`, start, -1, -1);
            return;
        }
        
        let need = k - path.length;
        let bound = n - need + 1;
        
        snapshot('vars', 8, 'default', 'Calculate Bound (Pruning)', `need = ${need}. bound = n - need + 1 = ${bound}. This prunes dead ends that can't reach size ${k}.`, start, bound, -1);
        
        for (let i = start; i <= bound; i++) {
            snapshot('loop', 9, 'default', `Loop: i = ${i}`, `Considering element ${i}. Loop range is ${start} to ${bound}.`, start, bound, i);
            
            path.push(i);
            snapshot('choose', 10, 'blue', `Choose ${i}`, `Appended ${i} to path. Calling backtrack(${i + 1}).`, start, bound, i);
            
            backtrack(i + 1);
            
            let popped = path.pop();
            snapshot('unchoose', 12, 'amber', `Unchoose ${popped}`, `Popped ${popped} from path. Backtracking.`, start, bound, i);
        }
    }
    
    backtrack(1);
    snapshot('done', 14, 'emerald', 'Complete', `Generated all ${results.length} combinations.`, -1, -1, -1);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getRangeHTML = (n, start, bound, currI) => {
        let els = [];
        for (let i = 1; i <= n; i++) {
            let cls = '';
            let ptrs = [];
            
            if (i === currI) {
                cls = 'active-k';
                ptrs.push(`<div class="pointer" style="color:var(--amber); top:-25px;">↓ i</div>`);
            }
            if (i === start) {
                cls = cls || 'active-1';
                ptrs.push(`<div class="pointer" style="color:var(--blue); bottom:-25px; left:5px;">↑ start</div>`);
            }
            if (i === bound) {
                cls = cls || 'active-red';
                ptrs.push(`<div class="pointer" style="color:var(--red); bottom:-40px; right:5px;">↑ bound</div>`);
            }
            
            if (i < start || i > bound) {
                cls = cls || 'merged';
            }
            
            els.push(`
            <div class="array-node ${cls}" style="position:relative; opacity: ${i < start || i > bound ? 0.4 : 1}; margin-bottom: 20px;">
                ${ptrs.join('')}
                ${i}
            </div>`);
        }
        return els.join('');
    };

    const getPathHTML = (path) => {
        if (path.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return path.map(val => `
            <div class="array-node active-1" style="background:var(--blue); color:white; border-color:white;">
                ${val}
            </div>
        `).join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${p.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Domain [1 .. ${s.n}]</div>
                  <div class="array-track" style="margin-bottom:25px; margin-top:15px;">${getRangeHTML(s.n, s.start, s.bound, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (len = ${s.path.length} / ${s.k})</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:160px;">
                  <div class="panel-heading">Results (${s.results.length} combinations)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});
