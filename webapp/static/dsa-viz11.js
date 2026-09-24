/* ============================================================================
   Visualizations for 09_recursion_backtracking (Part 1 - Basics & Subsets)
   ========================================================================= */
"use strict";

/* ================================ 09 · Fibonacci Number ==================== */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Fibonacci Number', short: 'Fibonacci Number',
  idea: 'Use top-down recursion with a memoization dictionary to cache results, avoiding exponential redundant work.',
  complexity: 'Time O(n) · Space O(n)',
  input: '4', hint: 'n (e.g. 4, max 10)',
  code: [
    'def fib(n, memo=None):',
    '    if memo is None:',
    '        memo = {}',
    '    if n < 2:',
    '        return n',
    '    if n in memo:',
    '        return memo[n]',
    '    memo[n] = fib(n - 1, memo) + fib(n - 2, memo)',
    '    return memo[n]'
  ],
  parse(s) {
    const n = avNum(s, 'n');
    if (n < 0 || n > 10) throw new Error('Keep n between 0 and 10');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let memo = {};
    let callStack = []; // will store { n, state: 'start' | 'waiting_left' | 'waiting_right' | 'done', returnVal: null }
    let callIdCounter = 0;
    
    function snapshot(kind, line, color, title, text, highlightNodeId = null) {
        domPushState(seq, {
            kind, line, color,
            memo: { ...memo },
            callStack: JSON.parse(JSON.stringify(callStack)),
            highlightNodeId,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 3, 'default', 'Initialization', `Calling fib(${n}) with an empty memo.`);
    
    function fib_memo(curr_n) {
        let callId = callIdCounter++;
        let frame = { id: callId, n: curr_n, state: 'start', returnVal: null, leftId: null, rightId: null };
        callStack.push(frame);
        
        snapshot('call', 4, 'blue', `Call fib(${curr_n})`, `Entering recursive call for n = ${curr_n}.`, callId);
        
        if (curr_n < 2) {
            frame.returnVal = curr_n;
            frame.state = 'done';
            snapshot('base', 5, 'emerald', `Base Case (n = ${curr_n})`, `n < 2. Returning ${curr_n}.`, callId);
            let ret = curr_n;
            callStack.pop();
            return ret;
        }
        
        snapshot('check-memo', 6, 'amber', `Check Memo for n = ${curr_n}`, `Is ${curr_n} in memo? ${curr_n in memo ? 'Yes!' : 'No.'}`, callId);
        
        if (curr_n in memo) {
            frame.returnVal = memo[curr_n];
            frame.state = 'done';
            snapshot('memo-hit', 7, 'emerald', `Memo Hit!`, `Found ${curr_n} in memo. Returning ${memo[curr_n]} without further recursion!`, callId);
            let ret = memo[curr_n];
            callStack.pop();
            return ret;
        }
        
        frame.state = 'waiting_left';
        snapshot('recurse-left', 8, 'default', `Recurse n-1`, `We need fib(${curr_n-1}) and fib(${curr_n-2}). First calling fib(${curr_n-1}).`, callId);
        
        let leftVal = fib_memo(curr_n - 1);
        frame.leftVal = leftVal;
        
        frame.state = 'waiting_right';
        snapshot('recurse-right', 8, 'default', `Recurse n-2`, `fib(${curr_n-1}) returned ${leftVal}. Now calling fib(${curr_n-2}).`, callId);
        
        let rightVal = fib_memo(curr_n - 2);
        frame.rightVal = rightVal;
        
        let sum = leftVal + rightVal;
        memo[curr_n] = sum;
        frame.returnVal = sum;
        frame.state = 'done';
        
        snapshot('cache-and-return', 9, 'emerald', `Store & Return`, `fib(${curr_n}) = ${leftVal} + ${rightVal} = ${sum}. Stored in memo and returning.`, callId);
        
        callStack.pop();
        return sum;
    }
    
    fib_memo(n);
    
    snapshot('done', 9, 'emerald', 'Complete', `Final answer for fib(${n}) is ${memo[n] || n}!`, null);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getCallStackHTML = (stack, highlightId) => {
        if (stack.length === 0) return `<div style="text-align:center; padding:20px; color:var(--text-dim);">Empty Call Stack</div>`;
        return stack.map((frame, idx) => {
            let isTop = idx === stack.length - 1;
            let cls = isTop ? 'active-1' : (frame.id === highlightId ? 'active-k' : '');
            
            let status = '';
            if (frame.state === 'start') status = 'Running';
            else if (frame.state === 'waiting_left') status = `Wait fib(${frame.n-1})`;
            else if (frame.state === 'waiting_right') status = `Wait fib(${frame.n-2})`;
            else if (frame.state === 'done') status = `Returning ${frame.returnVal}`;
            
            return `
            <div class="array-node ${cls}" style="margin-bottom:8px; min-width:140px; justify-content:space-between; padding:5px 15px; border-radius:6px;">
                <div style="font-weight:bold;">fib(${frame.n})</div>
                <div style="font-size:12px; color:var(--text-dim); margin-left:15px;">${status}</div>
                ${isTop ? '<div class="pointer" style="position:absolute; right:-35px; color:#3b82f6;">← top</div>' : ''}
            </div>`;
        }).reverse().join('');
    };
    
    const getMemoHTML = (memo) => {
        let keys = Object.keys(memo).sort((a,b) => parseInt(a) - parseInt(b));
        if (keys.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">{ }</div>`;
        
        return `<div style="display:flex; flex-wrap:wrap; gap:10px;">` + keys.map(k => {
            return `
            <div class="array-node merged" style="border-radius:6px; padding:5px 15px; border-color:var(--emerald); background:var(--bg-card);">
                <span style="color:var(--text-dim); margin-right:8px;">n=${k} :</span>
                <b style="color:var(--emerald);">${memo[k]}</b>
            </div>`;
        }).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div style="display:flex; gap:15px;">
                  <div class="glass-panel stack-container" style="flex:1; display:flex; flex-direction:column; align-items:center;">
                      <div class="panel-heading" style="align-self:flex-start;">Call Stack</div>
                      <div style="display:flex; flex-direction:column; justify-content:flex-end; min-height:200px; padding:20px 10px;">
                          ${getCallStackHTML(s.callStack, s.highlightNodeId)}
                      </div>
                  </div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald);">
                  <div class="panel-heading">Memoization Cache</div>
                  <div class="array-track" style="padding:10px; justify-content:flex-start;">${getMemoHTML(s.memo)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 09 · Subsets ============================ */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Subsets', short: 'Subsets',
  idea: 'At each node in the decision tree, the current path is a valid subset. To explore further, try appending each remaining element.',
  complexity: 'Time O(n * 2^n) · Space O(n)',
  input: '1, 2, 3', hint: 'list of unique numbers',
  code: [
    'def subsets(nums):',
    '    results, path = [], []',
    '    def backtrack(start):',
    '        results.append(path[:])',
    '        for i in range(start, len(nums)):',
    '            path.append(nums[i])',
    '            backtrack(i + 1)',
    '            path.pop()',
    '    backtrack(0)',
    '    return results'
  ],
  parse(s) {
    const nums = avNums(s, 6, 'nums');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let results = [];
    let path = [];
    let n = nums.length;
    
    function snapshot(kind, line, color, title, text, start = -1, i = -1) {
        domPushState(seq, {
            kind, line, color,
            nums, results: JSON.parse(JSON.stringify(results)), path: [...path],
            start, i,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 2, 'default', 'Initialization', 'Empty results and path.');
    
    function backtrack(start) {
        results.push([...path]);
        snapshot('record', 4, 'emerald', 'Record Subset', `Every node is a valid subset! Appended [${path.join(', ')}] to results.`, start, -1);
        
        for (let i = start; i < n; i++) {
            snapshot('loop', 5, 'default', `Loop: i = ${i}`, `Considering nums[${i}] = ${nums[i]}.`, start, i);
            
            path.push(nums[i]);
            snapshot('choose', 6, 'blue', `Choose ${nums[i]}`, `Appended ${nums[i]} to path. Calling backtrack(${i + 1}).`, start, i);
            
            backtrack(i + 1);
            
            let popped = path.pop();
            snapshot('unchoose', 8, 'amber', `Unchoose ${popped}`, `Popped ${popped} to backtrack and try other siblings.`, start, i);
        }
    }
    
    backtrack(0);
    snapshot('done', 10, 'emerald', 'Complete', `Generated all ${results.length} subsets.`, -1, -1);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getNumsHTML = (nums, start, currI) => {
        return nums.map((val, idx) => {
            let cls = '';
            let ptrs = [];
            
            if (idx === currI) {
                cls = 'active-k';
                ptrs.push(`<div class="pointer" style="color:var(--amber); top:-25px;">↓ i</div>`);
            }
            if (idx === start) {
                cls = 'active-1';
                ptrs.push(`<div class="pointer" style="color:var(--blue); bottom:-25px;">↑ start</div>`);
            }
            if (idx < start) cls = 'merged';
            
            return `
            <div class="array-node ${cls}" style="position:relative;">
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
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(subset => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${subset.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums</div>
                  <div class="array-track" style="margin-bottom:10px; margin-top:15px;">${getNumsHTML(s.nums, s.start, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (path)</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto;">
                  <div class="panel-heading">Results (${s.results.length} subsets)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 09 · Subsets II ========================= */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Subsets II', short: 'Subsets II',
  idea: 'To prevent duplicate subsets when the input has duplicates, sort first. At any given depth (start), skip any element that is the same as the PREVIOUS sibling.',
  complexity: 'Time O(n * 2^n) · Space O(n)',
  input: '1, 2, 2', hint: 'list of numbers (can have duplicates)',
  code: [
    'def subsetsWithDup(nums):',
    '    nums.sort()',
    '    results, path = [], []',
    '    def backtrack(start):',
    '        results.append(path[:])',
    '        for i in range(start, len(nums)):',
    '            if i > start and nums[i] == nums[i-1]:',
    '                continue # Skip duplicate sibling',
    '            path.append(nums[i])',
    '            backtrack(i + 1)',
    '            path.pop()',
    '    backtrack(0)',
    '    return results'
  ],
  parse(s) {
    const origNums = avNums(s, 6, 'nums');
    return { origNums };
  },
  buildStates({ origNums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let nums = [...origNums];
    let results = [];
    let path = [];
    let n = nums.length;
    
    function snapshot(kind, line, color, title, text, start = -1, i = -1) {
        domPushState(seq, {
            kind, line, color,
            nums: [...nums], results: JSON.parse(JSON.stringify(results)), path: [...path],
            start, i,
            explTitle: title,
            explText: text
        }, ctx);
    }
    
    snapshot('init', 1, 'default', 'Initialization', `Original array: [${origNums.join(', ')}]. We must sort it first.`);
    
    nums.sort((a, b) => a - b);
    
    snapshot('sort', 2, 'amber', 'Sorted Array', `Sorted array: [${nums.join(', ')}]. Now identical elements are adjacent.`);
    snapshot('vars', 3, 'default', 'Variables', 'Empty results and path.');
    
    function backtrack(start) {
        results.push([...path]);
        snapshot('record', 5, 'emerald', 'Record Subset', `Appended [${path.join(', ')}] to results.`, start, -1);
        
        for (let i = start; i < n; i++) {
            snapshot('loop', 6, 'default', `Loop: i = ${i}`, `Considering nums[${i}] = ${nums[i]}.`, start, i);
            
            if (i > start && nums[i] === nums[i-1]) {
                snapshot('skip', 8, 'red', `Skip Duplicate`, `i (${i}) > start (${start}) AND nums[${i}] == nums[${i-1}]. This is a duplicate sibling branch. Skipping!`, start, i);
                continue;
            }
            
            path.push(nums[i]);
            snapshot('choose', 9, 'blue', `Choose ${nums[i]}`, `Appended ${nums[i]} to path. Calling backtrack(${i + 1}).`, start, i);
            
            backtrack(i + 1);
            
            let popped = path.pop();
            snapshot('unchoose', 11, 'amber', `Unchoose ${popped}`, `Popped ${popped} to backtrack.`, start, i);
        }
    }
    
    backtrack(0);
    snapshot('done', 13, 'emerald', 'Complete', `Generated all ${results.length} distinct subsets.`, -1, -1);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getNumsHTML = (nums, start, currI) => {
        return nums.map((val, idx) => {
            let cls = '';
            let ptrs = [];
            let isSkipped = s.kind === 'skip' && idx === currI;
            
            if (idx === currI) {
                cls = isSkipped ? 'active-red' : 'active-k';
                ptrs.push(`<div class="pointer" style="color:${isSkipped ? 'var(--red)' : 'var(--amber)'}; top:-25px;">↓ i</div>`);
            }
            if (idx === start) {
                cls = cls || 'active-1';
                ptrs.push(`<div class="pointer" style="color:var(--blue); bottom:-25px;">↑ start</div>`);
            }
            if (idx < start) cls = cls || 'merged';
            
            return `
            <div class="array-node ${cls}" style="position:relative;">
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
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(subset => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${subset.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums</div>
                  <div class="array-track" style="margin-bottom:10px; margin-top:15px;">${getNumsHTML(s.nums, s.start, s.i)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (path)</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto;">
                  <div class="panel-heading">Results (${s.results.length} subsets)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});
