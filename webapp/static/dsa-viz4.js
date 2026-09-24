/* ============================================================================
   Visualizations for 04_prefix_sum and 05_binary_search
   ========================================================================= */
'use strict';

/* ================================ 04 · Prefix Sum (Running Sum) ========== */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Running Sum of 1D Array', short: 'Running Sum',
  idea: 'Keep a running total of elements seen so far by mutating the input array or creating a new one.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 4', hint: 'comma-separated numbers',
  code: [
    'def runningSum(nums):',
    '    for i in range(1, len(nums)):',
    '        nums[i] += nums[i - 1]',
    '    return nums'
  ],
  parse(s) { return { nums: avNums(s, 12) }; },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = nums.length;
    const ans = [...nums];
    
    domPushState(seq, {
      kind: 'init', line: 1, color: 'default',
      nums: [...nums], ans: [...ans], i: -1,
      explTitle: 'Initialization',
      explText: `We start with the original array. We will iterate from index 1 to the end, adding the previous element's value to the current element.`,
      pause: true
    }, ctx);

    for (let i = 1; i < n; i++) {
      domPushState(seq, {
        kind: 'loop', line: 2, color: 'blue',
        nums: [...nums], ans: [...ans], i,
        explTitle: `Index ${i}`,
        explText: `Looking at nums[${i}] = ${ans[i]} and nums[${i-1}] = ${ans[i-1]}.`
      }, ctx);

      ans[i] += ans[i - 1];

      domPushState(seq, {
        kind: 'add', line: 3, color: 'emerald',
        nums: [...nums], ans: [...ans], i,
        explTitle: `Update Running Sum`,
        explText: `Update nums[${i}] to ${ans[i-1]} + ${nums[i]} = ${ans[i]}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 4, color: 'default',
      nums: [...nums], ans: [...ans], i: -1,
      explTitle: 'Complete',
      explText: `Finished computing the running sum. We return the modified array.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getArrayHTML = (arr, activeI) => {
        return arr.map((v, idx) => {
            const isActive = idx === activeI;
            const isPrev = idx === activeI - 1;
            let cls = '';
            if (isActive) cls = 'active-k'; // green highlight
            else if (isPrev) cls = 'active-1'; // blue highlight
            else if (idx < activeI) cls = 'merged'; // dimmed/completed
            
            return `
            <div class="array-node ${cls}">
                ${isActive ? '<div class="pointer" style="color:#34d399">↓ i</div>' : ''}
                ${isPrev ? '<div class="pointer" style="color:var(--accent)">↓ i-1</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">nums</div>
                  <div class="array-track">${getArrayHTML(s.ans, s.i)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 05 · Binary Search (DOM) ========== */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Binary Search', short: 'Binary Search',
  idea: 'Search a sorted array by repeatedly dividing the search interval in half.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '-1, 0, 3, 5, 9, 12 ; 9', hint: 'sorted numbers ; target',
  code: [
    'def search(nums, target):',
    '    l, r = 0, len(nums) - 1',
    '    while l <= r:',
    '        mid = (l + r) // 2',
    '        if nums[mid] == target:',
    '            return mid',
    '        elif nums[mid] < target:',
    '            l = mid + 1',
    '        else:',
    '            r = mid - 1',
    '    return -1'
  ],
  parse(s) { 
    const [a, t] = avParts(s);
    const nums = avNums(a, 12, 'sorted numbers');
    if (nums.some((x, i) => i > 0 && x < nums[i-1])) throw new Error('Array must be sorted');
    return { nums, target: avNum(t, 'target') };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let l = 0, r = nums.length - 1;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, l, r, mid: -1, found: false,
      explTitle: 'Initialization',
      explText: `We want to find ${target}. We set pointers l = 0 and r = ${r}.`,
      pause: true
    }, ctx);

    while (l <= r) {
      domPushState(seq, {
        kind: 'loop-cond', line: 3, color: 'default',
        nums, target, l, r, mid: -1, found: false,
        explTitle: 'Check condition',
        explText: `l (${l}) <= r (${r}) is true. We continue searching.`
      }, ctx);

      let mid = Math.floor((l + r) / 2);
      domPushState(seq, {
        kind: 'mid', line: 4, color: 'blue',
        nums, target, l, r, mid, found: false,
        explTitle: 'Calculate mid',
        explText: `mid = (l + r) // 2 = (${l} + ${r}) // 2 = ${mid}. The value here is ${nums[mid]}.`
      }, ctx);

      if (nums[mid] === target) {
        domPushState(seq, {
          kind: 'found', line: 6, color: 'emerald',
          nums, target, l, r, mid, found: true,
          explTitle: 'Target found!',
          explText: `nums[${mid}] == ${target}. We return the index ${mid}.`,
          pause: true
        }, ctx);
        return seq;
      } else if (nums[mid] < target) {
        domPushState(seq, {
          kind: 'move-left', line: 8, color: 'amber',
          nums, target, l, r, mid, found: false,
          explTitle: 'Target is larger',
          explText: `${nums[mid]} < ${target}. The target must be in the right half. We move l to mid + 1.`
        }, ctx);
        l = mid + 1;
      } else {
        domPushState(seq, {
          kind: 'move-right', line: 10, color: 'amber',
          nums, target, l, r, mid, found: false,
          explTitle: 'Target is smaller',
          explText: `${nums[mid]} > ${target}. The target must be in the left half. We move r to mid - 1.`
        }, ctx);
        r = mid - 1;
      }
    }

    domPushState(seq, {
      kind: 'not-found', line: 11, color: 'default',
      nums, target, l, r, mid: -1, found: false,
      explTitle: 'Loop ends',
      explText: `l (${l}) is now > r (${r}). The loop terminates and we return -1.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getArrayHTML = (arr, l, r, mid, found) => {
        return arr.map((v, idx) => {
            const isMid = idx === mid;
            const inRange = idx >= Math.min(l, r+1) && idx <= Math.max(r, l-1);
            let cls = '';
            
            if (isMid && found) cls = 'active-k'; // emerald
            else if (isMid) cls = 'active-1'; // blue
            else if (!inRange) cls = 'merged'; // dimmed out
            
            let pointers = '';
            if (idx === l) pointers += `<div class="pointer" style="color:var(--accent)">↓ l</div>`;
            if (idx === r) pointers += `<div class="pointer" style="color:#f59e0b">↓ r</div>`;
            if (idx === mid) pointers += `<div class="pointer" style="color:#3b82f6">↓ m</div>`;
            
            return `
            <div class="array-node ${cls}" style="${!inRange ? 'opacity:0.3' : ''}">
                ${pointers}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>nums</span>
                      <span style="color:var(--text-bright);">Target: ${s.target}</span>
                  </div>
                  <div class="array-track">${getArrayHTML(s.nums, s.l, s.r, s.mid, s.found)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 04 · Find Pivot Index (DOM) ========== */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Find Pivot Index', short: 'Pivot Index',
  idea: 'Keep track of the total sum and the left sum. The right sum is total - leftSum - nums[i].',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 7, 3, 6, 5, 6', hint: 'comma-separated numbers',
  code: [
    'def pivotIndex(nums):',
    '    total = sum(nums)',
    '    leftSum = 0',
    '    for i, x in enumerate(nums):',
    '        if leftSum == total - leftSum - x:',
    '            return i',
    '        leftSum += x',
    '    return -1'
  ],
  parse(s) { return { nums: avNums(s, 10) }; },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let total = nums.reduce((a, b) => a + b, 0);
    let leftSum = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, i: -1, leftSum, total, found: false,
      explTitle: 'Initialization',
      explText: `Total sum is ${total}. leftSum starts at 0.`,
      pause: true
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      let x = nums[i];
      let rightSum = total - leftSum - x;
      
      domPushState(seq, {
        kind: 'check', line: 5, color: 'blue',
        nums, i, leftSum, rightSum, total, found: false,
        explTitle: `Index ${i}`,
        explText: `Is leftSum (${leftSum}) == rightSum (${rightSum})?`
      }, ctx);
      
      if (leftSum === rightSum) {
        domPushState(seq, {
          kind: 'found', line: 6, color: 'emerald',
          nums, i, leftSum, rightSum, total, found: true,
          explTitle: 'Pivot Found',
          explText: `Yes! Index ${i} is the pivot.`,
          pause: true
        }, ctx);
        return seq;
      }
      
      leftSum += x;
      domPushState(seq, {
        kind: 'add', line: 7, color: 'amber',
        nums, i, leftSum, rightSum, total, found: false,
        explTitle: 'Update leftSum',
        explText: `leftSum is now ${leftSum}.`
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'not-found', line: 8, color: 'default',
      nums, i: -1, leftSum, total, found: false,
      explTitle: 'No Pivot',
      explText: 'No pivot index was found.',
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getArrayHTML = (arr, activeI) => {
        return arr.map((v, idx) => {
            const isLeft = idx < activeI && activeI !== -1;
            const isRight = idx > activeI && activeI !== -1;
            const isPivot = idx === activeI;
            let cls = '';
            
            if (isPivot && s.found) cls = 'active-k'; // emerald
            else if (isPivot) cls = 'active-1'; // blue
            else if (isLeft) cls = 'active-3'; // left part
            else if (isRight) cls = 'merged'; // right part
            
            return `
            <div class="array-node ${cls}">
                ${isPivot ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>nums</span>
                      <span style="color:var(--text-bright);">Total: ${s.total} | leftSum: ${s.leftSum} | rightSum: ${s.rightSum !== undefined ? s.rightSum : '?'}</span>
                  </div>
                  <div class="array-track">${getArrayHTML(s.nums, s.i)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 05 · Search Insert Position (DOM) ========== */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Search Insert Position', short: 'Search Insert',
  idea: 'Binary search for the target. If not found, the left pointer will be at the correct insertion index.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '1, 3, 5, 6 ; 2', hint: 'sorted numbers ; target',
  code: [
    'def searchInsert(nums, target):',
    '    l, r = 0, len(nums) - 1',
    '    while l <= r:',
    '        mid = (l + r) // 2',
    '        if nums[mid] == target:',
    '            return mid',
    '        elif nums[mid] < target:',
    '            l = mid + 1',
    '        else:',
    '            r = mid - 1',
    '    return l'
  ],
  parse(s) { 
    const [a, t] = avParts(s);
    const nums = avNums(a, 12, 'sorted numbers');
    if (nums.some((x, i) => i > 0 && x < nums[i-1])) throw new Error('Array must be sorted');
    return { nums, target: avNum(t, 'target') };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let l = 0, r = nums.length - 1;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, l, r, mid: -1, found: false, finished: false,
      explTitle: 'Initialization',
      explText: `We want to insert ${target}. We set l = 0 and r = ${r}.`,
      pause: true
    }, ctx);

    while (l <= r) {
      let mid = Math.floor((l + r) / 2);
      domPushState(seq, {
        kind: 'mid', line: 4, color: 'blue',
        nums, target, l, r, mid, found: false, finished: false,
        explTitle: 'Calculate mid',
        explText: `mid = ${mid}. nums[${mid}] is ${nums[mid]}.`
      }, ctx);

      if (nums[mid] === target) {
        domPushState(seq, {
          kind: 'found', line: 6, color: 'emerald',
          nums, target, l, r, mid, found: true, finished: true,
          explTitle: 'Target found!',
          explText: `Found ${target} at index ${mid}. We return ${mid}.`,
          pause: true
        }, ctx);
        return seq;
      } else if (nums[mid] < target) {
        l = mid + 1;
        domPushState(seq, {
          kind: 'move-left', line: 8, color: 'amber',
          nums, target, l, r, mid, found: false, finished: false,
          explTitle: 'Target is larger',
          explText: `${nums[mid]} < ${target}. We move l to mid + 1 = ${l}.`
        }, ctx);
      } else {
        r = mid - 1;
        domPushState(seq, {
          kind: 'move-right', line: 10, color: 'amber',
          nums, target, l, r, mid, found: false, finished: false,
          explTitle: 'Target is smaller',
          explText: `${nums[mid]} > ${target}. We move r to mid - 1 = ${r}.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'not-found', line: 11, color: 'emerald',
      nums, target, l, r, mid: -1, found: false, finished: true,
      explTitle: 'Loop ends',
      explText: `l (${l}) > r (${r}). We insert at l = ${l}.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getArrayHTML = (arr, l, r, mid, finished, found) => {
        // If finished, insert a placeholder for the inserted element if it wasn't found
        let html = '';
        let insertAt = (finished && !found) ? l : -1;
        
        for (let idx = 0; idx <= arr.length; idx++) {
            if (idx === insertAt) {
                html += `
                <div class="array-node active-k" style="border-style:dashed;">
                    <div class="pointer" style="color:#34d399">↓ insert ${s.target}</div>
                    ${s.target}
                    <div class="node-index">${idx}</div>
    </div>`;
            }
            if (idx < arr.length) {
                const v = arr[idx];
                const isMid = idx === mid;
                const inRange = idx >= Math.min(l, r+1) && idx <= Math.max(r, l-1);
                let cls = '';
                
                if (isMid && found) cls = 'active-k'; 
                else if (isMid) cls = 'active-1'; 
                else if (!inRange) cls = 'merged'; 
                
                let pointers = '';
                if (idx === l && !finished) pointers += `<div class="pointer" style="color:var(--accent)">↓ l</div>`;
                if (idx === r && !finished) pointers += `<div class="pointer" style="color:#f59e0b">↓ r</div>`;
                if (idx === mid && !finished) pointers += `<div class="pointer" style="color:#3b82f6">↓ m</div>`;
                
                html += `
                <div class="array-node ${cls}" style="${!inRange ? 'opacity:0.3' : ''}">
                    ${pointers}
                    ${v}
                    <div class="node-index">${idx >= insertAt && insertAt !== -1 ? idx + 1 : idx}</div>
    </div>`;
            }
        }
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>nums</span>
                      <span style="color:var(--text-bright);">Target: ${s.target}</span>
                  </div>
                  <div class="array-track">${getArrayHTML(s.nums, s.l, s.r, s.mid, s.finished, s.found)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 04 · Subarray Sum Equals K (DOM) ========== */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Subarray Sum Equals K', short: 'Subarray Sum',
  idea: 'Keep a running sum and a hash map of prefix sums we have seen so far.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 1, 1 ; 2', hint: 'comma-separated numbers ; k',
  code: [
    'def subarraySum(nums, k):',
    '    res = 0',
    '    curSum = 0',
    '    prefixSums = { 0: 1 }',
    '    for n in nums:',
    '        curSum += n',
    '        diff = curSum - k',
    '        res += prefixSums.get(diff, 0)',
    '        prefixSums[curSum] = 1 + prefixSums.get(curSum, 0)',
    '    return res'
  ],
  parse(s) { 
    const [a, kStr] = avParts(s);
    return { nums: avNums(a, 10), k: avNum(kStr, 'k') }; 
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let res = 0;
    let curSum = 0;
    let prefixSums = { 0: 1 };
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, i: -1, curSum, diff: null, res, prefixSums: {...prefixSums},
      explTitle: 'Initialization',
      explText: `Target sum k is ${k}. We initialize prefixSums map with {0: 1} to handle subarrays starting from index 0.`,
      pause: true
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      let n = nums[i];
      domPushState(seq, {
        kind: 'loop', line: 5, color: 'default',
        nums, k, i, curSum, diff: null, res, prefixSums: {...prefixSums},
        explTitle: `Index ${i}`,
        explText: `Looking at nums[${i}] = ${n}.`
      }, ctx);

      curSum += n;
      domPushState(seq, {
        kind: 'add-sum', line: 6, color: 'blue',
        nums, k, i, curSum, diff: null, res, prefixSums: {...prefixSums},
        explTitle: 'Update curSum',
        explText: `curSum += ${n} = ${curSum}.`
      }, ctx);

      let diff = curSum - k;
      domPushState(seq, {
        kind: 'calc-diff', line: 7, color: 'amber',
        nums, k, i, curSum, diff, res, prefixSums: {...prefixSums},
        explTitle: 'Calculate diff',
        explText: `diff = curSum - k = ${curSum} - ${k} = ${diff}. We look for this diff in our prefixSums map.`
      }, ctx);

      let count = prefixSums[diff] || 0;
      if (count > 0) {
        res += count;
        domPushState(seq, {
          kind: 'found-diff', line: 8, color: 'emerald',
          nums, k, i, curSum, diff, res, prefixSums: {...prefixSums},
          explTitle: 'Subarray(s) Found!',
          explText: `We found ${count} previous prefix sum(s) equal to ${diff}. We add ${count} to res. res is now ${res}.`,
          pause: true
        }, ctx);
      } else {
        domPushState(seq, {
          kind: 'not-found-diff', line: 8, color: 'default',
          nums, k, i, curSum, diff, res, prefixSums: {...prefixSums},
          explTitle: 'Diff not in map',
          explText: `We haven't seen a prefix sum of ${diff} yet. res remains ${res}.`
        }, ctx);
      }

      prefixSums[curSum] = 1 + (prefixSums[curSum] || 0);
      domPushState(seq, {
        kind: 'update-map', line: 9, color: 'default',
        nums, k, i, curSum, diff, res, prefixSums: {...prefixSums},
        explTitle: 'Update prefixSums',
        explText: `Add curSum (${curSum}) to the prefixSums map. prefixSums[${curSum}] is now ${prefixSums[curSum]}.`
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'done', line: 10, color: 'default',
      nums, k, i: -1, curSum, diff: null, res, prefixSums: {...prefixSums},
      explTitle: 'Complete',
      explText: `Finished iterating. Total valid subarrays found: ${res}. We return res.`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getArrayHTML = (arr, activeI) => {
        return arr.map((v, idx) => {
            const isActive = idx === activeI;
            let cls = '';
            
            if (isActive) cls = 'active-k'; // emerald
            else if (idx < activeI) cls = 'active-1'; // blue part
            else cls = 'merged'; // dimmed out
            
            return `
            <div class="array-node ${cls}">
                ${isActive ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const formatMap = (map) => {
        return Object.entries(map).map(([k, v]) => {
            return `<div style="background:var(--bg-elevated); padding:4px 8px; border-radius:4px; font-family:var(--font-mono); font-size:13px;">${k}: ${v}</div>`;
        }).join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>nums (Target k: ${s.k})</span>
                      <span style="color:var(--text-bright);">Result: ${s.res}</span>
                  </div>
                  <div class="array-track">${getArrayHTML(s.nums, s.i)}</div>
              </div>
              <div style="display:flex; gap:15px;">
                  <div class="glass-panel" style="flex:1;">
                      <div class="panel-heading">Variables</div>
                      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:10px;">
                          <div>curSum: <b style="color:var(--accent)">${s.curSum}</b></div>
                          <div>diff: <b style="color:#f59e0b">${s.diff !== null ? s.diff : '-'}</b></div>
                      </div>
                  </div>
                  <div class="glass-panel" style="flex:1;">
                      <div class="panel-heading">PrefixSums Map</div>
                      <div style="display:flex; flex-wrap:wrap; gap:8px; padding:10px;">
                          ${formatMap(s.prefixSums)}
                      </div>
                  </div>
              </div>
    </div>`;
  }
});

/* ================================ 05 · First Bad Version (DOM) ========== */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'First Bad Version', short: 'First Bad Version',
  idea: 'Binary search for the first bad version. Since versions are [Good, Good, ..., Bad, Bad], we want to find the first transition to Bad.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '5 ; 4', hint: 'n ; bad',
  code: [
    'def firstBadVersion(n):',
    '    l, r = 1, n',
    '    while l < r:',
    '        mid = (l + r) // 2',
    '        if isBadVersion(mid):',
    '            r = mid',
    '        else:',
    '            l = mid + 1',
    '    return l'
  ],
  parse(s) { 
    const [nStr, badStr] = avParts(s);
    const n = avNum(nStr, 'n');
    const bad = avNum(badStr, 'bad');
    if (bad < 1 || bad > n) throw new Error('Bad version must be between 1 and n');
    if (n > 20) throw new Error('Keep n <= 20 for visualization purposes');
    return { n, bad };
  },
  buildStates({ n, bad }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let l = 1, r = n;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      n, bad, l, r, mid: -1, 
      explTitle: 'Initialization',
      explText: `We have ${n} versions. We know version ${bad} is the first bad one, but the algorithm doesn't. We set l = 1 and r = ${n}.`,
      pause: true
    }, ctx);

    while (l < r) {
      domPushState(seq, {
        kind: 'loop-cond', line: 3, color: 'default',
        n, bad, l, r, mid: -1,
        explTitle: 'Check condition',
        explText: `l (${l}) < r (${r}) is true. We continue searching.`
      }, ctx);

      let mid = Math.floor((l + r) / 2);
      let isBad = mid >= bad;
      
      domPushState(seq, {
        kind: 'mid', line: 4, color: 'blue',
        n, bad, l, r, mid, isBad,
        explTitle: 'Calculate mid',
        explText: `mid = (${l} + ${r}) // 2 = ${mid}. We call isBadVersion(${mid}).`
      }, ctx);

      if (isBad) {
        domPushState(seq, {
          kind: 'is-bad', line: 5, color: 'amber',
          n, bad, l, r, mid, isBad,
          explTitle: 'Version is Bad',
          explText: `isBadVersion(${mid}) is true. The first bad version must be at mid or before it. We move r to ${mid}.`
        }, ctx);
        r = mid;
      } else {
        domPushState(seq, {
          kind: 'is-good', line: 7, color: 'emerald',
          n, bad, l, r, mid, isBad,
          explTitle: 'Version is Good',
          explText: `isBadVersion(${mid}) is false. The first bad version must be after mid. We move l to ${mid + 1}.`
        }, ctx);
        l = mid + 1;
      }
    }

    domPushState(seq, {
      kind: 'done', line: 9, color: 'emerald',
      n, bad, l, r, mid: -1, 
      explTitle: 'Complete',
      explText: `l (${l}) == r (${r}). We found the first bad version. We return ${l}.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    // Generate array from 1 to n
    const arr = Array.from({length: s.n}, (_, i) => i + 1);
    
    const getArrayHTML = (arr, l, r, mid) => {
        return arr.map((v) => {
            const isMid = v === mid;
            const inRange = v >= Math.min(l, r) && v <= Math.max(r, l);
            const isBad = v >= s.bad;
            let cls = '';
            
            if (isMid) cls = 'active-k'; 
            else if (!inRange) cls = 'merged'; 
            else cls = 'active-1';
            
            let pointers = '';
            if (v === l) pointers += `<div class="pointer" style="color:var(--accent)">↓ l</div>`;
            if (v === r && v !== l) pointers += `<div class="pointer" style="color:#f59e0b">↓ r</div>`;
            if (v === r && v === l) pointers += `<div class="pointer" style="color:#f59e0b">↓ l,r</div>`;
            if (v === mid) pointers += `<div class="pointer" style="color:#3b82f6">↓ m</div>`;
            
            return `
            <div class="array-node ${cls}" style="${!inRange ? 'opacity:0.3' : ''}; position:relative; min-width:40px; text-align:center;">
                ${pointers}
                <div style="font-size:12px; font-weight:bold; color:${isBad ? '#ef4444' : '#10b981'}">${isBad ? 'B' : 'G'}</div>
                ${v}
            </div>`;
        }).join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Versions (1 to ${s.n})</span>
                      <span style="color:var(--text-bright);">Actual First Bad: ${s.bad}</span>
                  </div>
                  <div class="array-track">${getArrayHTML(arr, s.l, s.r, s.mid)}</div>
              </div>
    </div>`;
  }
});
