/* ============================================================================
   DOM-based glassmorphic visualizers — the rich "merge-two-sorted" style.
   Each uses  type: 'dom'  so renderAlgoTab() picks renderDomAlgo().
   Requires dsa-viz.js (defineAlgo, avNums, avParts, avNum, esc).
   ========================================================================= */
'use strict';

const defineAlgoDom = (topics, spec) => [].concat(topics).forEach(t => {
  ALGOS[t] = ALGOS[t] || [];
  ALGOS[t].unshift(spec);
});

/* ========================================================= helpers ======== */
const avArr = avNums;   // alias used throughout this file
function domPushState(seq, s, ctx) {
  if (s.explTitle) ctx.t = s.explTitle;
  if (s.explText) ctx.x = s.explText;
  s.explTitle = ctx.t;
  s.explText  = ctx.x;
  seq.push(s);
}

/* ================================ 08 · Reverse Linked List (DOM) ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Reverse a linked list', short: 'Reverse Linked List',
  idea: 'Use three pointers — <code>prev</code>, <code>curr</code>, <code>next</code> — to reverse each link in a single pass. At every step we save the next node, point the current node backwards, then advance all three pointers.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 4, 5', hint: 'comma-separated node values',
  code: [
    'def reverseList(head):',
    '    prev = None',
    '    curr = head',
    '    while curr:',
    '        next_node = curr.next',
    '        curr.next = prev',
    '        prev = curr',
    '        curr = next_node',
    '    return prev',
  ],
  parse(s) { return { vals: avNums(s, 12) }; },
  buildStates({ vals }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = vals.length;
    let prev = -1, curr = 0;
    // arrows[i] = index of node that node i points to, or -1 for null
    const arrows = vals.map((_, i) => i < n - 1 ? i + 1 : -1);

    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      vals, arrows: [...arrows], prev, curr, next: -1, done: false,
      explTitle: 'Initialization',
      explText: `We set prev = null and curr = head (node ${vals[0]}). We'll walk through the list, reversing each pointer as we go.`,
      pause: true
    }, ctx);

    while (curr >= 0 && curr < n) {
      const nextNode = arrows[curr];
      domPushState(seq, {
        kind: 'save-next', line: 5, color: 'blue',
        vals, arrows: [...arrows], prev, curr, next: nextNode, done: false,
        explTitle: 'Save Next',
        explText: `Save next_node = curr.next → ${nextNode >= 0 ? vals[nextNode] : 'None'}. We need this because we're about to break the forward link.`
      }, ctx);

      arrows[curr] = prev;
      domPushState(seq, {
        kind: 'reverse-link', line: 6, color: 'emerald',
        vals, arrows: [...arrows], prev, curr, next: nextNode, done: false,
        explTitle: 'Reverse Link',
        explText: `Point curr.next backwards to prev → ${prev >= 0 ? vals[prev] : 'None'}. The arrow from ${vals[curr]} now points left instead of right!`
      }, ctx);

      prev = curr;
      domPushState(seq, {
        kind: 'advance-prev', line: 7, color: 'amber',
        vals, arrows: [...arrows], prev, curr, next: nextNode, done: false,
        explTitle: 'Advance prev',
        explText: `Move prev forward to curr (node ${vals[prev]}).`
      }, ctx);

      curr = nextNode;
      domPushState(seq, {
        kind: 'advance-curr', line: 8, color: 'default',
        vals, arrows: [...arrows], prev, curr, next: -1, done: false,
        explTitle: 'Advance curr',
        explText: curr >= 0 ? `Move curr forward to next_node (node ${vals[curr]}). Loop continues.` : `curr is now None. The loop ends.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'complete', line: 9, color: 'emerald',
      vals, arrows: [...arrows], prev, curr: -1, next: -1, done: true,
      explTitle: 'Reversal Complete',
      explText: `Return prev (node ${vals[prev]}), which is the new head. The entire list has been reversed: ${[...vals].reverse().join(' → ')}.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const nodeHTML = s.vals.map((v, i) => {
      const isCurr = s.curr === i;
      const isPrev = s.prev === i;
      const isNext = s.next === i;
      let cls = '';
      if (isCurr) cls = 'active-1';
      else if (isPrev) cls = 'active-2';
      else if (isNext) cls = 'merged active-k';

      let pointerLabel = '';
      if (isCurr && isPrev) pointerLabel = '↓ prev,curr';
      else if (isCurr) pointerLabel = '↓ curr';
      else if (isPrev) pointerLabel = '↓ prev';
      if (isNext) pointerLabel = '↓ next';

      return `
        <div class="array-node ${cls}" style="min-width:48px;">
          ${pointerLabel ? `<div class="pointer" style="opacity:1;color:${isCurr ? 'var(--accent)' : isPrev ? '#fbbf24' : '#34d399'}">${pointerLabel}</div>` : ''}
          ${v}
          <div class="node-index">${i}</div>
        </div>`;
    }).join('');

    // Build arrow indicators between nodes
    const arrowsHTML = s.vals.map((_, i) => {
      const target = s.arrows[i];
      if (target === -1) return `<span style="color:var(--text-dim);font-size:11px;font-family:var(--mono);">→ ∅</span>`;
      const reversed = target < i;
      return `<span style="color:${reversed ? '#34d399' : 'var(--text-dim)'};font-size:14px;font-weight:bold;">${reversed ? '←' : '→'}</span>`;
    });

    // Interleave nodes and arrows
    let chainHTML = '';
    for (let i = 0; i < s.vals.length; i++) {
      const isCurr = s.curr === i;
      const isPrev = s.prev === i;
      const isNext = s.next === i;
      let cls = '';
      if (isCurr) cls = 'active-1';
      else if (isPrev) cls = 'active-2';
      else if (isNext) cls = 'merged active-k';

      let pointerLabel = '';
      if (isCurr && isPrev) pointerLabel = 'prev,curr';
      else if (isCurr) pointerLabel = 'curr';
      else if (isPrev) pointerLabel = 'prev';
      if (isNext) pointerLabel = 'next';

      chainHTML += `
        <div class="array-node ${cls}" style="min-width:48px;">
          ${pointerLabel ? `<div class="pointer" style="opacity:1;color:${isCurr ? 'var(--accent)' : isPrev ? '#fbbf24' : '#34d399'}">↓ ${pointerLabel}</div>` : ''}
          ${v = s.vals[i]}
          <div class="node-index">${i}</div>
        </div>`;
      if (i < s.vals.length - 1) {
        const target = s.arrows[i];
        const reversed = target >= 0 && target < i;
        chainHTML += `<div style="display:flex;align-items:center;padding:0 2px;font-size:16px;color:${reversed ? '#34d399' : 'var(--text-dim)'};font-weight:bold;">${reversed ? '←' : '→'}</div>`;
      }
    }

    const resultHTML = s.done
      ? `<div class="glass-panel" style="border-color:#34d399;background:color-mix(in srgb, #34d399 5%, transparent);">
           <div class="panel-heading" style="color:#34d399;">Reversed List</div>
           <div class="array-track">${[...s.vals].reverse().map(v => `<div class="array-node merged">${v}</div>`).join('<div style="display:flex;align-items:center;padding:0 2px;font-size:16px;color:#34d399;font-weight:bold;">→</div>')}</div>
         </div>`
      : '';

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Linked List Nodes</div>
        <div class="array-track" style="align-items:center;">${chainHTML}</div>
      </div>
      ${resultHTML}`;
  }
});

/* ================================ 08 · Linked List Cycle (DOM) ============ */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Floyd cycle detection (tortoise and hare)', short: 'Linked List Cycle',
  idea: 'Two pointers: <code>slow</code> moves 1 step, <code>fast</code> moves 2 steps. If there\'s a cycle, they <b>must</b> meet inside it — like two runners on a circular track. If fast reaches null, there is no cycle.',
  complexity: 'Time O(n) · Space O(1)',
  input: '3, 2, 0, -4 ; 1', hint: 'values ; cycle-start index (-1 for no cycle)',
  code: [
    'def hasCycle(head):',
    '    slow = fast = head',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '        if slow == fast:',
    '            return True   # cycle found',
    '    return False           # no cycle',
  ],
  parse(s) {
    const [a, c] = avParts(s);
    const vals = avNums(a, 12);
    const cyclePos = c !== undefined ? avNum(c, 'cycle position') : -1;
    if (cyclePos >= vals.length) throw new Error(`Cycle position ${cyclePos} is beyond the list length`);
    return { vals, cyclePos };
  },
  buildStates({ vals, cyclePos }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = vals.length;
    // Build adjacency: node i → i+1, last node → cyclePos (or -1)
    const next = vals.map((_, i) => i < n - 1 ? i + 1 : cyclePos);
    let slow = 0, fast = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      vals, next, slow, fast, met: false, done: false, cyclePos,
      explTitle: 'Initialization',
      explText: `Both slow and fast start at the head (node ${vals[0]}). Slow will move 1 step at a time, fast will move 2 steps.`,
      pause: true
    }, ctx);

    let steps = 0, maxSteps = n * 3;
    while (steps < maxSteps) {
      // Check fast and fast.next
      const fNext = next[fast];
      if (fNext < 0 || fNext >= n) {
        domPushState(seq, {
          kind: 'no-cycle', line: 8, color: 'emerald',
          vals, next, slow, fast, met: false, done: true, cyclePos,
          explTitle: 'No Cycle',
          explText: `fast reached null — the list has a definite end. Return False.`,
          pause: true
        }, ctx);
        return seq;
      }
      const fNextNext = next[fNext];
      if (fNextNext < 0 || fNextNext >= n) {
        domPushState(seq, {
          kind: 'no-cycle', line: 8, color: 'emerald',
          vals, next, slow, fast, met: false, done: true, cyclePos,
          explTitle: 'No Cycle',
          explText: `fast.next reached null — the list has a definite end. Return False.`,
          pause: true
        }, ctx);
        return seq;
      }

      slow = next[slow];
      fast = fNextNext;
      steps++;

      domPushState(seq, {
        kind: 'move', line: 4, color: 'blue',
        vals, next, slow, fast, met: false, done: false, cyclePos,
        explTitle: `Step ${steps}`,
        explText: `slow → node ${vals[slow]} (1 step). fast → node ${vals[fast]} (2 steps).`
      }, ctx);

      if (slow === fast) {
        domPushState(seq, {
          kind: 'cycle-found', line: 7, color: 'emerald',
          vals, next, slow, fast, met: true, done: true, cyclePos,
          explTitle: 'Cycle Detected!',
          explText: `slow and fast both point to node ${vals[slow]}. They met inside the cycle! Return True.`,
          pause: true
        }, ctx);
        return seq;
      }
    }
    return seq;
  },
  renderDOM(container, s) {
    const chainHTML = s.vals.map((v, i) => {
      const isSlow = s.slow === i;
      const isFast = s.fast === i;
      const isMet  = s.met && isSlow && isFast;
      let cls = '';
      if (isMet) cls = 'merged active-k';
      else if (isSlow && isFast) cls = 'active-1';
      else if (isSlow) cls = 'active-1';
      else if (isFast) cls = 'active-2';

      let label = '';
      if (isSlow && isFast) label = '🐢🐇';
      else if (isSlow) label = '🐢 slow';
      else if (isFast) label = '🐇 fast';

      return `
        <div class="array-node ${cls}" style="min-width:48px;">
          ${label ? `<div class="pointer" style="opacity:1;color:${isMet ? '#34d399' : isSlow ? 'var(--accent)' : '#fbbf24'}">${label}</div>` : ''}
          ${v}
          <div class="node-index">${i}</div>
        </div>`;
    }).join('');

    const cycleInfo = s.cyclePos >= 0
      ? `<div style="font-size:12px;color:#fbbf24;font-family:var(--mono);margin-top:4px;">⟲ Last node links back to index ${s.cyclePos} (node ${s.vals[s.cyclePos]})</div>`
      : `<div style="font-size:12px;color:var(--text-dim);font-family:var(--mono);margin-top:4px;">No cycle — last node points to null</div>`;

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Linked List</div>
        <div class="array-track">${chainHTML}</div>
        ${cycleInfo}
      </div>`;
  }
});

/* ================================ 06 · Valid Parentheses (DOM) ============= */
defineAlgoDom('06_stack', {
  type: 'dom',
  title: 'Valid Parentheses', short: 'Brackets',
  idea: 'Scan left to right: push every opening bracket onto a stack. When you hit a closing bracket, pop the stack and check if it matches. If the stack is empty at the end and every pop matched, the string is valid.',
  complexity: 'Time O(n) · Space O(n)',
  input: '({[]})', hint: 'bracket string e.g. ({[]})',
  code: [
    'def isValid(s):',
    '    stack = []',
    '    match = {")":"(", "]":"[", "}":"{"}',
    '    for ch in s:',
    '        if ch in "([{":',
    '            stack.append(ch)',
    '        elif stack and stack[-1] == match[ch]:',
    '            stack.pop()',
    '        else:',
    '            return False',
    '    return len(stack) == 0',
  ],
  parse(s) {
    const str = s.trim();
    if (!str) throw new Error('Enter a bracket string');
    if (str.length > 20) throw new Error('Use at most 20 characters');
    const valid = new Set('()[]{}');
    for (const ch of str) if (!valid.has(ch)) throw new Error(`"${ch}" is not a bracket`);
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const stack = [];
    const match = { ')': '(', ']': '[', '}': '{' };
    const colors = { '(': '#38bdf8', ')': '#38bdf8', '[': '#fbbf24', ']': '#fbbf24', '{': '#34d399', '}': '#34d399' };

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      str, i: -1, stack: [...stack], result: null, popIdx: -1,
      explTitle: 'Initialization',
      explText: `Create an empty stack. We'll scan each character of "${str}" left to right.`,
      pause: true
    }, ctx);

    for (let i = 0; i < str.length; i++) {
      const ch = str[i];

      domPushState(seq, {
        kind: 'scan', line: 4, color: 'default',
        str, i, stack: [...stack], result: null, popIdx: -1,
        explTitle: `Scanning Character`,
        explText: `Look at character "${ch}" at position ${i}.`
      }, ctx);

      if ('([{'.includes(ch)) {
        stack.push(ch);
        domPushState(seq, {
          kind: 'push', line: 6, color: 'blue',
          str, i, stack: [...stack], result: null, popIdx: -1,
          explTitle: 'Push to Stack',
          explText: `"${ch}" is an opening bracket — push it onto the stack. Stack: [${stack.join(', ')}]`
        }, ctx);
      } else if (stack.length && stack[stack.length - 1] === match[ch]) {
        const popped = stack.pop();
        domPushState(seq, {
          kind: 'pop-match', line: 8, color: 'emerald',
          str, i, stack: [...stack], result: null, popIdx: i,
          explTitle: 'Match Found!',
          explText: `"${ch}" matches top of stack "${popped}". Pop it! Stack: [${stack.join(', ') || 'empty'}]`
        }, ctx);
      } else {
        domPushState(seq, {
          kind: 'mismatch', line: 10, color: 'amber',
          str, i, stack: [...stack], result: false, popIdx: -1,
          explTitle: 'Mismatch!',
          explText: stack.length
            ? `"${ch}" does not match top of stack "${stack[stack.length - 1]}". Return False.`
            : `"${ch}" is a closing bracket but the stack is empty — nothing to match. Return False.`,
          pause: true
        }, ctx);
        return seq;
      }
    }

    const valid = stack.length === 0;
    domPushState(seq, {
      kind: 'done', line: 11, color: valid ? 'emerald' : 'amber',
      str, i: str.length, stack: [...stack], result: valid, popIdx: -1,
      explTitle: valid ? 'Valid!' : 'Invalid',
      explText: valid
        ? 'Stack is empty after scanning all characters — every bracket was matched. Return True.'
        : `Stack still has [${stack.join(', ')}] remaining — unmatched opening brackets. Return False.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const colors = { '(': '#38bdf8', ')': '#38bdf8', '[': '#fbbf24', ']': '#fbbf24', '{': '#34d399', '}': '#34d399' };

    const charsHTML = [...s.str].map((ch, i) => {
      const isActive = s.i === i;
      const isPast = s.i > i;
      const col = colors[ch] || 'var(--text)';
      return `
        <div class="array-node ${isActive ? 'active-1' : ''}" style="min-width:38px;${isPast ? 'opacity:0.35;' : ''}border-color:${isActive ? col : 'var(--border)'};${isActive ? `background:color-mix(in srgb, ${col} 15%, transparent);color:${col};box-shadow:0 0 15px color-mix(in srgb, ${col} 20%, transparent);transform:translateY(-4px);` : ''}">
          ${isActive ? `<div class="pointer" style="opacity:1;color:${col}">↓ ch</div>` : ''}
          <span style="font-size:1.1rem;">${ch}</span>
          <div class="node-index">${i}</div>
        </div>`;
    }).join('');

    const stackHTML = s.stack.length
      ? [...s.stack].reverse().map((ch, i) => {
          const col = colors[ch] || 'var(--text)';
          const isTop = i === 0;
          return `
          <div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:42px;border-color:${isTop ? col : 'var(--border)'};${isTop ? `background:color-mix(in srgb, ${col} 12%, transparent);color:${col};` : ''}">
            ${isTop ? '<div class="pointer" style="opacity:1;color:#fbbf24;">← top</div>' : ''}
            <span style="font-size:1.1rem;">${ch}</span>
          </div>`;
        }).join('')
      : '<div style="color:var(--text-dim);font-size:0.8rem;padding:10px;">(empty)</div>';

    const resultHTML = s.result !== null
      ? `<div class="glass-panel" style="border-color:${s.result ? '#34d399' : '#fb7185'};background:color-mix(in srgb, ${s.result ? '#34d399' : '#fb7185'} 5%, transparent);padding:10px;text-align:center;">
           <span style="font-size:1.2rem;font-weight:700;color:${s.result ? '#34d399' : '#fb7185'};">${s.result ? '✓ Valid' : '✗ Invalid'}</span>
         </div>`
      : '';

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Input String</div>
        <div class="array-track">${charsHTML}</div>
      </div>
      <div class="glass-panel" style="min-height:80px;">
        <div class="panel-heading" style="color:#fbbf24;">Stack (top → bottom)</div>
        <div class="array-track" style="min-height:56px;">${stackHTML}</div>
      </div>
      ${resultHTML}`;
  }
});

/* ================================ 05 · Binary Search (DOM) ================ */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Binary search', short: 'Exact match',
  idea: 'Maintain a search range <code>[lo, hi]</code>. Compare the middle element with the target: if it matches, done. If the target is smaller, discard the right half; if larger, discard the left half. Each step halves the range, giving O(log n).',
  complexity: 'Time O(log n) · Space O(1)',
  input: '1, 3, 5, 7, 9, 11, 13, 15 ; 7', hint: 'sorted numbers ; target',
  code: [
    'def binary_search(nums, target):',
    '    lo, hi = 0, len(nums) - 1',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        if nums[mid] == target:',
    '            return mid',
    '        elif nums[mid] < target:',
    '            lo = mid + 1',
    '        else:',
    '            hi = mid - 1',
    '    return -1',
  ],
  parse(s) {
    const [a, t] = avParts(s);
    const nums = avNums(a, 16, 'sorted numbers');
    const target = avNum(t, 'a target');
    const sorted = nums.every((v, i) => i === 0 || v >= nums[i - 1]);
    if (!sorted) throw new Error('Array must be sorted');
    return { nums, target };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let lo = 0, hi = nums.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, lo, hi, mid: -1, found: -1,
      explTitle: 'Initialization',
      explText: `Search for ${target} in the sorted array. Set lo=0, hi=${hi}. The search range is the entire array.`,
      pause: true
    }, ctx);

    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);

      domPushState(seq, {
        kind: 'calc-mid', line: 4, color: 'blue',
        nums, target, lo, hi, mid, found: -1,
        explTitle: 'Calculate Mid',
        explText: `mid = (${lo} + ${hi}) / 2 = ${mid}. Check nums[${mid}] = ${nums[mid]}.`
      }, ctx);

      if (nums[mid] === target) {
        domPushState(seq, {
          kind: 'found', line: 6, color: 'emerald',
          nums, target, lo, hi, mid, found: mid,
          explTitle: 'Target Found!',
          explText: `nums[${mid}] = ${nums[mid]} == ${target}. Return index ${mid}.`,
          pause: true
        }, ctx);
        return seq;
      } else if (nums[mid] < target) {
        domPushState(seq, {
          kind: 'go-right', line: 8, color: 'amber',
          nums, target, lo, hi, mid, found: -1,
          explTitle: 'Target is Larger',
          explText: `${nums[mid]} < ${target}, so the target is in the right half. Set lo = mid + 1 = ${mid + 1}. Discard the left half.`
        }, ctx);
        lo = mid + 1;
      } else {
        domPushState(seq, {
          kind: 'go-left', line: 10, color: 'amber',
          nums, target, lo, hi, mid, found: -1,
          explTitle: 'Target is Smaller',
          explText: `${nums[mid]} > ${target}, so the target is in the left half. Set hi = mid - 1 = ${mid - 1}. Discard the right half.`
        }, ctx);
        hi = mid - 1;
      }
    }

    domPushState(seq, {
      kind: 'not-found', line: 11, color: 'amber',
      nums, target, lo, hi, mid: -1, found: -1,
      explTitle: 'Not Found',
      explText: `lo (${lo}) > hi (${hi}). The search range is empty — ${target} is not in the array. Return -1.`,
      pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const arrHTML = s.nums.map((v, i) => {
      const isLo  = i === s.lo;
      const isHi  = i === s.hi;
      const isMid = i === s.mid;
      const isFound = i === s.found;
      const inRange = i >= s.lo && i <= s.hi;
      const eliminated = !inRange && s.found < 0;

      let cls = '';
      if (isFound) cls = 'merged active-k';
      else if (isMid) cls = 'active-1';
      else if (eliminated) cls = '';

      let label = '';
      if (isMid && isLo && isHi) label = 'lo,mid,hi';
      else if (isMid && isLo) label = 'lo,mid';
      else if (isMid && isHi) label = 'mid,hi';
      else if (isMid) label = 'mid';
      else if (isLo) label = 'lo';
      else if (isHi) label = 'hi';

      const labelColor = isMid ? 'var(--accent)' : isLo ? '#38bdf8' : '#fbbf24';

      return `
        <div class="array-node ${cls}" style="min-width:42px;${eliminated ? 'opacity:0.2;' : ''}${isFound ? '' : isMid ? '' : ''}">
          ${label ? `<div class="pointer" style="opacity:1;color:${labelColor}">↓ ${label}</div>` : ''}
          ${v}
          <div class="node-index">${i}</div>
        </div>`;
    }).join('');

    // Range bracket
    const rangeHTML = s.lo <= s.hi
      ? `<div style="font-size:12px;color:var(--accent);font-family:var(--mono);margin-top:4px;">Search range: [${s.lo}..${s.hi}] — ${s.hi - s.lo + 1} elements</div>`
      : `<div style="font-size:12px;color:#fb7185;font-family:var(--mono);margin-top:4px;">Search range empty (lo > hi)</div>`;

    const resultHTML = s.found >= 0
      ? `<div class="glass-panel" style="border-color:#34d399;background:color-mix(in srgb, #34d399 5%, transparent);padding:10px;text-align:center;">
           <span style="font-size:1.1rem;font-weight:700;color:#34d399;">Found ${s.target} at index ${s.found}</span>
         </div>`
      : s.kind === 'not-found'
        ? `<div class="glass-panel" style="border-color:#fb7185;background:color-mix(in srgb, #fb7185 5%, transparent);padding:10px;text-align:center;">
             <span style="font-size:1.1rem;font-weight:700;color:#fb7185;">${s.target} not found → return -1</span>
           </div>`
        : '';

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Sorted Array — target = ${s.target}</div>
        <div class="array-track">${arrHTML}</div>
        ${rangeHTML}
      </div>
      ${resultHTML}`;
  }
});

/* ================================ 03 · Buy and Sell Stock (DOM) ============ */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Best Time to Buy and Sell Stock', short: 'Buy/Sell Stock',
  idea: 'Track the <b>minimum price seen so far</b> as you scan left to right. At each day, the potential profit is <code>price[i] − min_so_far</code>. Keep updating the maximum of those profits.',
  complexity: 'Time O(n) · Space O(1)',
  input: '7, 1, 5, 3, 6, 4', hint: 'prices per day',
  code: [
    'def maxProfit(prices):',
    '    min_price = float("inf")',
    '    max_profit = 0',
    '    for price in prices:',
    '        if price < min_price:',
    '            min_price = price',
    '        profit = price - min_price',
    '        if profit > max_profit:',
    '            max_profit = profit',
    '    return max_profit',
  ],
  parse(s) { return { prices: avNums(s, 16, 'prices') }; },
  buildStates({ prices }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let minPrice = Infinity, maxProfit = 0, buyDay = -1, bestBuy = -1, bestSell = -1;

    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      prices, i: -1, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: 0,
      explTitle: 'Initialization',
      explText: `Set min_price = ∞ and max_profit = 0. We want to find the best day to buy (lowest) and sell (highest after buying).`,
      pause: true
    }, ctx);

    for (let i = 0; i < prices.length; i++) {
      const price = prices[i];

      domPushState(seq, {
        kind: 'scan', line: 4, color: 'default',
        prices, i, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: 0,
        explTitle: `Day ${i}`,
        explText: `Look at price ${price} on day ${i}.`
      }, ctx);

      if (price < minPrice) {
        minPrice = price;
        buyDay = i;
        domPushState(seq, {
          kind: 'new-min', line: 6, color: 'blue',
          prices, i, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: 0,
          explTitle: 'New Minimum Price',
          explText: `${price} < previous min. Update min_price = ${price} (potential buy day = ${i}).`
        }, ctx);
      }

      const profit = price - minPrice;
      domPushState(seq, {
        kind: 'calc-profit', line: 7, color: 'default',
        prices, i, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: profit,
        explTitle: 'Calculate Profit',
        explText: `If we bought at ${minPrice} (day ${buyDay}) and sold today at ${price}: profit = ${price} - ${minPrice} = ${profit}.`
      }, ctx);

      if (profit > maxProfit) {
        maxProfit = profit;
        bestBuy = buyDay;
        bestSell = i;
        domPushState(seq, {
          kind: 'new-max', line: 9, color: 'emerald',
          prices, i, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: profit,
          explTitle: 'New Best Profit!',
          explText: `${profit} > previous max_profit. Update max_profit = ${profit} (buy day ${bestBuy}, sell day ${bestSell}).`,
          pause: i === prices.length - 1
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      prices, i: prices.length, minPrice, maxProfit, buyDay, bestBuy, bestSell, curProfit: 0,
      explTitle: 'Complete',
      explText: maxProfit > 0
        ? `Maximum profit = ${maxProfit}. Buy on day ${bestBuy} (price ${prices[bestBuy]}), sell on day ${bestSell} (price ${prices[bestSell]}).`
        : `No profitable trade exists. Prices never increased. Return 0.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const maxVal = Math.max(...s.prices, 1);

    const barsHTML = s.prices.map((p, i) => {
      const isActive = s.i === i;
      const isBuy = s.bestBuy === i && s.maxProfit > 0;
      const isSell = s.bestSell === i && s.maxProfit > 0;
      const isBuyDay = s.buyDay === i;
      const height = Math.max(8, (p / maxVal) * 80);

      let cls = '';
      if (isActive) cls = 'active-1';
      else if (isBuy) cls = 'active-2';
      else if (isSell) cls = 'merged active-k';

      let label = '';
      if (isActive && isBuyDay) label = '↓ min';
      else if (isActive) label = '↓ i';

      const barColor = isBuy ? '#38bdf8' : isSell ? '#34d399' : isActive ? 'var(--accent)' : 'var(--text-dim)';

      return `
        <div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1;min-width:32px;">
          <div style="font-size:10px;color:${barColor};font-family:var(--mono);font-weight:600;">${p}</div>
          <div style="width:100%;max-width:36px;height:${height}px;background:color-mix(in srgb, ${barColor} ${isActive || isBuy || isSell ? '40' : '20'}%, transparent);border:1px solid ${barColor};border-radius:4px 4px 0 0;transition:all 0.3s;${isActive ? 'box-shadow:0 0 10px color-mix(in srgb, var(--accent) 30%, transparent);' : ''}"></div>
          <div style="font-size:10px;color:var(--text-dim);font-family:var(--mono);">${i}</div>
          ${isBuy ? '<div style="font-size:9px;color:#38bdf8;font-weight:700;">BUY</div>' : ''}
          ${isSell ? '<div style="font-size:9px;color:#34d399;font-weight:700;">SELL</div>' : ''}
        </div>`;
    }).join('');

    const statsHTML = `
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;">
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">min_price</span> <b style="color:#38bdf8;">${s.minPrice === Infinity ? '∞' : s.minPrice}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">cur_profit</span> <b style="color:var(--accent);">${s.curProfit}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:color-mix(in srgb, #34d399 10%, transparent);border:1px solid color-mix(in srgb, #34d399 30%, transparent);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">max_profit</span> <b style="color:#34d399;">${s.maxProfit}</b>
        </div>
      </div>`;

    container.innerHTML = `
      <div class="glass-panel">
        <div class="panel-heading" style="color:var(--accent);">Prices per Day</div>
        <div style="display:flex;gap:4px;align-items:flex-end;padding:12px 4px;min-height:120px;">${barsHTML}</div>
        ${statsHTML}
      </div>`;
  }
});

/* ================================ 10 · Invert Binary Tree (DOM) =========== */
defineAlgoDom('10_trees', {
  type: 'dom',
  title: 'Invert Binary Tree', short: 'Invert Tree',
  idea: 'Recursively swap every node\'s left and right children. At each node: swap children, then recurse into both subtrees. The base case is a null node.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '4, 2, 7, 1, 3, 6, 9', hint: 'level-order tree values',
  code: [
    'def invertTree(root):',
    '    if not root:',
    '        return None',
    '    root.left, root.right = root.right, root.left',
    '    invertTree(root.left)',
    '    invertTree(root.right)',
    '    return root',
  ],
  parse(s) {
    const vals = s.trim().split(/[\s,]+/).map(x => x === 'null' ? null : Number(x));
    if (!vals.length || vals[0] === null) throw new Error('Tree must have a root');
    if (vals.some(v => v !== null && !Number.isFinite(v))) throw new Error('Use numbers or null');
    if (vals.length > 15) throw new Error('Use at most 15 nodes for readability');
    return { vals };
  },
  buildStates({ vals }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    // Build tree as array of {val, left, right} or null
    const tree = vals.map(v => v !== null ? { val: v, left: -1, right: -1 } : null);
    for (let i = 0; i < tree.length; i++) {
      if (!tree[i]) continue;
      const l = 2 * i + 1, r = 2 * i + 2;
      tree[i].left = l < tree.length && tree[l] ? l : -1;
      tree[i].right = r < tree.length && tree[r] ? r : -1;
    }

    const snap = () => tree.filter(n => n).map(n => ({ ...n }));
    const swapped = new Set();

    domPushState(seq, {
      kind: 'init', line: 1, color: 'default',
      tree: snap(), cur: -1, swapped: new Set(), treeLen: tree.length,
      explTitle: 'Start',
      explText: `We'll recursively visit every node and swap its left and right children.`,
      pause: true
    }, ctx);

    function dfs(i) {
      if (i < 0 || i >= tree.length || !tree[i]) return;

      domPushState(seq, {
        kind: 'visit', line: 1, color: 'blue',
        tree: snap(), cur: i, swapped: new Set(swapped), treeLen: tree.length,
        explTitle: `Visit Node ${tree[i].val}`,
        explText: `At node ${tree[i].val}. Swap its left (${tree[i].left >= 0 ? tree[tree[i].left].val : 'null'}) and right (${tree[i].right >= 0 ? tree[tree[i].right].val : 'null'}) children.`
      }, ctx);

      // Swap
      const tmp = tree[i].left;
      tree[i].left = tree[i].right;
      tree[i].right = tmp;
      swapped.add(i);

      domPushState(seq, {
        kind: 'swap', line: 4, color: 'emerald',
        tree: snap(), cur: i, swapped: new Set(swapped), treeLen: tree.length,
        explTitle: `Swapped Children of ${tree[i].val}`,
        explText: `Now left = ${tree[i].left >= 0 ? tree[tree[i].left].val : 'null'}, right = ${tree[i].right >= 0 ? tree[tree[i].right].val : 'null'}.`
      }, ctx);

      dfs(tree[i].left);
      dfs(tree[i].right);
    }

    dfs(0);

    domPushState(seq, {
      kind: 'done', line: 7, color: 'emerald',
      tree: snap(), cur: -1, swapped: new Set(swapped), treeLen: tree.length,
      explTitle: 'Inversion Complete',
      explText: `Every node's children have been swapped. The tree is now a mirror image of the original.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    // Simple level-order tree rendering
    const tree = s.tree;
    if (!tree.length) { container.innerHTML = '<div style="color:var(--text-dim);padding:20px;">Empty tree</div>'; return; }

    // Calculate tree depth for layout
    let maxIdx = 0;
    tree.forEach((n, i) => { if (n) maxIdx = i; });
    const depth = Math.floor(Math.log2(maxIdx + 1)) + 1;

    let treeHTML = '';
    for (let d = 0; d < depth; d++) {
      const start = Math.pow(2, d) - 1;
      const count = Math.pow(2, d);
      let levelHTML = '';
      for (let k = 0; k < count; k++) {
        const idx = start + k;
        const node = idx < tree.length ? tree[idx] : null;
        if (node) {
          const isCur = s.cur === idx;
          const isSwapped = s.swapped.has(idx);
          let cls = '';
          if (isCur) cls = 'active-1';
          else if (isSwapped) cls = 'merged';

          levelHTML += `
            <div class="array-node ${cls}" style="min-width:40px;height:40px;border-radius:50%;margin:2px auto;">
              ${isCur ? '<div class="pointer" style="opacity:1;color:var(--accent);">↓</div>' : ''}
              ${node.val}
            </div>`;
        } else {
          levelHTML += `<div style="min-width:40px;height:40px;margin:2px auto;"></div>`;
        }
      }
      treeHTML += `<div style="display:flex;justify-content:space-around;align-items:center;gap:4px;">${levelHTML}</div>`;
    }

    container.innerHTML = `
      <div class="glass-panel">
        <div class="panel-heading" style="color:var(--accent);">Binary Tree</div>
        <div style="display:flex;flex-direction:column;gap:8px;padding:12px;">${treeHTML}</div>
      </div>`;
  }
});

/* ================================ 02 · Container With Most Water (DOM) ===== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Container With Most Water', short: 'Most water',
  idea: 'Start with the widest container (pointers at both ends). The area is <code>min(left, right) × width</code>. To potentially find a larger area, move the <b>shorter</b> side inward — moving the taller side can only shrink or keep the area the same.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 8, 6, 2, 5, 4, 8, 3, 7', hint: 'heights',
  code: [
    'def maxArea(height):',
    '    l, r = 0, len(height) - 1',
    '    best = 0',
    '    while l < r:',
    '        area = min(height[l], height[r]) * (r - l)',
    '        best = max(best, area)',
    '        if height[l] < height[r]:',
    '            l += 1',
    '        else:',
    '            r -= 1',
    '    return best',
  ],
  parse(s) {
    const h = avNums(s, 16, 'heights');
    if (h.length < 2) throw new Error('Need at least 2 heights');
    return { heights: h };
  },
  buildStates({ heights }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let l = 0, r = heights.length - 1, best = 0, bestL = -1, bestR = -1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      heights, l, r, area: 0, best, bestL, bestR,
      explTitle: 'Initialization',
      explText: `Start with the widest container: l=0, r=${r}. We'll greedily move the shorter side inward.`,
      pause: true
    }, ctx);

    while (l < r) {
      const area = Math.min(heights[l], heights[r]) * (r - l);

      domPushState(seq, {
        kind: 'calc-area', line: 5, color: 'blue',
        heights, l, r, area, best, bestL, bestR,
        explTitle: 'Calculate Area',
        explText: `area = min(${heights[l]}, ${heights[r]}) × (${r} - ${l}) = ${Math.min(heights[l], heights[r])} × ${r - l} = ${area}.`
      }, ctx);

      if (area > best) {
        best = area;
        bestL = l;
        bestR = r;
        domPushState(seq, {
          kind: 'new-best', line: 6, color: 'emerald',
          heights, l, r, area, best, bestL, bestR,
          explTitle: 'New Best!',
          explText: `${area} > previous best. Update best = ${area} (between indices ${l} and ${r}).`
        }, ctx);
      }

      if (heights[l] < heights[r]) {
        domPushState(seq, {
          kind: 'move-left', line: 8, color: 'amber',
          heights, l, r, area, best, bestL, bestR,
          explTitle: 'Move Left Pointer',
          explText: `height[${l}] (${heights[l]}) < height[${r}] (${heights[r]}). Move the shorter side: l++ = ${l + 1}.`
        }, ctx);
        l++;
      } else {
        domPushState(seq, {
          kind: 'move-right', line: 10, color: 'amber',
          heights, l, r, area, best, bestL, bestR,
          explTitle: 'Move Right Pointer',
          explText: `height[${l}] (${heights[l]}) >= height[${r}] (${heights[r]}). Move the shorter side: r-- = ${r - 1}.`
        }, ctx);
        r--;
      }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      heights, l, r, area: 0, best, bestL, bestR,
      explTitle: 'Complete',
      explText: `Pointers crossed. Maximum area = ${best} (between indices ${bestL} and ${bestR}).`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const maxH = Math.max(...s.heights, 1);

    const barsHTML = s.heights.map((h, i) => {
      const isL = i === s.l;
      const isR = i === s.r;
      const isBestL = i === s.bestL && s.best > 0;
      const isBestR = i === s.bestR && s.best > 0;
      const inRange = i >= s.l && i <= s.r;
      const isWaterCol = i > s.l && i < s.r;
      const barH = Math.max(4, (h / maxH) * 100);
      const waterH = isWaterCol ? Math.max(4, (Math.min(s.heights[s.l], s.heights[s.r]) / maxH) * 100) : 0;

      let barColor = 'var(--text-dim)';
      if (isL) barColor = '#38bdf8';
      else if (isR) barColor = '#fbbf24';
      else if (!inRange) barColor = 'color-mix(in srgb, var(--text-dim) 30%, transparent)';

      let label = '';
      if (isL) label = '↑ L';
      if (isR) label = '↑ R';

      return `
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;min-width:24px;position:relative;">
          <div style="font-size:10px;color:${barColor};font-family:var(--mono);font-weight:600;">${h}</div>
          <div style="position:relative;width:100%;max-width:32px;height:${barH}px;">
            <div style="position:absolute;bottom:0;width:100%;height:100%;background:color-mix(in srgb, ${barColor} ${isL || isR ? '45' : '20'}%, transparent);border:1px solid ${barColor};border-radius:3px 3px 0 0;z-index:2;"></div>
            ${isWaterCol ? `<div style="position:absolute;bottom:0;width:100%;height:${waterH}px;background:color-mix(in srgb, #38bdf8 15%, transparent);border-left:1px dashed color-mix(in srgb, #38bdf8 20%, transparent);border-right:1px dashed color-mix(in srgb, #38bdf8 20%, transparent);z-index:1;"></div>` : ''}
          </div>
          <div style="font-size:10px;color:var(--text-dim);font-family:var(--mono);">${i}</div>
          ${label ? `<div style="font-size:10px;color:${isL ? '#38bdf8' : '#fbbf24'};font-weight:700;font-family:var(--mono);">${label}</div>` : ''}
        </div>`;
    }).join('');

    const statsHTML = `
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;">
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">current area</span> <b style="color:var(--accent);">${s.area}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:color-mix(in srgb, #34d399 10%, transparent);border:1px solid color-mix(in srgb, #34d399 30%, transparent);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">best area</span> <b style="color:#34d399;">${s.best}</b>
        </div>
      </div>`;

    container.innerHTML = `
      <div class="glass-panel">
        <div class="panel-heading" style="color:var(--accent);">Heights</div>
        <div style="display:flex;gap:2px;align-items:flex-end;padding:12px 4px;min-height:140px;">${barsHTML}</div>
        ${statsHTML}
      </div>`;
  }
});

/* ================================ 04 · Subarray Sum Equals K (DOM) ========= */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Subarray Sum Equals K', short: 'Sum equals K',
  idea: 'Use a running sum and a hash map of <code>{prefix_sum: count}</code>. At each step, if <code>sum - k</code> is in the map, it means there are that many subarrays ending here that sum to <code>k</code>.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, -1, 1, 1, 1, 1 ; 2', hint: 'numbers ; k',
  code: [
    'def subarraySum(nums, k):',
    '    counts = {0: 1}',
    '    curr_sum = ans = 0',
    '    for x in nums:',
    '        curr_sum += x',
    '        if (curr_sum - k) in counts:',
    '            ans += counts[curr_sum - k]',
    '        counts[curr_sum] = counts.get(curr_sum, 0) + 1',
    '    return ans',
  ],
  parse(s) {
    const [a, kStr] = avParts(s);
    return { nums: avNums(a, 16), k: avNum(kStr, 'k') };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const counts = { 0: 1 };
    let curr_sum = 0, ans = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, i: -1, curr_sum, ans, counts: { ...counts }, match: null,
      explTitle: 'Initialization',
      explText: `We want subarrays that sum to ${k}. We initialize the hash map with {0: 1} to handle subarrays that start at index 0.`,
      pause: true
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      curr_sum += nums[i];
      domPushState(seq, {
        kind: 'running-sum', line: 5, color: 'blue',
        nums, k, i, curr_sum, ans, counts: { ...counts }, match: null,
        explTitle: 'Update Running Sum',
        explText: `Added nums[${i}] = ${nums[i]}. New running sum = ${curr_sum}.`
      }, ctx);

      const lookback = curr_sum - k;
      const found = counts[lookback] || 0;
      
      domPushState(seq, {
        kind: 'check-map', line: 6, color: found ? 'emerald' : 'amber',
        nums, k, i, curr_sum, ans, counts: { ...counts }, match: lookback,
        explTitle: 'Check Hash Map',
        explText: `We need a previous prefix sum of (curr_sum - k) = (${curr_sum} - ${k}) = ${lookback}. Is ${lookback} in our map? ${found ? 'Yes!' : 'No.'}`
      }, ctx);

      if (found) {
        ans += found;
        domPushState(seq, {
          kind: 'match', line: 7, color: 'emerald',
          nums, k, i, curr_sum, ans, counts: { ...counts }, match: lookback,
          explTitle: 'Found Subarray(s)!',
          explText: `We found ${found} past prefix sum(s) equal to ${lookback}. Added ${found} to total ans. Total ans = ${ans}.`,
          pause: true
        }, ctx);
      }

      counts[curr_sum] = (counts[curr_sum] || 0) + 1;
      domPushState(seq, {
        kind: 'update-map', line: 8, color: 'default',
        nums, k, i, curr_sum, ans, counts: { ...counts }, match: null,
        explTitle: 'Update Map',
        explText: `Add current prefix sum (${curr_sum}) to the hash map so future iterations can find it.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 9, color: 'emerald',
      nums, k, i: nums.length, curr_sum, ans, counts: { ...counts }, match: null,
      explTitle: 'Complete',
      explText: `Finished processing array. Total subarrays summing to ${k} = ${ans}.`,
      pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const arrHTML = s.nums.map((v, i) => {
      const isActive = s.i === i;
      const isPast = s.i > i;
      let cls = isActive ? 'active-1' : isPast ? 'merged' : '';
      return `
        <div class="array-node ${cls}" style="min-width:40px;${!isActive && !isPast ? 'opacity:0.3;' : ''}">
          ${isActive ? '<div class="pointer" style="opacity:1;color:var(--accent);">↓</div>' : ''}
          ${v}
          <div class="node-index">${i}</div>
        </div>`;
    }).join('');

    const mapEntries = Object.entries(s.counts).map(([sumStr, count]) => {
      const sum = Number(sumStr);
      const isMatch = s.match === sum;
      return `
        <div style="display:inline-flex; align-items:baseline; gap:6px; padding:6px 12px; border-radius:999px; font-family:var(--mono); font-size:12px; border:1px solid ${isMatch ? '#34d399' : 'var(--border)'}; background:${isMatch ? 'rgba(52, 211, 153, 0.15)' : 'var(--surface)'}; color:${isMatch ? '#34d399' : 'var(--text)'}; ${isMatch ? 'box-shadow:0 0 10px rgba(52, 211, 153, 0.2); transform:scale(1.05); transition:all 0.2s;' : ''}">
          <span>sum ${sum}</span> <span style="color:var(--text-faint)">→</span> <b>count ${count}</b>
        </div>`;
    }).join('');

    const statsHTML = `
      <div style="display:flex;gap:12px;margin-top:10px;">
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:13px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">k (target)</span> <b style="color:#fbbf24;">${s.k}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:13px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">curr_sum</span> <b style="color:var(--accent);">${s.curr_sum}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:color-mix(in srgb, #34d399 10%, transparent);border:1px solid color-mix(in srgb, #34d399 30%, transparent);font-size:13px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">total ans</span> <b style="color:#34d399;">${s.ans}</b>
        </div>
      </div>`;

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Array & Running Sum</div>
        <div class="array-track">${arrHTML}</div>
        ${statsHTML}
      </div>
      <div class="glass-panel" style="min-height:90px;">
        <div class="panel-heading" style="color:#fbbf24;">Prefix Sum Hash Map</div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; padding:8px 4px;">${mapEntries}</div>
        ${s.match !== null && !(s.match in s.counts) ? `<div style="color:#fb7185; font-size:12px; font-weight:600; margin-top:8px;">${s.match} is not in the map</div>` : ''}
      </div>`;
  }
});

/* ================================ 07 · Implement Queue using Stacks (DOM) == */
defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: 'Implement Queue using Stacks', short: 'Queue via Stacks',
  idea: 'We need FIFO behavior but only have LIFO stacks. Keep two stacks: <code>push_stack</code> and <code>pop_stack</code>. Push items to push_stack. When we need to pop/peek, if pop_stack is empty, pour <b>everything</b> from push_stack into pop_stack. This reverses the order, placing the oldest element at the top!',
  complexity: 'Time O(1) amortized · Space O(n)',
  input: 'push 1, push 2, peek, pop, push 3, pop', hint: 'comma-separated operations (push X, pop, peek)',
  code: [
    'class MyQueue:',
    '    def __init__(self):',
    '        self.push_s = []',
    '        self.pop_s = []',
    '',
    '    def push(self, x):',
    '        self.push_s.append(x)',
    '',
    '    def pop(self):',
    '        self.peek()',
    '        return self.pop_s.pop()',
    '',
    '    def peek(self):',
    '        if not self.pop_s:',
    '            while self.push_s:',
    '                self.pop_s.append(self.push_s.pop())',
    '        return self.pop_s[-1]',
  ],
  parse(s) {
    const ops = s.split(',').map(x => x.trim().toLowerCase()).filter(Boolean);
    if (!ops.length) throw new Error('Enter operations like: push 1, pop');
    return { ops };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const push_s = [], pop_s = [];

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      ops, opIdx: -1, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: false,
      explTitle: 'Initialization',
      explText: 'Create two empty stacks: push_s and pop_s.',
      pause: true
    }, ctx);

    for (let opIdx = 0; opIdx < ops.length; opIdx++) {
      const opStr = ops[opIdx];
      const parts = opStr.split(/\s+/);
      const cmd = parts[0];

      if (cmd === 'push') {
        const val = Number(parts[1]);
        push_s.push(val);
        domPushState(seq, {
          kind: 'push', line: 7, color: 'blue',
          ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: false,
          explTitle: `Push ${val}`,
          explText: `Always push directly onto push_s. It is O(1).`
        }, ctx);
      } else if (cmd === 'peek' || cmd === 'pop') {
        domPushState(seq, {
          kind: cmd, line: cmd === 'pop' ? 10 : 14, color: 'amber',
          ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: false,
          explTitle: cmd === 'pop' ? 'Pop Operation' : 'Peek Operation',
          explText: `We need the oldest element. It should be at the top of pop_s. Is pop_s empty? ${pop_s.length === 0 ? 'Yes.' : 'No.'}`
        }, ctx);

        if (pop_s.length === 0) {
          domPushState(seq, {
            kind: 'pour-start', line: 15, color: 'amber',
            ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: true,
            explTitle: 'Pouring Stacks',
            explText: 'pop_s is empty! We must pour all elements from push_s into pop_s to reverse their order.'
          }, ctx);

          while (push_s.length > 0) {
            const moving = push_s.pop();
            pop_s.push(moving);
            domPushState(seq, {
              kind: 'pouring', line: 16, color: 'blue',
              ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: true,
              explTitle: 'Pouring...',
              explText: `Moved ${moving} from push_s to pop_s.`
            }, ctx);
          }
        }

        const top = pop_s[pop_s.length - 1];
        if (cmd === 'peek') {
          domPushState(seq, {
            kind: 'peek-done', line: 17, color: 'emerald',
            ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: top, pouring: false,
            explTitle: 'Peek Complete',
            explText: `The oldest element is ${top} at the top of pop_s.`,
            pause: true
          }, ctx);
        } else {
          pop_s.pop();
          domPushState(seq, {
            kind: 'pop-done', line: 11, color: 'emerald',
            ops, opIdx, push_s: [...push_s], pop_s: [...pop_s], result: top, pouring: false,
            explTitle: 'Pop Complete',
            explText: `Popped ${top} from pop_s.`,
            pause: true
          }, ctx);
        }
      }
    }

    domPushState(seq, {
      kind: 'done', line: -1, color: 'emerald',
      ops, opIdx: ops.length, push_s: [...push_s], pop_s: [...pop_s], result: null, pouring: false,
      explTitle: 'Finished',
      explText: 'All operations complete.',
      pause: true
    }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const renderStack = (stack, title, color) => {
      const items = [...stack].reverse().map((v, i) => {
        const isTop = i === 0;
        return `
          <div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:48px;border-color:${isTop ? color : 'var(--border)'};${isTop ? `background:color-mix(in srgb, ${color} 12%, transparent);color:${color};` : ''}">
            ${isTop ? `<div class="pointer" style="opacity:1;color:${color};left:-30px;top:10px;">top →</div>` : ''}
            <span style="font-size:1.1rem;font-weight:700;">${v}</span>
          </div>`;
      }).join('');
      
      return `
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;">
          <div style="font-size:12px;font-weight:600;color:${color};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">${title}</div>
          <div style="display:flex;flex-direction:column;gap:4px;border-left:2px solid var(--border);border-right:2px solid var(--border);border-bottom:2px solid var(--border);border-radius:0 0 8px 8px;padding:8px;min-height:160px;width:100px;justify-content:flex-end;background:color-mix(in srgb, ${color} 3%, transparent);">
            ${items || '<div style="text-align:center;color:var(--text-dim);font-size:12px;margin-bottom:10px;">(empty)</div>'}
          </div>
        </div>`;
    };

    const opsList = s.ops.map((op, i) => {
      const isCur = s.opIdx === i;
      const isPast = s.opIdx > i;
      return `<div style="padding:4px 8px;border-radius:4px;font-family:var(--mono);font-size:12px;${isCur ? 'background:var(--accent);color:var(--accent-ink);font-weight:bold;' : isPast ? 'color:var(--text-dim);text-decoration:line-through;' : 'color:var(--text);'}">${op}</div>`;
    }).join('');

    const resultBox = s.result !== null
      ? `<div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:color-mix(in srgb, #34d399 15%, transparent);border:1px solid #34d399;color:#34d399;font-weight:bold;text-align:center;">Returned: ${s.result}</div>`
      : '';

    container.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:8px;">
        ${opsList}
      </div>
      <div class="glass-panel" style="flex-direction:row;justify-content:space-around;padding:24px 12px;gap:20px;position:relative;">
        ${renderStack(s.push_s, 'Push Stack', '#38bdf8')}
        ${s.pouring ? '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);font-size:24px;color:#fbbf24;animation:pulse 1s infinite;">⟿</div>' : ''}
        ${renderStack(s.pop_s, 'Pop Stack', '#34d399')}
      </div>
      ${resultBox}`;
  }
});

/* ================================ 09 · Subsets (DOM) ======================= */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'Subsets', short: 'Subsets',
  idea: 'At each element in the array, we have a choice: <b>Include it</b> or <b>Exclude it</b>. This creates a decision tree of height <code>n</code>, with exactly <code>2^n</code> leaves (the subsets).',
  complexity: 'Time O(n * 2^n) · Space O(n)',
  input: '1, 2, 3', hint: 'comma-separated distinct numbers',
  code: [
    'def subsets(nums):',
    '    ans = []',
    '    def dfs(i, path):',
    '        if i == len(nums):',
    '            ans.append(list(path))',
    '            return',
    '        ',
    '        # Choice 1: Include nums[i]',
    '        path.append(nums[i])',
    '        dfs(i + 1, path)',
    '        path.pop()',
    '        ',
    '        # Choice 2: Exclude nums[i]',
    '        dfs(i + 1, path)',
    '    ',
    '    dfs(0, [])',
    '    return ans',
  ],
  parse(s) {
    const nums = avNums(s, 6); // Max 6 to prevent 2^n explosion
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const ans = [];
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, path: [], ans: [...ans], i: 0, depth: 0,
      explTitle: 'Start Backtracking',
      explText: `We want to generate all subsets of [${nums.join(', ')}]. Start with an empty path at index 0.`,
      pause: true
    }, ctx);

    function dfs(i, path, depth) {
      if (i === nums.length) {
        ans.push([...path]);
        domPushState(seq, {
          kind: 'base-case', line: 4, color: 'emerald',
          nums, path: [...path], ans: [...ans], i, depth,
          explTitle: 'Base Case Reached',
          explText: `Index is ${i}. We've made decisions for all elements. Add current path [${path.join(', ')}] to results!`,
          pause: true
        }, ctx);
        return;
      }

      domPushState(seq, {
        kind: 'choice-include', line: 8, color: 'blue',
        nums, path: [...path, nums[i]], ans: [...ans], i, depth,
        explTitle: `Choice: Include ${nums[i]}`,
        explText: `Add ${nums[i]} to the current path.`
      }, ctx);
      
      dfs(i + 1, [...path, nums[i]], depth + 1);

      domPushState(seq, {
        kind: 'backtrack', line: 11, color: 'amber',
        nums, path: [...path], ans: [...ans], i, depth,
        explTitle: 'Backtrack',
        explText: `Finished exploring branch with ${nums[i]}. Pop it off to try the other choice.`
      }, ctx);

      domPushState(seq, {
        kind: 'choice-exclude', line: 14, color: 'default',
        nums, path: [...path], ans: [...ans], i, depth,
        explTitle: `Choice: Exclude ${nums[i]}`,
        explText: `Skip ${nums[i]} and move to the next index.`
      }, ctx);

      dfs(i + 1, [...path], depth + 1);
    }

    dfs(0, [], 0);

    domPushState(seq, {
      kind: 'done', line: 17, color: 'emerald',
      nums, path: [], ans: [...ans], i: nums.length, depth: 0,
      explTitle: 'Complete',
      explText: `Generated all ${ans.length} subsets.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const arrayHTML = s.nums.map((v, i) => {
      const isCur = s.i === i;
      const isPast = s.i > i;
      let cls = isCur ? 'active-1' : isPast ? 'merged' : '';
      return `
        <div class="array-node ${cls}" style="${!isCur && !isPast ? 'opacity:0.3;' : ''}">
          ${isCur ? '<div class="pointer" style="opacity:1;color:var(--accent);">↓</div>' : ''}
          ${v}
        </div>`;
    }).join('');

    const pathHTML = s.path.length === 0 ? '<span style="color:var(--text-dim);">[ ]</span>' : `[ ${s.path.join(', ')} ]`;

    const resultsHTML = s.ans.map(sub => `
      <div style="padding:4px 8px;border-radius:4px;background:var(--surface);border:1px solid var(--border);font-family:var(--mono);font-size:13px;">
        [ ${sub.join(', ')} ]
      </div>
    `).join('');

    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:var(--accent);">Input Array (idx = ${s.i})</div>
        <div class="array-track">${arrayHTML}</div>
      </div>
      <div style="display:flex;gap:12px;margin:12px 0;">
        <div class="glass-panel" style="flex:1;min-height:80px;align-items:center;justify-content:center;">
          <div class="panel-heading" style="color:#fbbf24;">Current Path</div>
          <div style="font-family:var(--mono);font-size:20px;font-weight:bold;color:var(--accent);">${pathHTML}</div>
        </div>
      </div>
      <div class="glass-panel" style="min-height:120px;">
        <div class="panel-heading" style="color:#34d399;">Results (${s.ans.length} found)</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;padding:8px 4px;">
          ${resultsHTML || '<div style="color:var(--text-dim);font-style:italic;">None yet...</div>'}
        </div>
      </div>`;
  }
});

/* ================================ 11 · Insert into BST (DOM) =============== */
defineAlgoDom('11_binary_search_tree', {
  type: 'dom',
  title: 'Insert into a Binary Search Tree', short: 'Insert into BST',
  idea: 'Traverse the tree: if the new value is less than the current node, go left; if greater, go right. When we hit a <code>null</code> pointer, that is exactly where the new node belongs!',
  complexity: 'Time O(H) · Space O(H) (where H is tree height)',
  input: '4,2,7,1,3,null,null ; 5', hint: 'BST node values ; value to insert',
  code: [
    'def insertIntoBST(root, val):',
    '    if not root:',
    '        return TreeNode(val)',
    '',
    '    if val < root.val:',
    '        root.left = insertIntoBST(root.left, val)',
    '    else:',
    '        root.right = insertIntoBST(root.right, val)',
    '        ',
    '    return root',
  ],
  parse(s) {
    const [treeStr, valStr] = avParts(s);
    return { tree: avTree(treeStr), val: avNum(valStr, 'val') };
  },
  buildStates({ tree, val }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    // We will build a flat node dictionary to track the tree structure
    const nodes = {};
    let rootId = null;

    // Helper to extract the initial tree structure
    function buildNodeMap(node, id = '0') {
      if (!node) return null;
      nodes[id] = { val: node.val, left: null, right: null };
      if (rootId === null) rootId = id;
      
      if (node.left) nodes[id].left = buildNodeMap(node.left, id + 'L');
      if (node.right) nodes[id].right = buildNodeMap(node.right, id + 'R');
      return id;
    }
    
    buildNodeMap(tree);

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: rootId,
      explTitle: 'Initialization',
      explText: `We want to insert ${val} into the BST. We start at the root.`,
      pause: true
    }, ctx);

    function dfs(nodeId, parentId, isLeft) {
      if (!nodeId) {
        // Base case: we hit a null pointer, insert here
        const newId = parentId ? (parentId + (isLeft ? 'L' : 'R')) : '0';
        nodes[newId] = { val, left: null, right: null };
        if (!parentId) rootId = newId;
        else {
          if (isLeft) nodes[parentId].left = newId;
          else nodes[parentId].right = newId;
        }

        domPushState(seq, {
          kind: 'insert', line: 3, color: 'emerald',
          nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: newId,
          explTitle: 'Null Pointer Reached!',
          explText: `Found the empty spot! Inserted new node ${val} here.`,
          pause: true
        }, ctx);
        return newId;
      }

      domPushState(seq, {
        kind: 'visit', line: 5, color: 'blue',
        nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: nodeId,
        explTitle: `Visit Node ${nodes[nodeId].val}`,
        explText: `Compare ${val} with current node ${nodes[nodeId].val}.`
      }, ctx);

      if (val < nodes[nodeId].val) {
        domPushState(seq, {
          kind: 'go-left', line: 6, color: 'amber',
          nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: nodeId,
          explTitle: `Go Left`,
          explText: `${val} < ${nodes[nodeId].val}, so we must traverse the LEFT subtree.`
        }, ctx);
        dfs(nodes[nodeId].left, nodeId, true);
      } else {
        domPushState(seq, {
          kind: 'go-right', line: 8, color: 'amber',
          nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: nodeId,
          explTitle: `Go Right`,
          explText: `${val} >= ${nodes[nodeId].val}, so we must traverse the RIGHT subtree.`
        }, ctx);
        dfs(nodes[nodeId].right, nodeId, false);
      }
      return nodeId;
    }

    dfs(rootId, null, false);

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      nodes: JSON.parse(JSON.stringify(nodes)), rootId, val, curId: null,
      explTitle: 'Complete',
      explText: `Insertion complete. The tree structure is preserved.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    // A simplified text/flex-based tree rendering
    // For a real app, you'd use D3 or SVG, but we can do a clever flex layout
    
    function renderNode(id, level = 0) {
      if (!id) return '<div style="width:40px;height:40px;"></div>';
      const node = s.nodes[id];
      const isCur = s.curId === id;
      
      const nodeHtml = `
        <div style="
          width:40px;height:40px;border-radius:50%;
          display:flex;align-items:center;justify-content:center;
          background:${isCur ? 'var(--accent)' : 'var(--surface)'};
          color:${isCur ? 'var(--accent-ink)' : 'var(--text)'};
          border:2px solid ${isCur ? 'var(--accent)' : 'var(--border)'};
          font-weight:bold;z-index:2;position:relative;
          ${isCur ? 'box-shadow:0 0 15px var(--accent);transform:scale(1.1);' : ''}
          transition:all 0.3s;
        ">${node.val}</div>
      `;

      if (!node.left && !node.right) return `<div style="display:flex;flex-direction:column;align-items:center;">${nodeHtml}</div>`;

      return `
        <div style="display:flex;flex-direction:column;align-items:center;">
          ${nodeHtml}
          <div style="display:flex;width:100%;min-width:${120 / (level+1)}px;justify-content:space-between;margin-top:20px;position:relative;">
            <svg style="position:absolute;top:-20px;left:0;width:100%;height:20px;z-index:1;pointer-events:none;">
               ${node.left ? `<line x1="50%" y1="0" x2="25%" y2="20" stroke="var(--border)" stroke-width="2"/>` : ''}
               ${node.right ? `<line x1="50%" y1="0" x2="75%" y2="20" stroke="var(--border)" stroke-width="2"/>` : ''}
            </svg>
            <div style="flex:1;display:flex;justify-content:center;">${renderNode(node.left, level+1)}</div>
            <div style="flex:1;display:flex;justify-content:center;">${renderNode(node.right, level+1)}</div>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="glass-panel" style="padding:40px 20px;overflow-x:auto;">
         <div style="display:flex;justify-content:center;min-width:300px;">
            ${renderNode(s.rootId)}
         </div>
      </div>
      <div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:var(--surface);border:1px solid var(--border);text-align:center;">
        Value to insert: <b style="color:var(--accent);font-size:18px;">${s.val}</b>
      </div>
    `;
  }
});

/* ================================ 14 · Number of Islands (DOM) ============= */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Number of Islands', short: 'Number of Islands',
  idea: 'Scan the grid. When you find an unvisited land cell (<code>"1"</code>), increment the island count, then trigger a DFS/BFS to "sink" or mark all connected land cells as visited.',
  complexity: 'Time O(m * n) · Space O(m * n)',
  input: '11000, 11000, 00100, 00011', hint: 'comma-separated rows of 1s (land) and 0s (water)',
  code: [
    'def numIslands(grid):',
    '    if not grid: return 0',
    '    rows, cols = len(grid), len(grid[0])',
    '    islands = 0',
    '',
    '    def dfs(r, c):',
    '        if r < 0 or c < 0 or r == rows or c == cols or grid[r][c] == "0":',
    '            return',
    '        grid[r][c] = "0" # mark visited',
    '        dfs(r+1, c)',
    '        dfs(r-1, c)',
    '        dfs(r, c+1)',
    '        dfs(r, c-1)',
    '',
    '    for r in range(rows):',
    '        for c in range(cols):',
    '            if grid[r][c] == "1":',
    '                islands += 1',
    '                dfs(r, c)',
    '    return islands'
  ],
  parse(s) {
    const grid = s.split(',').map(r => r.trim().split(''));
    if (!grid.length || !grid[0].length) throw new Error('Enter a valid grid');
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    let islands = 0;
    
    // Deep copy for state tracking
    let curGrid = JSON.parse(JSON.stringify(grid));

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      grid: JSON.parse(JSON.stringify(curGrid)), r: -1, c: -1, islands, dfsR: -1, dfsC: -1,
      explTitle: 'Initialization',
      explText: `We have a ${rows}x${cols} grid. We will scan every cell looking for land ("1").`,
      pause: true
    }, ctx);

    function dfs(r, c) {
      if (r < 0 || c < 0 || r === rows || c === cols || curGrid[r][c] === "0") {
        return;
      }

      curGrid[r][c] = "0";
      
      domPushState(seq, {
        kind: 'dfs', line: 9, color: 'blue',
        grid: JSON.parse(JSON.stringify(curGrid)), r: -1, c: -1, islands, dfsR: r, dfsC: c,
        explTitle: 'DFS Sinking',
        explText: `Found land at (${r}, ${c}). Sinking it (marking as visited "0") so we don't count it twice.`
      }, ctx);

      dfs(r + 1, c);
      dfs(r - 1, c);
      dfs(r, c + 1);
      dfs(r, c - 1);
    }

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        domPushState(seq, {
          kind: 'scan', line: 17, color: 'default',
          grid: JSON.parse(JSON.stringify(curGrid)), r, c, islands, dfsR: -1, dfsC: -1,
          explTitle: 'Scanning Grid',
          explText: `Checking cell (${r}, ${c}). It is ${curGrid[r][c] === "1" ? 'land!' : 'water.'}`
        }, ctx);

        if (curGrid[r][c] === "1") {
          islands += 1;
          domPushState(seq, {
            kind: 'found', line: 18, color: 'emerald',
            grid: JSON.parse(JSON.stringify(curGrid)), r, c, islands, dfsR: -1, dfsC: -1,
            explTitle: 'Found an Island!',
            explText: `Found unvisited land! Increment island count to ${islands} and launch DFS to sink the entire island.`,
            pause: true
          }, ctx);
          dfs(r, c);
        }
      }
    }

    domPushState(seq, {
      kind: 'done', line: 20, color: 'emerald',
      grid: JSON.parse(JSON.stringify(curGrid)), r: -1, c: -1, islands, dfsR: -1, dfsC: -1,
      explTitle: 'Complete',
      explText: `Scanned the entire grid. Total islands found: ${islands}.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    let gridHTML = '';
    const rows = s.grid.length;
    const cols = s.grid[0].length;
    
    for (let r = 0; r < rows; r++) {
      gridHTML += `<div style="display:flex;">`;
      for (let c = 0; c < cols; c++) {
        const val = s.grid[r][c];
        const isLand = val === "1";
        
        let bg = isLand ? '#34d399' : 'color-mix(in srgb, #38bdf8 15%, transparent)';
        let border = isLand ? '#10b981' : 'color-mix(in srgb, #38bdf8 30%, transparent)';
        let content = isLand ? '🏝️' : '🌊';
        let opacity = 1;
        let scale = 1;
        let z = 1;
        let shadow = '';

        if (s.r === r && s.c === c) {
          border = '#fbbf24';
          bg = 'color-mix(in srgb, #fbbf24 30%, transparent)';
          scale = 1.1;
          z = 10;
          shadow = 'box-shadow:0 0 15px #fbbf24;';
        } else if (s.dfsR === r && s.dfsC === c) {
          border = '#f43f5e';
          bg = 'color-mix(in srgb, #f43f5e 30%, transparent)';
          content = '🔥'; // "sinking"
          scale = 1.2;
          z = 10;
          shadow = 'box-shadow:0 0 15px #f43f5e;';
        } else if (!isLand) {
          opacity = 0.5;
        }

        gridHTML += `
          <div style="
            width:40px;height:40px;margin:2px;border-radius:4px;
            display:flex;align-items:center;justify-content:center;
            background:${bg};border:2px solid ${border};
            font-size:20px;opacity:${opacity};
            transform:scale(${scale});z-index:${z};${shadow}
            transition:all 0.2s;
          ">${content}</div>`;
      }
      gridHTML += `</div>`;
    }

    container.innerHTML = `
      <div style="display:flex;gap:20px;align-items:flex-start;">
        <div class="glass-panel" style="padding:12px;display:flex;flex-direction:column;">
          ${gridHTML}
        </div>
        <div class="glass-panel" style="flex:1;min-height:100px;">
          <div class="panel-heading" style="color:#34d399;">Islands Found</div>
          <div style="font-size:48px;font-weight:bold;color:var(--accent);text-align:center;margin-top:10px;">
             ${s.islands}
          </div>
        </div>
      </div>`;
  }
});

/* ================================ 14 · Course Schedule (DOM) =============== */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Course Schedule', short: 'Course Schedule',
  idea: 'Use Kahn\'s Algorithm (Topological Sort). Count the <b>in-degree</b> (prerequisites) of each course. Put courses with 0 in-degree into a queue. Process them by unlocking their neighbors (decreasing their in-degree). If we process all courses, it\'s possible!',
  complexity: 'Time O(V + E) · Space O(V + E)',
  input: '4 ; 1,0 ; 2,1 ; 3,1 ; 3,2', hint: 'numCourses ; u,v edges (u depends on v)',
  code: [
    'def canFinish(numCourses, prerequisites):',
    '    adj = {i: [] for i in range(numCourses)}',
    '    indegree = [0] * numCourses',
    '    for crs, pre in prerequisites:',
    '        adj[pre].append(crs)',
    '        indegree[crs] += 1',
    '',
    '    q = deque([i for i in range(numCourses) if indegree[i] == 0])',
    '    count = 0',
    '',
    '    while q:',
    '        curr = q.popleft()',
    '        count += 1',
    '        for nei in adj[curr]:',
    '            indegree[nei] -= 1',
    '            if indegree[nei] == 0:',
    '                q.append(nei)',
    '',
    '    return count == numCourses'
  ],
  parse(s) {
    const parts = s.split(';');
    const n = Math.max(1, parseInt(parts[0].trim()) || 0);
    const edges = parts.slice(1).map(x => {
      const p = x.split(',').map(n => parseInt(n.trim()));
      return p;
    });
    return { n, edges };
  },
  buildStates({ n, edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const adj = Array.from({length: n}, () => []);
    const indegree = Array(n).fill(0);
    
    for (const [u, v] of edges) {
      if (u >= 0 && u < n && v >= 0 && v < n) {
        adj[v].push(u); // u depends on v -> edge v to u
        indegree[u]++;
      }
    }

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      n, adj, indegree: [...indegree], q: [], processed: [], curr: -1, nei: -1,
      explTitle: 'Build Graph',
      explText: `Built adjacency list and calculated in-degrees (number of prerequisites) for each course.`,
      pause: true
    }, ctx);

    const q = [];
    for (let i = 0; i < n; i++) {
      if (indegree[i] === 0) q.push(i);
    }

    domPushState(seq, {
      kind: 'queue-init', line: 8, color: 'blue',
      n, adj, indegree: [...indegree], q: [...q], processed: [], curr: -1, nei: -1,
      explTitle: 'Initialize Queue',
      explText: `Found courses with 0 prerequisites: [${q.join(', ')}]. Added them to the queue to process first.`,
      pause: true
    }, ctx);

    const processed = [];

    while (q.length > 0) {
      const curr = q.shift();
      processed.push(curr);
      
      domPushState(seq, {
        kind: 'pop', line: 12, color: 'amber',
        n, adj, indegree: [...indegree], q: [...q], processed: [...processed], curr, nei: -1,
        explTitle: `Process Course ${curr}`,
        explText: `Take course ${curr}. Now we can unlock courses that depend on it.`
      }, ctx);

      for (const nei of adj[curr]) {
        indegree[nei]--;
        
        domPushState(seq, {
          kind: 'unlock', line: 15, color: 'default',
          n, adj, indegree: [...indegree], q: [...q], processed: [...processed], curr, nei,
          explTitle: `Unlock Neighbor ${nei}`,
          explText: `Decremented in-degree of course ${nei} to ${indegree[nei]}.`
        }, ctx);

        if (indegree[nei] === 0) {
          q.push(nei);
          domPushState(seq, {
            kind: 'enqueue', line: 17, color: 'emerald',
            n, adj, indegree: [...indegree], q: [...q], processed: [...processed], curr, nei,
            explTitle: `Course ${nei} Ready!`,
            explText: `Course ${nei} now has 0 prerequisites. Add it to the queue!`
          }, ctx);
        }
      }
    }

    const success = processed.length === n;
    domPushState(seq, {
      kind: 'done', line: 19, color: success ? 'emerald' : 'red',
      n, adj, indegree: [...indegree], q: [...q], processed: [...processed], curr: -1, nei: -1,
      explTitle: success ? 'Success!' : 'Cycle Detected!',
      explText: success ? `Processed all ${n} courses!` : `Only processed ${processed.length}/${n} courses. There is a cycle!`
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    // We'll render courses as cards
    const courseCards = Array.from({length: s.n}).map((_, i) => {
      const inD = s.indegree[i];
      const isProcessed = s.processed.includes(i);
      const isQueue = s.q.includes(i);
      const isCur = s.curr === i;
      const isNei = s.nei === i;

      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let status = '';

      if (isProcessed) {
        bg = 'rgba(52, 211, 153, 0.1)';
        border = '#34d399';
        status = '✅ Done';
      } else if (isCur) {
        bg = 'rgba(251, 191, 36, 0.15)';
        border = '#fbbf24';
        status = '⏳ Active';
      } else if (isNei) {
        bg = 'rgba(56, 189, 248, 0.15)';
        border = '#38bdf8';
        status = '🔍 Check';
      } else if (isQueue) {
        status = '📝 Ready';
      } else {
        status = `🔒 Blocked (${inD})`;
      }

      return `
        <div style="
          padding:10px 16px;border-radius:8px;border:2px solid ${border};background:${bg};
          display:flex;flex-direction:column;align-items:center;min-width:80px;
          ${isCur ? 'transform:scale(1.1);box-shadow:0 0 15px rgba(251,191,36,0.3);z-index:2;' : ''}
          transition:all 0.3s;
        ">
          <div style="font-size:24px;font-weight:bold;margin-bottom:4px;">${i}</div>
          <div style="font-size:11px;font-family:var(--mono);color:var(--text-dim);">${status}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="glass-panel" style="padding:20px;display:flex;flex-wrap:wrap;gap:16px;justify-content:center;">
        ${courseCards}
      </div>
      <div style="display:flex;gap:12px;margin-top:16px;">
        <div class="glass-panel" style="flex:1;">
          <div class="panel-heading" style="color:var(--accent);">Queue</div>
          <div style="font-family:var(--mono);font-size:16px;">
             ${s.q.length === 0 ? '<span style="color:var(--text-dim);">empty</span>' : `[ ${s.q.join(', ')} ]`}
          </div>
        </div>
        <div class="glass-panel" style="flex:1;">
          <div class="panel-heading" style="color:#34d399;">Processed</div>
          <div style="font-family:var(--mono);font-size:16px;">
             ${s.processed.length} / ${s.n}
          </div>
        </div>
      </div>
    `;
  }
});/* ================================ 09 · N-Queens (DOM) ======================= */
defineAlgoDom('09_recursion_backtracking', {
  type: 'dom',
  title: 'N-Queens', short: 'N-Queens',
  idea: 'Place queens row by row. We use sets to track which columns and diagonals are under attack. If a cell is safe, place the queen and recurse. If we hit a dead end, we <b>backtrack</b> by removing the queen and trying the next column.',
  complexity: 'Time O(N!) · Space O(N)',
  input: '4', hint: 'board size N (try 4 to 6)',
  code: [
    'def solveNQueens(n):',
    '    cols = set()',
    '    posDiag = set() # r - c',
    '    negDiag = set() # r + c',
    '    ans = []',
    '    board = [["."] * n for _ in range(n)]',
    '',
    '    def backtrack(r):',
    '        if r == n:',
    '            ans.append(["".join(row) for row in board])',
    '            return',
    '',
    '        for c in range(n):',
    '            if c in cols or (r - c) in posDiag or (r + c) in negDiag:',
    '                continue',
    '',
    '            # Place queen',
    '            cols.add(c); posDiag.add(r - c); negDiag.add(r + c)',
    '            board[r][c] = "Q"',
    '            backtrack(r + 1)',
    '            # Remove queen (backtrack)',
    '            cols.remove(c); posDiag.remove(r - c); negDiag.remove(r + c)',
    '            board[r][c] = "."',
    '',
    '    backtrack(0)',
    '    return ans',
  ],
  parse(s) {
    const n = Math.min(Math.max(avNum(s, 'n') || 4, 1), 6);
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const ans = [];
    const cols = new Set(), posDiag = new Set(), negDiag = new Set();
    const queens = []; // stores {r, c}

    domPushState(seq, {
      kind: 'init', line: 6, color: 'default',
      n, r: 0, c: 0, queens: [], ans: 0, conflict: null,
      explTitle: 'Initialization',
      explText: `Create an empty ${n}x${n} board. We'll track columns and diagonals to detect attacks in O(1) time.`,
      pause: true
    }, ctx);

    function backtrack(r) {
      if (r === n) {
        ans.push([...queens]);
        domPushState(seq, {
          kind: 'base-case', line: 9, color: 'emerald',
          n, r, c: -1, queens: [...queens], ans: ans.length, conflict: null,
          explTitle: 'Valid Solution!',
          explText: `We reached row ${n}, which means all queens are placed safely! Saved solution.`,
          pause: true
        }, ctx);
        return;
      }

      for (let c = 0; c < n; c++) {
        const pd = r - c, nd = r + c;
        const underAttack = cols.has(c) || posDiag.has(pd) || negDiag.has(nd);
        
        domPushState(seq, {
          kind: 'try', line: 14, color: underAttack ? 'red' : 'default',
          n, r, c, queens: [...queens], ans: ans.length, conflict: underAttack ? {c, pd, nd} : null,
          explTitle: `Try Row ${r}, Col ${c}`,
          explText: underAttack ? 'Under attack! Skip this cell.' : 'Safe cell found! We can place a queen here.'
        }, ctx);

        if (underAttack) continue;

        cols.add(c); posDiag.add(pd); negDiag.add(nd);
        queens.push({r, c});
        
        domPushState(seq, {
          kind: 'place', line: 18, color: 'emerald',
          n, r, c, queens: [...queens], ans: ans.length, conflict: null,
          explTitle: 'Place Queen',
          explText: `Placed 👑 at (${r}, ${c}). Moving to row ${r + 1}.`
        }, ctx);

        backtrack(r + 1);

        cols.delete(c); posDiag.delete(pd); negDiag.delete(nd);
        queens.pop();

        domPushState(seq, {
          kind: 'backtrack', line: 22, color: 'amber',
          n, r, c, queens: [...queens], ans: ans.length, conflict: null,
          explTitle: 'Backtrack',
          explText: `Backtracking from row ${r+1}. Removed 👑 at (${r}, ${c}) to try the next column.`
        }, ctx);
      }
    }

    backtrack(0);

    domPushState(seq, {
      kind: 'done', line: 26, color: 'emerald',
      n, r: n, c: -1, queens: [], ans: ans.length, conflict: null,
      explTitle: 'Complete',
      explText: `Explored all possibilities. Found ${ans.length} solutions for N=${n}.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    // Generate an NxN grid
    let gridHTML = '';
    
    for (let r = 0; r < s.n; r++) {
      gridHTML += `<div style="display:flex;width:100%;">`;
      for (let c = 0; c < s.n; c++) {
        const isDark = (r + c) % 2 === 1;
        const bg = isDark ? 'color-mix(in srgb, var(--surface) 80%, black)' : 'var(--surface)';
        
        let content = '';
        let cellStyle = `width:${100/s.n}%;aspect-ratio:1;display:flex;align-items:center;justify-content:center;background:${bg};font-size:32px;transition:all 0.2s;position:relative;`;
        
        // Find if there's a queen here
        const hasQueen = s.queens.some(q => q.r === r && q.c === c);
        
        if (hasQueen) {
          content = '👑';
        }
        
        // Highlight logic
        if (s.r === r && s.c === c && !hasQueen) {
           if (s.conflict) {
             cellStyle += `background:rgba(239,68,68,0.3);box-shadow:inset 0 0 0 3px #ef4444;`;
             content = '❌';
           } else {
             cellStyle += `background:rgba(52,211,153,0.3);box-shadow:inset 0 0 0 3px #34d399;`;
             content = '✅';
           }
        }
        
        // Visualize attack lines if conflict
        if (s.conflict && !hasQueen && (r !== s.r || c !== s.c)) {
          // If this cell is causing the conflict (another queen is attacking)
          const attackingQueen = s.queens.find(q => 
            q.c === s.c || 
            (q.r - q.c) === s.conflict.pd || 
            (q.r + q.c) === s.conflict.nd
          );
          
          if (attackingQueen) {
             // Highlight attack path
             if (c === s.c || (r - c) === s.conflict.pd || (r + c) === s.conflict.nd) {
                cellStyle += `background:rgba(239,68,68,0.15);`;
             }
             if (attackingQueen.r === r && attackingQueen.c === c) {
                cellStyle += `box-shadow:0 0 15px #ef4444;background:rgba(239,68,68,0.4);z-index:10;`;
             }
          }
        }

        gridHTML += `<div style="${cellStyle}">${content}</div>`;
      }
      gridHTML += `</div>`;
    }

    container.innerHTML = `
      <div style="display:flex;gap:20px;align-items:flex-start;">
        <div class="glass-panel" style="flex:1;max-width:400px;padding:12px;display:flex;flex-direction:column;gap:0;">
           <div style="border:2px solid var(--border);border-radius:4px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,0.2);">
              ${gridHTML}
           </div>
        </div>
        <div class="glass-panel" style="flex:1;min-height:150px;">
          <div class="panel-heading" style="color:#34d399;">Solutions Found: ${s.ans}</div>
          <div style="color:var(--text-dim);font-size:13px;line-height:1.6;margin-top:10px;">
             Rows placed: <b>${s.queens.length} / ${s.n}</b><br/>
             Current checking row: <b>${s.r < s.n ? s.r : '-'}</b>
          </div>
        </div>
      </div>`;
  }
});

/* ================================ 01 · Contains Duplicate (DOM) ============ */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Contains Duplicate', short: 'Contains Dup',
  idea: 'We use a <b>Hash Set</b>. As we iterate through the array, we check if the element is already in the set. If it is, we found a duplicate! Otherwise, we add it to the set.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 2, 3, 1', hint: 'comma-separated array of numbers',
  code: [
    'def containsDuplicate(nums):',
    '    hashset = set()',
    '',
    '    for n in nums:',
    '        if n in hashset:',
    '            return True',
    '        hashset.add(n)',
    '',
    '    return False'
  ],
  parse(s) {
    return { nums: avArr(s) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const hashset = new Set();
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, hashset: Array.from(hashset), curr: -1, found: false,
      explTitle: 'Initialization',
      explText: 'Initialize an empty Hash Set.'
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        nums, hashset: Array.from(hashset), curr: i, found: false,
        explTitle: `Check ${nums[i]}`,
        explText: `Check if ${nums[i]} is already in our Hash Set.`
      }, ctx);

      if (hashset.has(nums[i])) {
        domPushState(seq, {
          kind: 'found', line: 6, color: 'red',
          nums, hashset: Array.from(hashset), curr: i, found: true,
          explTitle: `Duplicate Found!`,
          explText: `${nums[i]} is already in the set. We return True.`
        }, ctx);
        return seq;
      }

      hashset.add(nums[i]);
      domPushState(seq, {
        kind: 'add', line: 7, color: 'emerald',
        nums, hashset: Array.from(hashset), curr: i, found: false,
        explTitle: `Add ${nums[i]}`,
        explText: `Not found. We add ${nums[i]} to the Hash Set.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 9, color: 'emerald',
      nums, hashset: Array.from(hashset), curr: -1, found: false,
      explTitle: `Complete`,
      explText: `We checked all elements. No duplicates found. We return False.`
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    // Array layout
    const arrHTML = s.nums.map((v, i) => {
      const isCur = i === s.curr;
      const isFound = isCur && s.found;
      let bg = isFound ? 'rgba(244,63,94,0.2)' : isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isFound ? '#f43f5e' : isCur ? '#38bdf8' : 'var(--border)';
      return `
        <div style="
          width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;
          background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size: 18px;
          ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 15px ' + border + ';' : ''}
          transition: all 0.3s;
        ">${v}</div>
      `;
    }).join('');

    // Set layout
    const setHTML = s.hashset.length === 0 
      ? '<div style="color:var(--text-dim); font-style:italic;">Empty Set</div>'
      : s.hashset.map(v => {
          const isTarget = s.curr !== -1 && s.nums[s.curr] === v && s.found;
          return `
            <div style="
              padding: 8px 16px; border-radius: 20px; 
              background: ${isTarget ? '#f43f5e' : 'var(--accent)'};
              color: ${isTarget ? '#fff' : 'var(--accent-ink)'};
              font-weight: bold;
              ${isTarget ? 'box-shadow: 0 0 15px #f43f5e; transform: scale(1.1);' : ''}
              transition: all 0.3s;
            ">${v}</div>
          `;
        }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Input Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${arrHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height:120px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Hash Set</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; align-items:center;">
            ${setHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Valid Anagram (DOM) ================= */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Valid Anagram', short: 'Valid Anagram',
  idea: 'Count the frequency of each character in both strings. We can use one hash map (or array): increment for chars in <code>s</code>, decrement for chars in <code>t</code>. If all counts end up at 0, they are anagrams.',
  complexity: 'Time O(S + T) · Space O(1) (since English alphabet is fixed to 26 chars)',
  input: 'anagram ; nagaram', hint: 'string s ; string t',
  code: [
    'def isAnagram(s, t):',
    '    if len(s) != len(t):',
    '        return False',
    '',
    '    count = {}',
    '    for i in range(len(s)):',
    '        count[s[i]] = count.get(s[i], 0) + 1',
    '        count[t[i]] = count.get(t[i], 0) - 1',
    '',
    '    for c in count:',
    '        if count[c] != 0:',
    '            return False',
    '',
    '    return True'
  ],
  parse(str) {
    const parts = str.split(';');
    return { s: parts[0]?.trim() || '', t: parts[1]?.trim() || '' };
  },
  buildStates({ s, t }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const count = {};

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, t, count: {...count}, i: -1, phase: 'check_len',
      explTitle: 'Check Length',
      explText: `s is length ${s.length}, t is length ${t.length}.`
    }, ctx);

    if (s.length !== t.length) {
      domPushState(seq, {
        kind: 'done', line: 3, color: 'red',
        s, t, count: {...count}, i: -1, phase: 'done',
        explTitle: 'Lengths Differ',
        explText: 'Strings have different lengths, cannot be anagrams. Return False.'
      }, ctx);
      return seq;
    }

    for (let i = 0; i < s.length; i++) {
      count[s[i]] = (count[s[i]] || 0) + 1;
      
      domPushState(seq, {
        kind: 'inc', line: 7, color: 'blue',
        s, t, count: {...count}, i, phase: 'count', charS: s[i], charT: null,
        explTitle: `Process s[${i}]`,
        explText: `Increment count for '${s[i]}'.`
      }, ctx);

      count[t[i]] = (count[t[i]] || 0) - 1;

      domPushState(seq, {
        kind: 'dec', line: 8, color: 'amber',
        s, t, count: {...count}, i, phase: 'count', charS: s[i], charT: t[i],
        explTitle: `Process t[${i}]`,
        explText: `Decrement count for '${t[i]}'.`
      }, ctx);
    }

    for (const char of Object.keys(count)) {
      domPushState(seq, {
        kind: 'check', line: 11, color: 'blue',
        s, t, count: {...count}, i: -1, phase: 'verify', checkChar: char,
        explTitle: `Verify '${char}'`,
        explText: `Check if count for '${char}' is 0.`
      }, ctx);

      if (count[char] !== 0) {
        domPushState(seq, {
          kind: 'invalid', line: 12, color: 'red',
          s, t, count: {...count}, i: -1, phase: 'done', checkChar: char,
          explTitle: `Invalid Count`,
          explText: `Count for '${char}' is not 0. Return False.`
        }, ctx);
        return seq;
      }
    }

    domPushState(seq, {
      kind: 'valid', line: 14, color: 'emerald',
      s, t, count: {...count}, i: -1, phase: 'done',
      explTitle: `Valid Anagram`,
      explText: `All character counts are exactly 0. It is a valid anagram! Return True.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const renderStr = (str, isS) => {
      return str.split('').map((c, idx) => {
        const isCur = state.i === idx;
        const color = isCur ? (isS ? '#38bdf8' : '#fbbf24') : 'var(--text)';
        const bg = isCur ? (isS ? 'rgba(56,189,248,0.2)' : 'rgba(251,191,36,0.2)') : 'var(--surface)';
        const border = isCur ? (isS ? '#38bdf8' : '#fbbf24') : 'var(--border)';
        return `
          <div style="
            width:35px; height:35px; display:flex; align-items:center; justify-content:center;
            border:1px solid ${border}; background:${bg}; color:${color}; font-weight:bold; font-size:18px;
            ${isCur ? 'transform:scale(1.1); box-shadow:0 0 10px ' + border + '; z-index:2;' : ''}
            transition: all 0.3s;
          ">${c}</div>
        `;
      }).join('');
    };

    const countHTML = Object.entries(state.count).map(([char, cnt]) => {
      const isChecking = state.phase === 'verify' && state.checkChar === char;
      const isZero = cnt === 0;
      let border = 'var(--border)';
      let bg = 'var(--surface)';
      let textCol = 'var(--text)';
      
      if (isChecking) {
        border = isZero ? '#34d399' : '#f43f5e';
        bg = isZero ? 'rgba(52,211,153,0.2)' : 'rgba(244,63,94,0.2)';
        textCol = border;
      } else if (cnt > 0) {
        textCol = '#38bdf8';
      } else if (cnt < 0) {
        textCol = '#fbbf24';
      }

      return `
        <div style="
          display:flex; flex-direction:column; align-items:center; border: 1px solid ${border}; 
          border-radius: 8px; overflow: hidden; background: ${bg};
          ${isChecking ? 'transform:scale(1.1); box-shadow:0 0 10px ' + border + ';' : ''}
          transition: all 0.3s;
        ">
          <div style="background:var(--surface); padding: 4px 12px; font-weight:bold; border-bottom: 1px solid var(--border);">${char}</div>
          <div style="padding: 8px 12px; font-family:var(--mono); font-weight:bold; color: ${textCol};">${cnt}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div style="display:flex; gap: 40px; width:100%; justify-content:center;">
          <div class="glass-panel" style="padding: 15px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="color: #38bdf8; margin-bottom: 10px;">String s (+1)</div>
            <div style="display:flex; gap:4px;">${renderStr(state.s, true)}</div>
          </div>
          <div class="glass-panel" style="padding: 15px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="color: #fbbf24; margin-bottom: 10px;">String t (-1)</div>
            <div style="display:flex; gap:4px;">${renderStr(state.t, false)}</div>
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height: 120px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Character Frequencies</div>
          <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
            ${Object.keys(state.count).length === 0 ? '<div style="color:var(--text-dim);font-style:italic;">Empty Hash Map</div>' : countHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Two Sum (DOM) ======================= */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Two Sum with a hash map', short: 'Two Sum',
  idea: 'Use a Hash Map to store <code>{ value: index }</code>. For each number, we calculate the <code>diff = target - num</code>. If <code>diff</code> is already in our map, we found the pair!',
  complexity: 'Time O(N) · Space O(N)',
  input: '2, 7, 11, 15 ; 9', hint: 'comma-separated array ; target sum',
  code: [
    'def twoSum(nums, target):',
    '    prevMap = {} # val : index',
    '',
    '    for i, n in enumerate(nums):',
    '        diff = target - n',
    '        if diff in prevMap:',
    '            return [prevMap[diff], i]',
    '        prevMap[n] = i',
    '    return'
  ],
  parse(str) {
    const [arrStr, targetStr] = avParts(str);
    return { nums: avArr(arrStr), target: avNum(targetStr) };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const prevMap = {};

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, prevMap: {...prevMap}, i: -1, diff: null, foundIdx: -1,
      explTitle: 'Initialization',
      explText: `Target sum is ${target}. Initialize an empty hash map.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      const n = nums[i];
      const diff = target - n;

      domPushState(seq, {
        kind: 'visit', line: 5, color: 'blue',
        nums, target, prevMap: {...prevMap}, i, diff, foundIdx: -1,
        explTitle: `Check ${n}`,
        explText: `We need ${target} - ${n} = ${diff}. Is ${diff} in our map?`
      }, ctx);

      if (diff in prevMap) {
        domPushState(seq, {
          kind: 'found', line: 7, color: 'emerald',
          nums, target, prevMap: {...prevMap}, i, diff, foundIdx: prevMap[diff],
          explTitle: `Match Found!`,
          explText: `Found ${diff} at index ${prevMap[diff]}! We return [${prevMap[diff]}, ${i}].`
        }, ctx);
        return seq;
      }

      prevMap[n] = i;
      domPushState(seq, {
        kind: 'add', line: 8, color: 'amber',
        nums, target, prevMap: {...prevMap}, i, diff, foundIdx: -1,
        explTitle: `Store in Map`,
        explText: `${diff} not found. Store { ${n}: ${i} } in the map for future checks.`
      }, ctx);
    }

    return seq;
  },
  renderDOM(container, state) {
    // Array
    const arrHTML = state.nums.map((v, i) => {
      const isCur = i === state.i;
      const isFound = i === state.foundIdx || (state.foundIdx !== -1 && i === state.i);
      let bg = isFound ? 'rgba(52,211,153,0.2)' : isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isFound ? '#34d399' : isCur ? '#38bdf8' : 'var(--border)';
      return `
        <div style="
          width: 50px; height: 50px; display: flex; flex-direction:column; align-items: center; justify-content: center;
          background: ${bg}; border: 2px solid ${border}; border-radius: 8px;
          ${isCur || isFound ? 'transform: scale(1.1); box-shadow: 0 0 15px ' + border + ';' : ''}
          transition: all 0.3s;
        ">
          <span style="font-size: 11px; color: var(--text-dim); margin-bottom:-4px;">[${i}]</span>
          <span style="font-weight: bold; font-size: 16px;">${v}</span>
        </div>
      `;
    }).join('');

    // Map
    const mapEntriesHTML = Object.keys(state.prevMap).length === 0 
      ? '<div style="color:var(--text-dim);font-style:italic;">Empty Hash Map</div>' 
      : Object.entries(state.prevMap).map(([val, idx]) => {
          const isTarget = parseInt(val) === state.diff && state.foundIdx !== -1;
          const bg = isTarget ? '#34d399' : 'var(--surface)';
          const color = isTarget ? '#000' : 'var(--text)';
          const border = isTarget ? '#34d399' : 'var(--border)';
          return `
            <div style="
              display:flex; border: 1px solid ${border}; border-radius: 6px; overflow: hidden;
              background:${bg}; color:${color}; font-family: var(--mono);
              ${isTarget ? 'transform: scale(1.1); box-shadow: 0 0 15px #34d399; font-weight:bold;' : ''}
              transition: all 0.3s;
            ">
              <div style="padding: 6px 10px; border-right: 1px solid ${border};">Val: ${val}</div>
              <div style="padding: 6px 10px; background: rgba(0,0,0,0.1);">Idx: ${idx}</div>
            </div>
          `;
        }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        
        <div style="display:flex; width:100%; gap:20px;">
          <div class="glass-panel" style="flex: 2; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Input Array (Target: ${state.target})</div>
            <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
              ${arrHTML}
            </div>
          </div>
          
          ${state.diff !== null ? `
          <div class="glass-panel" style="flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content:center; background: rgba(56,189,248,0.1); border-color: #38bdf8;">
            <div style="font-size: 14px; color: var(--text-dim);">Looking for Difference</div>
            <div style="font-size: 24px; font-weight: bold; color: #38bdf8; margin-top:8px;">
              ${state.target} - ${state.nums[state.i]} = <span style="color:#fbbf24">${state.diff}</span>
            </div>
          </div>
          ` : ''}
        </div>

        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height: 120px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">prevMap { Value : Index }</div>
          <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
            ${mapEntriesHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Group Anagrams (DOM) ================ */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Group Anagrams', short: 'Group Anagrams',
  idea: 'We can group anagrams together by using a <b>Hash Map</b>. The key is a character count tuple (or a sorted version of the string), and the value is the list of anagrams that match that key.',
  complexity: 'Time O(m * n) · Space O(m * n) (where m is number of strings, n is max string length)',
  input: 'eat, tea, tan, ate, nat, bat', hint: 'comma-separated strings',
  code: [
    'def groupAnagrams(strs):',
    '    res = defaultdict(list)',
    '',
    '    for s in strs:',
    '        count = [0] * 26',
    '        for c in s:',
    '            count[ord(c) - ord("a")] += 1',
    '',
    '        res[tuple(count)].append(s)',
    '',
    '    return res.values()'
  ],
  parse(str) {
    return { strs: str.split(',').map(s => s.trim()) };
  },
  buildStates({ strs }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const res = {}; // key -> array of strings

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      strs, res: JSON.parse(JSON.stringify(res)), curr: -1, currKey: null,
      explTitle: 'Initialization',
      explText: `Create an empty Hash Map where the key will be the character count signature.`
    }, ctx);

    for (let i = 0; i < strs.length; i++) {
      const s = strs[i];
      const count = Array(26).fill(0);
      for (const c of s) {
        count[c.charCodeAt(0) - 97]++;
      }
      // Compress the key for display purposes (e.g. 1a1e1t)
      let key = '';
      for (let j = 0; j < 26; j++) {
        if (count[j] > 0) key += `${count[j]}${String.fromCharCode(97 + j)}`;
      }

      domPushState(seq, {
        kind: 'count', line: 5, color: 'blue',
        strs, res: JSON.parse(JSON.stringify(res)), curr: i, currKey: key,
        explTitle: `Process "${s}"`,
        explText: `Count characters in "${s}". The unique signature is [${key}].`
      }, ctx);

      if (!res[key]) res[key] = [];
      res[key].push(s);

      domPushState(seq, {
        kind: 'group', line: 9, color: 'emerald',
        strs, res: JSON.parse(JSON.stringify(res)), curr: i, currKey: key,
        explTitle: `Group by Signature`,
        explText: `Append "${s}" to the list for signature [${key}].`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      strs, res: JSON.parse(JSON.stringify(res)), curr: -1, currKey: null,
      explTitle: `Complete`,
      explText: `All strings are grouped! Return the values of the hash map.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    // Array
    const arrHTML = state.strs.map((v, i) => {
      const isCur = i === state.curr;
      const bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      const border = isCur ? '#38bdf8' : 'var(--border)';
      return `
        <div style="
          padding: 8px 16px; display: flex; align-items: center; justify-content: center;
          background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-weight: bold;
          ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + ';' : ''}
          transition: all 0.3s;
        ">"${v}"</div>
      `;
    }).join('');

    // Map
    const mapEntriesHTML = Object.keys(state.res).length === 0 
      ? '<div style="color:var(--text-dim);font-style:italic;">Empty Map</div>' 
      : Object.entries(state.res).map(([key, list]) => {
          const isTarget = key === state.currKey;
          const bg = isTarget ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
          const border = isTarget ? '#34d399' : 'var(--border)';
          
          const listHtml = list.map(s => `<span style="background:var(--bg); padding:2px 8px; border-radius:4px; margin:2px;">"${s}"</span>`).join('');

          return `
            <div style="
              display:flex; flex-direction:column; border: 1px solid ${border}; border-radius: 8px; overflow: hidden;
              background:${bg}; 
              ${isTarget ? 'box-shadow: 0 0 10px #34d399; transform:scale(1.05);' : ''}
              transition: all 0.3s; width: 100%; max-width: 300px;
            ">
              <div style="padding: 6px 12px; background: rgba(0,0,0,0.2); border-bottom: 1px solid ${border}; font-family: var(--mono); color: #34d399; font-weight:bold;">
                Key: [${key}]
              </div>
              <div style="padding: 10px; display:flex; flex-wrap:wrap; gap:4px;">
                ${listHtml}
              </div>
            </div>
          `;
        }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Input Strings</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${arrHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height: 150px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Groups Hash Map</div>
          <div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; width:100%;">
            ${mapEntriesHTML}
          </div>
        </div>

      </div>
    `;
  }
});

/* ================================ 01 · Top K Frequent Elements (DOM) ======= */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Top K Frequent Elements', short: 'Top K Freq',
  idea: 'Count frequencies in a Hash Map, then use <b>Bucket Sort</b>. The bucket index is the frequency, and the bucket contents are elements with that frequency. Scan buckets from right to left to get the top K elements.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 1, 1, 2, 2, 3 ; 2', hint: 'comma-separated array ; K',
  code: [
    'def topKFrequent(nums, k):',
    '    count = {}',
    '    freq = [[] for i in range(len(nums) + 1)]',
    '',
    '    for n in nums:',
    '        count[n] = 1 + count.get(n, 0)',
    '    for n, c in count.items():',
    '        freq[c].append(n)',
    '',
    '    res = []',
    '    for i in range(len(freq) - 1, 0, -1):',
    '        for n in freq[i]:',
    '            res.append(n)',
    '            if len(res) == k:',
    '                return res'
  ],
  parse(str) {
    const [arrStr, kStr] = avParts(str);
    return { nums: avArr(arrStr), k: avNum(kStr) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const count = {};
    const freq = Array.from({length: nums.length + 1}, () => []);
    const res = [];

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res], 
      currNum: null, currFreq: null, phase: 'count',
      explTitle: 'Initialization',
      explText: `Target is top ${k} frequent elements. Initialize a frequency Hash Map and Bucket Array.`
    }, ctx);

    // Step 1: Count
    for (let i = 0; i < nums.length; i++) {
      const n = nums[i];
      count[n] = (count[n] || 0) + 1;
      
      domPushState(seq, {
        kind: 'count', line: 6, color: 'blue',
        nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
        currNum: n, currFreq: null, phase: 'count', i,
        explTitle: `Count Frequencies`,
        explText: `Increment count for ${n}. It is now ${count[n]}.`
      }, ctx);
    }

    // Step 2: Bucket Sort
    domPushState(seq, {
      kind: 'bucket_init', line: 7, color: 'default',
      nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
      currNum: null, currFreq: null, phase: 'bucket',
      explTitle: `Populate Buckets`,
      explText: `Move Hash Map entries into the bucket array where index = frequency.`
    }, ctx);

    for (const [nStr, c] of Object.entries(count)) {
      const n = parseInt(nStr);
      freq[c].push(n);

      domPushState(seq, {
        kind: 'bucket', line: 8, color: 'amber',
        nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
        currNum: n, currFreq: c, phase: 'bucket',
        explTitle: `Bucket Insert`,
        explText: `Element ${n} has frequency ${c}. Append to bucket ${c}.`
      }, ctx);
    }

    // Step 3: Gather Res
    domPushState(seq, {
      kind: 'gather_init', line: 11, color: 'default',
      nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
      currNum: null, currFreq: null, phase: 'gather', bucketIdx: -1,
      explTitle: `Gather Results`,
      explText: `Scan buckets from right to left (highest frequency first).`
    }, ctx);

    for (let i = freq.length - 1; i > 0; i--) {
      domPushState(seq, {
        kind: 'gather_scan', line: 11, color: 'blue',
        nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
        currNum: null, currFreq: null, phase: 'gather', bucketIdx: i,
        explTitle: `Scan Bucket ${i}`,
        explText: `Checking bucket ${i}.`
      }, ctx);

      for (const n of freq[i]) {
        res.push(n);

        domPushState(seq, {
          kind: 'gather', line: 13, color: 'emerald',
          nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
          currNum: n, currFreq: i, phase: 'gather', bucketIdx: i,
          explTitle: `Found Element!`,
          explText: `Appended ${n} to results.`
        }, ctx);

        if (res.length === k) {
          domPushState(seq, {
            kind: 'done', line: 15, color: 'emerald',
            nums, k, count: {...count}, freq: [...freq.map(arr => [...arr])], res: [...res],
            currNum: null, currFreq: null, phase: 'done', bucketIdx: i,
            explTitle: `Done!`,
            explText: `We have found exactly K (${k}) elements. Return results.`
          }, ctx);
          return seq;
        }
      }
    }

    return seq;
  },
  renderDOM(container, state) {
    const isCountPhase = state.phase === 'count';
    const isBucketPhase = state.phase === 'bucket';
    const isGatherPhase = state.phase === 'gather' || state.phase === 'done';

    // Array (Count Phase)
    let arrHTML = '';
    if (isCountPhase) {
      arrHTML = `
        <div class="glass-panel" style="padding: 15px; display: flex; flex-direction: column; align-items: center; width:100%;">
          <div class="panel-heading" style="margin-bottom: 10px; color: var(--accent);">Input Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${state.nums.map((v, i) => {
              const isCur = i === state.i;
              const bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
              const border = isCur ? '#38bdf8' : 'var(--border)';
              return `
                <div style="
                  width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
                  background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-weight: bold;
                  ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + ';' : ''}
                  transition: all 0.3s;
                ">${v}</div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // Hash Map
    const mapHTML = Object.keys(state.count).length === 0 
      ? '<div style="color:var(--text-dim);font-style:italic;">Empty Hash Map</div>' 
      : Object.entries(state.count).map(([val, freq]) => {
          const isTarget = isCountPhase && parseInt(val) === state.currNum;
          const bg = isTarget ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
          const border = isTarget ? '#38bdf8' : 'var(--border)';
          return `
            <div style="
              display:flex; flex-direction:column; align-items:center; border: 1px solid ${border}; border-radius: 6px; overflow: hidden;
              background:${bg}; 
              ${isTarget ? 'transform: scale(1.1); box-shadow: 0 0 10px #38bdf8;' : ''}
              transition: all 0.3s; min-width: 50px;
            ">
              <div style="padding: 4px 10px; background: rgba(0,0,0,0.2); border-bottom: 1px solid ${border}; font-size:12px; color:var(--text-dim);">Num</div>
              <div style="padding: 4px 10px; font-weight:bold;">${val}</div>
              <div style="padding: 4px 10px; background: rgba(0,0,0,0.2); border-top: 1px solid ${border}; font-size:12px; color:var(--text-dim);">Count</div>
              <div style="padding: 4px 10px; font-weight:bold; color: #38bdf8;">${freq}</div>
            </div>
          `;
        }).join('');

    // Buckets
    let bucketHTML = '';
    if (!isCountPhase) {
      bucketHTML = `
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; overflow-x:auto;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #fbbf24;">Frequency Buckets Array</div>
          <div style="display:flex; gap:6px;">
            ${state.freq.map((arr, idx) => {
              const isTarget = isBucketPhase && idx === state.currFreq;
              const isScanning = isGatherPhase && idx === state.bucketIdx;
              
              let border = 'var(--border)';
              let bg = 'var(--surface)';
              let boxsh = '';
              let scale = 1;
              if (isTarget) {
                border = '#fbbf24';
                bg = 'rgba(251,191,36,0.2)';
                boxsh = 'box-shadow: 0 0 10px #fbbf24;';
                scale = 1.05;
              } else if (isScanning) {
                border = '#38bdf8';
                bg = 'rgba(56,189,248,0.2)';
                boxsh = 'box-shadow: 0 0 10px #38bdf8;';
                scale = 1.05;
              }

              const items = arr.map(v => {
                const isItemGather = isGatherPhase && idx === state.currFreq && v === state.currNum;
                return `<div style="
                  background: ${isItemGather ? '#34d399' : 'rgba(0,0,0,0.3)'}; 
                  color: ${isItemGather ? '#000' : 'var(--text)'};
                  padding:4px 8px; border-radius:4px; margin:2px; font-weight:bold;
                  ${isItemGather ? 'box-shadow:0 0 10px #34d399;' : ''}
                ">${v}</div>`;
              }).join('');

              return `
                <div style="
                  display:flex; flex-direction:column; border: 1px solid ${border}; border-radius: 6px; 
                  background:${bg}; width: 60px; min-height: 100px;
                  ${boxsh} transform:scale(${scale});
                  transition: all 0.3s; align-items:center;
                ">
                  <div style="width:100%; text-align:center; padding: 4px 0; background: rgba(0,0,0,0.2); border-bottom: 1px solid ${border}; font-size:11px; color:var(--text-dim);">Idx ${idx}</div>
                  <div style="flex:1; display:flex; flex-direction:column-reverse; padding: 4px; gap:4px; width:100%; align-items:center;">
                    ${items}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // Results
    let resHTML = '';
    if (isGatherPhase) {
      resHTML = `
        <div class="glass-panel" style="padding: 15px; display: flex; flex-direction: column; align-items: center; width:100%;">
          <div class="panel-heading" style="margin-bottom: 10px; color: #34d399;">Result Array (Top K)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; min-height:40px;">
            ${state.res.length === 0 ? '<span style="color:var(--text-dim);font-style:italic;align-self:center;">Empty</span>' : state.res.map(v => `
              <div style="
                width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
                background: rgba(52,211,153,0.2); border: 2px solid #34d399; border-radius: 6px; font-weight: bold; color: #34d399;
              ">${v}</div>
            `).join('')}
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        ${arrHTML}
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Frequencies</div>
          <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
            ${mapHTML}
          </div>
        </div>

        ${bucketHTML}
        ${resHTML}
      </div>
    `;
  }
});

/* ================================ 03 · Longest Substring Without Repeating (DOM) */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Longest Substring Without Repeating Characters', short: 'No Repeats',
  idea: 'Use a <b>Sliding Window</b> and a <b>Hash Set</b>. Advance the right pointer <code>R</code> to expand the window. If a duplicate is found, shrink the window from the left by advancing <code>L</code> until the duplicate is evicted.',
  complexity: 'Time O(N) · Space O(1) (Hash set holds at most 26 chars)',
  input: 'abcabcbb', hint: 'a single string',
  code: [
    'def lengthOfLongestSubstring(s):',
    '    charSet = set()',
    '    l = 0',
    '    res = 0',
    '',
    '    for r in range(len(s)):',
    '        while s[r] in charSet:',
    '            charSet.remove(s[l])',
    '            l += 1',
    '        charSet.add(s[r])',
    '        res = max(res, r - l + 1)',
    '    return res'
  ],
  parse(str) {
    if (!str.trim()) throw new Error('Input cannot be empty');
    return { s: str.trim() };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const charSet = new Set();
    let l = 0, res = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, charSet: Array.from(charSet), l: -1, r: -1, res, phase: 'init',
      explTitle: 'Initialization',
      explText: `Initialize an empty Hash Set, Left pointer, and Result counter.`
    }, ctx);

    for (let r = 0; r < s.length; r++) {
      domPushState(seq, {
        kind: 'visit', line: 6, color: 'blue',
        s, charSet: Array.from(charSet), l, r, res, phase: 'visit',
        explTitle: `Expand Window`,
        explText: `Advance R pointer to index ${r} ('${s[r]}').`
      }, ctx);

      while (charSet.has(s[r])) {
        domPushState(seq, {
          kind: 'duplicate', line: 7, color: 'amber',
          s, charSet: Array.from(charSet), l, r, res, phase: 'shrink',
          explTitle: `Duplicate Found!`,
          explText: `'${s[r]}' is already in the window. Shrinking window from the left...`
        }, ctx);

        charSet.delete(s[l]);
        l++;

        domPushState(seq, {
          kind: 'shrink', line: 9, color: 'amber',
          s, charSet: Array.from(charSet), l, r, res, phase: 'shrink',
          explTitle: `Shrink Complete Step`,
          explText: `Removed '${s[l - 1]}' from the set and advanced L pointer.`
        }, ctx);
      }

      charSet.add(s[r]);
      const curLen = r - l + 1;
      const oldRes = res;
      res = Math.max(res, curLen);

      domPushState(seq, {
        kind: 'update', line: 11, color: 'emerald',
        s, charSet: Array.from(charSet), l, r, res, phase: 'valid',
        explTitle: `Valid Window`,
        explText: `Window is valid! Length is ${curLen}. Max length updated to ${res}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'emerald',
      s, charSet: Array.from(charSet), l, r: s.length - 1, res, phase: 'done',
      explTitle: `Complete`,
      explText: `Reached the end of the string. Maximum valid substring length is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const isShrinking = state.phase === 'shrink';
    
    // String Layout
    const charsHTML = state.s.split('').map((c, i) => {
      const isL = i === state.l;
      const isR = i === state.r;
      const inWindow = i >= state.l && i <= state.r;
      const isDupCheck = isR && isShrinking;

      let bg = inWindow ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = inWindow ? '#38bdf8' : 'var(--border)';
      let boxsh = inWindow ? 'box-shadow: 0 0 10px #38bdf8;' : '';
      let color = 'var(--text)';

      if (isDupCheck) {
        bg = 'rgba(244,63,94,0.2)';
        border = '#f43f5e';
        boxsh = 'box-shadow: 0 0 10px #f43f5e;';
        color = '#f43f5e';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px; height:12px;">
            ${isL ? '<span style="color:#34d399;font-weight:bold;">L</span>' : ''}
            ${isR ? '<span style="color:#fbbf24;font-weight:bold;">R</span>' : ''}
          </div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${boxsh} transition: all 0.3s;
          ">${c}</div>
        </div>
      `;
    }).join('');

    // Set Layout
    const setHTML = state.charSet.length === 0 
      ? '<div style="color:var(--text-dim); font-style:italic;">Empty Window Set</div>'
      : state.charSet.map(v => {
          const isTarget = isShrinking && state.s[state.r] === v;
          return `
            <div style="
              padding: 8px 16px; border-radius: 20px; 
              background: ${isTarget ? '#f43f5e' : 'var(--accent)'};
              color: ${isTarget ? '#fff' : 'var(--accent-ink)'};
              font-weight: bold;
              ${isTarget ? 'box-shadow: 0 0 15px #f43f5e; transform: scale(1.1);' : ''}
              transition: all 0.3s;
            ">${v}</div>
          `;
        }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        
        <div style="display:flex; width:100%; gap:20px;">
          <div class="glass-panel" style="flex: 2; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Sliding Window</div>
            <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:center;">
              ${charsHTML}
            </div>
          </div>
          
          <div class="glass-panel" style="flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content:center;">
            <div style="font-size: 14px; color: var(--text-dim);">Max Length</div>
            <div style="font-size: 48px; font-weight: bold; color: #34d399; margin-top:8px; text-shadow: 0 0 15px rgba(52,211,153,0.4);">
              ${state.res}
            </div>
          </div>
        </div>

        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height:120px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #38bdf8;">Window Character Set</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; align-items:center;">
            ${setHTML}
          </div>
        </div>

      </div>
    `;
  }
});

/* ================================ 06 · Daily Temperatures (DOM) ============ */
defineAlgoDom('06_stack', {
  type: 'dom',
  title: 'Daily Temperatures with a monotonic stack', short: 'Monotonic stack',
  idea: 'Maintain a <b>Monotonic Decreasing Stack</b>. Store pairs of <code>[temp, index]</code>. If the current temperature is greater than the stack top, we found a warmer day! Pop the stack and calculate the day difference.',
  complexity: 'Time O(N) · Space O(N)',
  input: '73, 74, 75, 71, 69, 72, 76, 73', hint: 'comma-separated array of temperatures',
  code: [
    'def dailyTemperatures(temperatures):',
    '    res = [0] * len(temperatures)',
    '    stack = []  # pair: [temp, index]',
    '',
    '    for i, t in enumerate(temperatures):',
    '        while stack and t > stack[-1][0]:',
    '            stackT, stackInd = stack.pop()',
    '            res[stackInd] = (i - stackInd)',
    '        stack.append([t, i])',
    '    return res'
  ],
  parse(str) {
    return { temps: avArr(str) };
  },
  buildStates({ temps }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const res = Array(temps.length).fill(0);
    const stack = [];

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      temps, res: [...res], stack: [...stack], i: -1, phase: 'init',
      explTitle: 'Initialization',
      explText: `Initialize a result array of 0s, and an empty stack.`
    }, ctx);

    for (let i = 0; i < temps.length; i++) {
      const t = temps[i];
      domPushState(seq, {
        kind: 'visit', line: 5, color: 'blue',
        temps, res: [...res], stack: [...stack], i, phase: 'visit',
        explTitle: `Check Temp ${t}`,
        explText: `Current temp is ${t} at index ${i}.`
      }, ctx);

      while (stack.length > 0 && t > stack[stack.length - 1].temp) {
        domPushState(seq, {
          kind: 'compare', line: 6, color: 'amber',
          temps, res: [...res], stack: [...stack], i, phase: 'compare',
          explTitle: `Warmer Day Found!`,
          explText: `${t} > ${stack[stack.length - 1].temp}, so we found a warmer day for index ${stack[stack.length - 1].idx}.`
        }, ctx);

        const popped = stack.pop();
        const diff = i - popped.idx;
        res[popped.idx] = diff;

        domPushState(seq, {
          kind: 'pop', line: 8, color: 'emerald',
          temps, res: [...res], stack: [...stack], i, phase: 'pop', updatedIdx: popped.idx,
          explTitle: `Update Result`,
          explText: `Popped [${popped.temp}, ${popped.idx}]. Difference is ${i} - ${popped.idx} = ${diff} days.`
        }, ctx);
      }

      stack.push({ temp: t, idx: i });
      domPushState(seq, {
        kind: 'push', line: 9, color: 'default',
        temps, res: [...res], stack: [...stack], i, phase: 'push',
        explTitle: `Push to Stack`,
        explText: `Push [${t}, ${i}] to the stack and maintain monotonic decreasing order.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      temps, res: [...res], stack: [...stack], i: -1, phase: 'done',
      explTitle: `Complete`,
      explText: `Any remaining temps in the stack have no warmer future days, so they stay 0.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    // Array
    const arrHTML = state.temps.map((v, i) => {
      const isCur = i === state.i;
      const isUpdated = state.phase === 'pop' && i === state.updatedIdx;
      
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      if (isUpdated) {
        bg = 'rgba(52,211,153,0.2)';
        border = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">Idx ${i}</div>
          <div style="
            width: 45px; display: flex; flex-direction:column; align-items: center; justify-content: center;
            background: ${bg}; border: 1px solid ${border}; border-radius: 6px; overflow:hidden;
            ${isCur || isUpdated ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + '; z-index:2;' : ''}
            transition: all 0.3s;
          ">
            <div style="padding: 4px; font-weight: bold; font-size:16px;">${v}°</div>
            <div style="width:100%; padding: 4px; background: rgba(0,0,0,0.2); border-top: 1px solid ${border}; font-size: 14px; font-family:var(--mono); color: ${isUpdated ? '#34d399' : 'var(--text)'}; text-align:center;">
              ${state.res[i]}
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Stack
    const stackHTML = state.stack.length === 0 
      ? '<div style="color:var(--text-dim);font-style:italic;align-self:center;">Empty Stack</div>' 
      : state.stack.map((item, idx) => {
          const isTop = idx === state.stack.length - 1;
          const isTarget = isTop && (state.phase === 'compare');
          
          let border = 'var(--border)';
          let bg = 'rgba(0,0,0,0.3)';
          if (isTarget) {
            border = '#f43f5e';
            bg = 'rgba(244,63,94,0.2)';
          } else if (isTop && state.phase === 'push') {
            border = '#34d399';
            bg = 'rgba(52,211,153,0.2)';
          }

          return `
            <div style="
              display:flex; border: 1px solid ${border}; border-radius: 6px; overflow: hidden;
              background:${bg}; font-family: var(--mono); width: 100px;
              ${isTarget || (isTop && state.phase === 'push') ? 'transform: scale(1.05); box-shadow: 0 0 10px ' + border + ';' : ''}
              transition: all 0.3s;
            ">
              <div style="flex:1; padding: 6px; border-right: 1px solid ${border}; text-align:center; font-weight:bold;">${item.temp}°</div>
              <div style="flex:1; padding: 6px; background: rgba(0,0,0,0.1); text-align:center; color:var(--text-dim);">[${item.idx}]</div>
            </div>
          `;
        }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        
        <div style="display:flex; width:100%; gap:20px;">
          <div class="glass-panel" style="flex: 2; padding: 20px; display: flex; flex-direction: column; align-items: center; overflow-x:auto;">
            <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Temperatures & Result Array</div>
            <div style="display:flex; gap:10px; justify-content:center;">
              ${arrHTML}
            </div>
          </div>
          
          <div class="glass-panel" style="flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content:center; min-height: 200px;">
            <div class="panel-heading" style="margin-bottom: 15px; color: #fbbf24;">Monotonic Stack</div>
            <div style="display:flex; flex-direction: column-reverse; gap:6px; flex:1; width:100%; align-items:center;">
              ${stackHTML}
            </div>
            <div style="width: 120px; height: 10px; border-bottom: 2px solid #fbbf24; border-left: 2px solid #fbbf24; border-right: 2px solid #fbbf24; margin-top:4px; border-bottom-left-radius:8px; border-bottom-right-radius:8px;"></div>
          </div>
        </div>

      </div>
    `;
  }
});

/* ================================ 01 · Concatenation of Array (DOM) ======== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Concatenation of Array', short: 'Concat Array',
  idea: 'We need to create an array <code>ans</code> of length <code>2n</code> where <code>ans[i] == nums[i]</code> and <code>ans[i + n] == nums[i]</code>. We can iterate once and assign both indices simultaneously.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 2, 1', hint: 'comma-separated array',
  code: [
    'def getConcatenation(nums):',
    '    n = len(nums)',
    '    ans = [0] * (2 * n)',
    '    for i in range(n):',
    '        ans[i] = nums[i]',
    '        ans[i + n] = nums[i]',
    '    return ans'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = nums.length;
    const ans = Array(2 * n).fill(null);

    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      nums, ans: [...ans], i: -1, phase: 'init', n,
      explTitle: 'Initialization',
      explText: `Array length is ${n}. Initialize empty ans array of length ${2*n}.`
    }, ctx);

    for (let i = 0; i < n; i++) {
      ans[i] = nums[i];
      domPushState(seq, {
        kind: 'assign1', line: 5, color: 'blue',
        nums, ans: [...ans], i, phase: 'first', n,
        explTitle: `Copy to i`,
        explText: `Copy nums[${i}] = ${nums[i]} to ans[${i}].`
      }, ctx);

      ans[i + n] = nums[i];
      domPushState(seq, {
        kind: 'assign2', line: 6, color: 'emerald',
        nums, ans: [...ans], i, phase: 'second', n,
        explTitle: `Copy to i + n`,
        explText: `Copy nums[${i}] = ${nums[i]} to ans[${i + n}].`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 7, color: 'emerald',
      nums, ans: [...ans], i: -1, phase: 'done', n,
      explTitle: `Done`,
      explText: `Return the concatenated array.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, i) => {
      const isCur = state.i === i;
      const bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      const border = isCur ? '#38bdf8' : 'var(--border)';
      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${i}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px;
            ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + ';' : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    const ansHTML = state.ans.map((v, idx) => {
      let isTarget = false;
      let border = 'var(--border)';
      let bg = 'rgba(0,0,0,0.1)';
      let textCol = 'var(--text-dim)';
      let boxsh = '';

      if (state.i !== -1) {
        if (state.phase === 'first' && idx === state.i) {
          isTarget = true; border = '#38bdf8'; bg = 'rgba(56,189,248,0.2)'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; textCol = 'var(--text)';
        } else if (state.phase === 'second' && (idx === state.i || idx === state.i + state.n)) {
          if (idx === state.i + state.n) {
            isTarget = true; border = '#34d399'; bg = 'rgba(52,211,153,0.2)'; boxsh = 'box-shadow: 0 0 10px #34d399;'; textCol = 'var(--text)';
          } else {
            border = '#38bdf8'; bg = 'rgba(56,189,248,0.1)'; textCol = 'var(--text)';
          }
        }
      }

      if (v !== null && !isTarget) {
        textCol = 'var(--text)';
        bg = 'var(--surface)';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px; color:${textCol};
            ${isTarget ? `transform: scale(1.1); ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v === null ? '' : v}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">nums (Length ${state.n})</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">ans (Length ${2*state.n})</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${ansHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Majority Element (DOM) ============== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Majority Element', short: 'Majority Elem',
  idea: 'We can use the <b>Boyer-Moore Voting Algorithm</b>. We maintain a <code>candidate</code> and a <code>count</code>. If count is 0, we assign the current element as candidate. If it matches candidate, count increments; otherwise it decrements.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 2, 1, 1, 1, 2, 2', hint: 'comma-separated array',
  code: [
    'def majorityElement(nums):',
    '    res, count = 0, 0',
    '',
    '    for n in nums:',
    '        if count == 0:',
    '            res = n',
    '        if n == res:',
    '            count += 1',
    '        else:',
    '            count -= 1',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let res = 0;
    let count = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, res, count, i: -1, phase: 'init',
      explTitle: 'Initialization',
      explText: `Start with an initial count of 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      const n = nums[i];
      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        nums, res, count, i, phase: 'visit', n,
        explTitle: `Check ${n}`,
        explText: `Current number is ${n}.`
      }, ctx);

      if (count === 0) {
        res = n;
        domPushState(seq, {
          kind: 'swap', line: 6, color: 'amber',
          nums, res, count, i, phase: 'swap', n,
          explTitle: `New Candidate!`,
          explText: `Count is 0, so ${n} becomes the new candidate majority element.`
        }, ctx);
      }

      if (n === res) {
        count += 1;
        domPushState(seq, {
          kind: 'inc', line: 8, color: 'emerald',
          nums, res, count, i, phase: 'inc', n,
          explTitle: `Increment Count`,
          explText: `${n} matches candidate, increment count to ${count}.`
        }, ctx);
      } else {
        count -= 1;
        domPushState(seq, {
          kind: 'dec', line: 10, color: 'red',
          nums, res, count, i, phase: 'dec', n,
          explTitle: `Decrement Count`,
          explText: `${n} != candidate, decrement count to ${count}.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, res, count, i: -1, phase: 'done', n: null,
      explTitle: `Done`,
      explText: `The majority element is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, i) => {
      const isCur = state.i === i;
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      if (isCur && state.phase === 'inc') { bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; }
      if (isCur && state.phase === 'dec') { bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; }
      if (isCur && state.phase === 'swap') { bg = 'rgba(251,191,36,0.2)'; border = '#fbbf24'; }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size:18px;
            ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + ';' : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    const isDone = state.phase === 'done';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Input Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; justify-content:center;">
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:150px; ${isDone ? 'border-color:#34d399; box-shadow:0 0 20px rgba(52,211,153,0.3);' : ''}">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Candidate (res)</div>
            <div style="font-size: 40px; font-weight: bold; color: ${isDone ? '#34d399' : '#fbbf24'};">
              ${state.i === -1 && state.phase === 'init' ? '-' : state.res}
            </div>
          </div>
          
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:150px;">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Count</div>
            <div style="font-size: 40px; font-weight: bold; color: ${state.phase === 'inc' ? '#34d399' : state.phase === 'dec' ? '#f43f5e' : '#38bdf8'}; transition: color 0.3s;">
              ${state.count}
            </div>
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Find All Numbers Disappeared ======== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Find All Numbers Disappeared in an Array', short: 'Disappeared Nums',
  idea: 'We can mark a number <code>n</code> as seen by jumping to index <code>abs(n) - 1</code> and negating the value there. After a single pass, any index with a positive value means we never saw <code>index + 1</code>!',
  complexity: 'Time O(N) · Space O(1) (excluding output array)',
  input: '4, 3, 2, 7, 8, 2, 3, 1', hint: 'comma-separated array (elements 1..N)',
  code: [
    'def findDisappearedNumbers(nums):',
    '    for n in nums:',
    '        i = abs(n) - 1',
    '        nums[i] = -1 * abs(nums[i])',
    '',
    '    res = []',
    '    for i, n in enumerate(nums):',
    '        if n > 0:',
    '            res.append(i + 1)',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums];
    const res = [];

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], res: [...res], i: -1, phase: 'init', targetIdx: -1,
      explTitle: 'Initialization',
      explText: `We will scan the array and negate elements.`
    }, ctx);

    // Pass 1: Negation
    for (let i = 0; i < arr.length; i++) {
      const n = Math.abs(arr[i]);
      const targetIdx = n - 1;

      domPushState(seq, {
        kind: 'visit', line: 3, color: 'blue',
        nums: [...arr], res: [...res], i, phase: 'calc', targetIdx,
        explTitle: `Check |${arr[i]}|`,
        explText: `Current abs value is ${n}. Target index is ${n} - 1 = ${targetIdx}.`
      }, ctx);

      arr[targetIdx] = -1 * Math.abs(arr[targetIdx]);
      
      domPushState(seq, {
        kind: 'negate', line: 4, color: 'red',
        nums: [...arr], res: [...res], i, phase: 'negate', targetIdx,
        explTitle: `Negate Value`,
        explText: `Set nums[${targetIdx}] to negative to mark ${n} as seen.`
      }, ctx);
    }

    // Pass 2: Gathering
    domPushState(seq, {
      kind: 'pass2_init', line: 7, color: 'default',
      nums: [...arr], res: [...res], i: -1, phase: 'gather_init', targetIdx: -1,
      explTitle: `Second Pass`,
      explText: `Scan for positive values. A positive value at index i means i+1 was missing.`
    }, ctx);

    for (let i = 0; i < arr.length; i++) {
      domPushState(seq, {
        kind: 'check_pos', line: 8, color: 'amber',
        nums: [...arr], res: [...res], i, phase: 'check_pos', targetIdx: -1,
        explTitle: `Check index ${i}`,
        explText: `Is ${arr[i]} > 0?`
      }, ctx);

      if (arr[i] > 0) {
        res.push(i + 1);
        domPushState(seq, {
          kind: 'found', line: 9, color: 'emerald',
          nums: [...arr], res: [...res], i, phase: 'found', targetIdx: -1,
          explTitle: `Missing Number Found!`,
          explText: `${arr[i]} is positive! Append ${i + 1} to results.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      nums: [...arr], res: [...res], i: -1, phase: 'done', targetIdx: -1,
      explTitle: `Complete`,
      explText: `Missing numbers are: ${res.join(', ')}`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const isPass1 = state.phase === 'calc' || state.phase === 'negate';
    const isPass2 = state.phase === 'check_pos' || state.phase === 'found';

    const arrHTML = state.nums.map((v, i) => {
      const isCur = state.i === i;
      const isTarget = isPass1 && i === state.targetIdx;
      
      let border = 'var(--border)';
      let bg = 'var(--surface)';
      let boxsh = '';
      let color = v < 0 ? '#f43f5e' : 'var(--text)'; // Negatives are red

      if (isCur) {
        border = isPass2 ? '#fbbf24' : '#38bdf8';
        bg = isPass2 ? 'rgba(251,191,36,0.2)' : 'rgba(56,189,248,0.2)';
        boxsh = `box-shadow: 0 0 10px ${border};`;
      }
      
      if (isTarget) {
        border = '#f43f5e';
        bg = state.phase === 'negate' ? 'rgba(244,63,94,0.3)' : 'rgba(244,63,94,0.1)';
        boxsh = 'box-shadow: 0 0 15px #f43f5e;';
      }

      if (state.phase === 'found' && isCur) {
        border = '#34d399'; bg = 'rgba(52,211,153,0.2)'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">Idx ${i}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size:16px; color:${color};
            ${isCur || isTarget ? `transform: scale(1.1); ${boxsh} z-index:2;` : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    const resHTML = state.phase === 'init' || isPass1 ? '' : `
      <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; margin-top:20px; max-width:600px;">
        <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Result Array</div>
        <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; min-height:45px;">
          ${state.res.length === 0 ? '<span style="color:var(--text-dim); font-style:italic; align-self:center;">Empty</span>' : state.res.map(v => `
            <div style="
              width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
              background: rgba(52,211,153,0.2); border: 2px solid #34d399; border-radius: 8px; font-weight: bold; font-size:16px; color:#34d399;
            ">${v}</div>
          `).join('')}
        </div>
      </div>
    `;

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Array (Negatives mark presence)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${arrHTML}
          </div>
        </div>
        ${resHTML}
      </div>
    `;
  }
});

/* ================================ 01 · Encode and Decode Strings (DOM) ===== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Encode and Decode Strings', short: 'Encode & Decode',
  idea: 'To encode, we can prepend the length of each string followed by a delimiter (like <code>#</code>). E.g. <code>"neet"</code> becomes <code>"4#neet"</code>. To decode, we read the integer until <code>#</code>, then extract exactly that many characters.',
  complexity: 'Time O(N) · Space O(N)',
  input: 'neet, code, love, you', hint: 'comma-separated strings',
  code: [
    'class Codec:',
    '    def encode(self, strs):',
    '        res = ""',
    '        for s in strs:',
    '            res += str(len(s)) + "#" + s',
    '        return res',
    '',
    '    def decode(self, s):',
    '        res, i = [], 0',
    '        while i < len(s):',
    '            j = i',
    '            while s[j] != "#":',
    '                j += 1',
    '            length = int(s[i:j])',
    '            res.append(s[j + 1 : j + 1 + length])',
    '            i = j + 1 + length',
    '        return res'
  ],
  parse(str) {
    return { strs: str.split(',').map(s => s.trim()) };
  },
  buildStates({ strs }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    // --- Encoding Phase ---
    let encoded = "";
    domPushState(seq, {
      kind: 'encode_init', line: 2, color: 'default',
      strs, encoded, decoded: [], phase: 'encode_init', activeStr: -1, i: -1, j: -1,
      explTitle: 'Encode Init',
      explText: `Start encoding array of ${strs.length} strings.`
    }, ctx);

    for (let k = 0; k < strs.length; k++) {
      const s = strs[k];
      domPushState(seq, {
        kind: 'encode_process', line: 5, color: 'blue',
        strs, encoded, decoded: [], phase: 'encode_process', activeStr: k, i: -1, j: -1,
        explTitle: `Encode "${s}"`,
        explText: `Length is ${s.length}. Append "${s.length}#${s}".`
      }, ctx);
      
      encoded += `${s.length}#${s}`;
      
      domPushState(seq, {
        kind: 'encode_append', line: 5, color: 'emerald',
        strs, encoded, decoded: [], phase: 'encode_append', activeStr: k, i: -1, j: -1,
        explTitle: `String Encoded`,
        explText: `Encoded string is now: ${encoded}`
      }, ctx);
    }

    // --- Decoding Phase ---
    let decoded = [];
    let i = 0;
    domPushState(seq, {
      kind: 'decode_init', line: 9, color: 'default',
      strs, encoded, decoded: [...decoded], phase: 'decode_init', activeStr: -1, i, j: -1,
      explTitle: 'Decode Init',
      explText: `Start decoding: "${encoded}". Pointer i starts at 0.`
    }, ctx);

    while (i < encoded.length) {
      let j = i;
      domPushState(seq, {
        kind: 'decode_scan', line: 12, color: 'amber',
        strs, encoded, decoded: [...decoded], phase: 'decode_scan', activeStr: -1, i, j,
        explTitle: `Find Delimiter`,
        explText: `Scan for '#' starting at index ${j}.`
      }, ctx);
      
      while (encoded[j] !== '#') {
        j++;
      }
      
      let length = parseInt(encoded.substring(i, j), 10);
      domPushState(seq, {
        kind: 'decode_len', line: 14, color: 'amber',
        strs, encoded, decoded: [...decoded], phase: 'decode_len', activeStr: -1, i, j, length,
        explTitle: `Parse Length`,
        explText: `Found '#' at index ${j}. Length parsed: ${length}.`
      }, ctx);
      
      let word = encoded.substring(j + 1, j + 1 + length);
      decoded.push(word);
      
      domPushState(seq, {
        kind: 'decode_extract', line: 15, color: 'emerald',
        strs, encoded, decoded: [...decoded], phase: 'decode_extract', activeStr: -1, i, j, length, word,
        explTitle: `Extract String`,
        explText: `Extracted ${length} chars: "${word}".`
      }, ctx);
      
      i = j + 1 + length;
    }

    domPushState(seq, {
      kind: 'done', line: 17, color: 'emerald',
      strs, encoded, decoded: [...decoded], phase: 'done', activeStr: -1, i: -1, j: -1,
      explTitle: `Done!`,
      explText: `Successfully encoded and decoded the strings.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const origHTML = state.strs.map((s, idx) => {
      let isCur = state.activeStr === idx;
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      return `
        <div style="padding: 8px 12px; background: ${bg}; border: 1px solid ${border}; border-radius: 6px; font-family: monospace; ${isCur ? 'transform:scale(1.05); box-shadow:0 0 10px #38bdf8;' : ''} transition: all 0.3s;">
          "${s}"
        </div>
      `;
    }).join('');

    let encodedStrHTML = '';
    if (state.encoded === '') {
      encodedStrHTML = '<span style="color:var(--text-dim); font-style:italic;">Empty</span>';
    } else {
      let chars = state.encoded.split('');
      encodedStrHTML = chars.map((char, idx) => {
        let isI = state.phase.startsWith('decode') && idx === state.i;
        let isJ = state.phase.startsWith('decode') && idx === state.j;
        let isExtract = state.phase === 'decode_extract' && idx > state.j && idx <= state.j + state.length;
        
        let bg = 'transparent';
        let color = 'var(--text)';
        if (char === '#') color = '#f43f5e'; // Highlight delimiters red
        if (isExtract) bg = 'rgba(52,211,153,0.3)';
        
        return `
          <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
            <div style="
              width:20px; height:24px; display:flex; align-items:center; justify-content:center;
              background:${bg}; color:${color}; font-family:monospace; font-size:16px; font-weight:bold;
              border-bottom: 1px solid var(--border);
            ">${char}</div>
            ${isI ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:10px;">i</div>' : ''}
            ${isJ ? '<div style="position:absolute; bottom:-28px; color:#fbbf24; font-size:10px;">j</div>' : ''}
          </div>
        `;
      }).join('');
    }

    const decodedHTML = state.decoded.map(s => `
      <div style="padding: 8px 12px; background: rgba(52,211,153,0.1); border: 1px solid #34d399; border-radius: 6px; font-family: monospace; color:#34d399;">
        "${s}"
      </div>
    `).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div style="display:flex; width:100%; gap:20px;">
          <div class="glass-panel" style="flex:1; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Original Strings</div>
            <div style="display:flex; flex-direction:column; gap:10px; width:100%;">
              ${origHTML}
            </div>
          </div>
          
          <div class="glass-panel" style="flex:1; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Decoded Strings</div>
            <div style="display:flex; flex-direction:column; gap:10px; width:100%; min-height:100px;">
              ${decodedHTML}
            </div>
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; min-height:120px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #f43f5e;">Encoded Stream</div>
          <div style="display:flex; gap:2px; flex-wrap:wrap; justify-content:center;">
            ${encodedStrHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Product of Array Except Self (DOM) = */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Product of Array Except Self', short: 'Prod Except Self',
  idea: 'We can solve this in O(N) by calculating a <code>prefix</code> product from the left, and a <code>postfix</code> product from the right. To optimize space, we can store prefix products directly in the <code>res</code> array, then multiply them by the postfix running product in a second pass.',
  complexity: 'Time O(N) · Space O(1) (excluding output array)',
  input: '1, 2, 3, 4', hint: 'comma-separated array',
  code: [
    'def productExceptSelf(nums):',
    '    res = [1] * len(nums)',
    '',
    '    prefix = 1',
    '    for i in range(len(nums)):',
    '        res[i] = prefix',
    '        prefix *= nums[i]',
    '',
    '    postfix = 1',
    '    for i in range(len(nums) - 1, -1, -1):',
    '        res[i] *= postfix',
    '        postfix *= nums[i]',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = nums.length;
    const res = Array(n).fill(1);

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, res: [...res], i: -1, phase: 'init', prefix: 1, postfix: 1,
      explTitle: 'Initialization',
      explText: `Create an output array of 1s.`
    }, ctx);

    // Pass 1: Prefix
    let prefix = 1;
    for (let i = 0; i < n; i++) {
      res[i] = prefix;
      domPushState(seq, {
        kind: 'prefix_set', line: 6, color: 'blue',
        nums, res: [...res], i, phase: 'prefix1', prefix, postfix: 1,
        explTitle: `Set Prefix (Idx ${i})`,
        explText: `res[${i}] = prefix (${prefix}).`
      }, ctx);

      prefix *= nums[i];
      domPushState(seq, {
        kind: 'prefix_calc', line: 7, color: 'amber',
        nums, res: [...res], i, phase: 'prefix2', prefix, postfix: 1,
        explTitle: `Update Prefix`,
        explText: `prefix = prefix * nums[${i}] => ${prefix}.`
      }, ctx);
    }

    // Pass 2: Postfix
    let postfix = 1;
    for (let i = n - 1; i >= 0; i--) {
      res[i] *= postfix;
      domPushState(seq, {
        kind: 'postfix_set', line: 11, color: 'emerald',
        nums, res: [...res], i, phase: 'postfix1', prefix, postfix,
        explTitle: `Multiply Postfix (Idx ${i})`,
        explText: `res[${i}] *= postfix (${postfix}) => ${res[i]}.`
      }, ctx);

      postfix *= nums[i];
      domPushState(seq, {
        kind: 'postfix_calc', line: 12, color: 'amber',
        nums, res: [...res], i, phase: 'postfix2', prefix, postfix,
        explTitle: `Update Postfix`,
        explText: `postfix = postfix * nums[${i}] => ${postfix}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      nums, res: [...res], i: -1, phase: 'done', prefix, postfix,
      explTitle: `Complete`,
      explText: `Output array contains products except self.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const isPrefix = state.phase.startsWith('prefix');
    const isPostfix = state.phase.startsWith('postfix');

    const numsHTML = state.nums.map((v, i) => {
      const isCur = state.i === i;
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      
      if (isCur && isPostfix) { border = '#34d399'; bg = 'rgba(52,211,153,0.2)'; }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">Idx ${i}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size:16px;
            ${isCur ? 'transform: scale(1.1); box-shadow: 0 0 10px ' + border + ';' : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    const resHTML = state.res.map((v, i) => {
      const isCur = state.i === i;
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';

      if (isPrefix) {
        if (i < state.i) { bg = 'rgba(56,189,248,0.1)'; border = '#38bdf8'; } // completed
        if (isCur && state.phase === 'prefix1') { bg = 'rgba(56,189,248,0.3)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 15px #38bdf8;'; color = '#38bdf8'; }
      }
      if (isPostfix || state.phase === 'done') {
        bg = 'rgba(56,189,248,0.1)'; border = '#38bdf8'; // Base from pass 1
        if (i > state.i || state.phase === 'done') { bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; color = '#34d399'; } // multiplied
        if (isCur && state.phase === 'postfix1') { bg = 'rgba(52,211,153,0.4)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399'; }
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="
            width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size:18px; color:${color};
            ${isCur ? `transform: scale(1.1); ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">nums Array</div>
          <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; width:100%; gap:20px; justify-content:center;">
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:120px;">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Prefix</div>
            <div style="font-size: 32px; font-weight: bold; color: ${isPrefix ? '#38bdf8' : 'var(--text-dim)'};">
              ${state.phase !== 'init' ? state.prefix : '-'}
            </div>
          </div>
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:120px;">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Postfix</div>
            <div style="font-size: 32px; font-weight: bold; color: ${isPostfix ? '#34d399' : 'var(--text-dim)'};">
              ${isPostfix || state.phase === 'done' ? state.postfix : '-'}
            </div>
          </div>
        </div>

        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: #34d399;">Result Array</div>
          <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center;">
            ${resHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Valid Sudoku (DOM) ================== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Valid Sudoku', short: 'Valid Sudoku',
  idea: 'We need to check if every row, column, and 3x3 sub-box contains unique digits (1-9). We can use Hash Sets for each row, column, and square to track seen digits in a single pass.',
  complexity: 'Time O(9^2) = O(1) · Space O(9^2) = O(1)',
  input: '9x9 Grid (Simplified for UI)', hint: 'Automatically generates a small valid/invalid grid',
  code: [
    'def isValidSudoku(board):',
    '    cols = collections.defaultdict(set)',
    '    rows = collections.defaultdict(set)',
    '    squares = collections.defaultdict(set)',
    '',
    '    for r in range(9):',
    '        for c in range(9):',
    '            if board[r][c] == ".":',
    '                continue',
    '            if (board[r][c] in rows[r] or',
    '                board[r][c] in cols[c] or',
    '                board[r][c] in squares[(r // 3, c // 3)]):',
    '                return False',
    '            cols[c].add(board[r][c])',
    '            rows[r].add(board[r][c])',
    '            squares[(r // 3, c // 3)].add(board[r][c])',
    '    return True'
  ],
  parse(str) {
    // Return a fixed 9x9 board with some filled numbers
    return {
      board: [
        ["5","3",".",".","7",".",".",".","."],
        ["6",".",".","1","9","5",".",".","."],
        [".","9","8",".",".",".",".","6","."],
        ["8",".",".",".","6",".",".",".","3"],
        ["4",".",".","8",".","3",".",".","1"],
        ["7",".",".",".","2",".",".",".","6"],
        [".","6",".",".",".",".","2","8","."],
        [".",".",".","4","1","9",".",".","5"],
        [".",".",".",".","8",".",".","7","9"]
      ]
    };
  },
  buildStates({ board }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let rows = Array.from({length: 9}, () => new Set());
    let cols = Array.from({length: 9}, () => new Set());
    let sqrs = Array.from({length: 9}, () => new Set()); // index: (r//3)*3 + (c//3)
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      board, r: -1, c: -1, phase: 'init', valid: true,
      rows: rows.map(s => [...s]), cols: cols.map(s => [...s]), sqrs: sqrs.map(s => [...s]),
      explTitle: 'Initialization',
      explText: `Create Hash Sets for 9 rows, 9 columns, and 9 squares.`
    }, ctx);

    // For visualization speed, we'll only step through non-empty cells
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        const val = board[r][c];
        if (val === '.') continue;

        domPushState(seq, {
          kind: 'visit', line: 10, color: 'blue',
          board, r, c, phase: 'check', valid: true, val,
          rows: rows.map(s => [...s]), cols: cols.map(s => [...s]), sqrs: sqrs.map(s => [...s]),
          explTitle: `Check [${r}][${c}]`,
          explText: `Cell value is '${val}'. Is it in Row ${r}, Col ${c}, or Sq ${(Math.floor(r/3)*3) + Math.floor(c/3)}?`
        }, ctx);

        const sqIdx = Math.floor(r / 3) * 3 + Math.floor(c / 3);

        if (rows[r].has(val) || cols[c].has(val) || sqrs[sqIdx].has(val)) {
          domPushState(seq, {
            kind: 'invalid', line: 13, color: 'red',
            board, r, c, phase: 'invalid', valid: false, val,
            rows: rows.map(s => [...s]), cols: cols.map(s => [...s]), sqrs: sqrs.map(s => [...s]),
            explTitle: `Duplicate Found!`,
            explText: `'${val}' is already present in this row, col, or square.`
          }, ctx);
          return seq;
        }

        rows[r].add(val);
        cols[c].add(val);
        sqrs[sqIdx].add(val);

        domPushState(seq, {
          kind: 'add', line: 14, color: 'emerald',
          board, r, c, phase: 'add', valid: true, val,
          rows: rows.map(s => [...s]), cols: cols.map(s => [...s]), sqrs: sqrs.map(s => [...s]),
          explTitle: `Add to Sets`,
          explText: `Added '${val}' to Row ${r}, Col ${c}, Sq ${sqIdx}.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 17, color: 'emerald',
      board, r: -1, c: -1, phase: 'done', valid: true,
      rows: rows.map(s => [...s]), cols: cols.map(s => [...s]), sqrs: sqrs.map(s => [...s]),
      explTitle: `Done`,
      explText: `No duplicates found. Sudoku is valid!`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    let boardHTML = '';
    for (let i = 0; i < 9; i++) {
      boardHTML += `<div style="display:flex;">`;
      for (let j = 0; j < 9; j++) {
        const val = state.board[i][j];
        const isCur = state.r === i && state.c === j;
        
        let bg = 'transparent';
        let border = '1px solid var(--border)';
        let color = val === '.' ? 'transparent' : 'var(--text)';
        
        // Thicker borders for 3x3 grids
        let bb = (i === 2 || i === 5) ? '2px solid #555' : border;
        let br = (j === 2 || j === 5) ? '2px solid #555' : border;
        
        if (isCur) {
          bg = state.phase === 'invalid' ? 'rgba(244,63,94,0.3)' : 'rgba(56,189,248,0.3)';
          color = state.phase === 'invalid' ? '#f43f5e' : '#38bdf8';
        }

        boardHTML += `
          <div style="
            width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border-bottom: ${bb}; border-right: ${br}; 
            ${i===0 ? 'border-top:1px solid var(--border);' : ''}
            ${j===0 ? 'border-left:1px solid var(--border);' : ''}
            font-weight: bold; font-size: 16px; color: ${color};
          ">${val === '.' ? '' : val}</div>
        `;
      }
      boardHTML += `</div>`;
    }

    // Hash Set Viz for current cell
    let setHTML = '';
    if (state.r !== -1) {
      const sqIdx = Math.floor(state.r / 3) * 3 + Math.floor(state.c / 3);
      const rSet = state.rows[state.r].join(', ');
      const cSet = state.cols[state.c].join(', ');
      const sSet = state.sqrs[sqIdx].join(', ');
      
      setHTML = `
        <div style="display:flex; width:100%; gap:10px; margin-top:20px; justify-content:center;">
          <div style="flex:1; background:var(--surface); border:1px solid var(--border); padding:10px; border-radius:6px; text-align:center;">
            <div style="font-size:10px; color:var(--text-dim);">Row ${state.r} Set</div>
            <div style="color:#fbbf24; font-family:monospace;">{ ${rSet} }</div>
          </div>
          <div style="flex:1; background:var(--surface); border:1px solid var(--border); padding:10px; border-radius:6px; text-align:center;">
            <div style="font-size:10px; color:var(--text-dim);">Col ${state.c} Set</div>
            <div style="color:#fbbf24; font-family:monospace;">{ ${cSet} }</div>
          </div>
          <div style="flex:1; background:var(--surface); border:1px solid var(--border); padding:10px; border-radius:6px; text-align:center;">
            <div style="font-size:10px; color:var(--text-dim);">Sq ${sqIdx} Set</div>
            <div style="color:#fbbf24; font-family:monospace;">{ ${sSet} }</div>
          </div>
        </div>
      `;
    } else if (state.phase === 'done') {
      setHTML = `<div style="color:#34d399; font-size:24px; font-weight:bold; margin-top:20px;">VALID SUDOKU</div>`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">9x9 Sudoku Board</div>
          <div style="display:flex; flex-direction:column; border: 2px solid #555;">
            ${boardHTML}
          </div>
          ${setHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Longest Consecutive Sequence (DOM) == */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Longest Consecutive Sequence', short: 'Longest Consec',
  idea: 'Put all numbers in a <b>Hash Set</b>. For each number <code>n</code>, check if <code>n - 1</code> exists. If it does not, <code>n</code> is the start of a sequence! From there, count upwards (<code>n + 1</code>, <code>n + 2</code>, etc.) and update the max length.',
  complexity: 'Time O(N) · Space O(N)',
  input: '100, 4, 200, 1, 3, 2', hint: 'comma-separated array',
  code: [
    'def longestConsecutive(nums):',
    '    numSet = set(nums)',
    '    longest = 0',
    '',
    '    for n in nums:',
    '        if (n - 1) not in numSet:',
    '            length = 0',
    '            while (n + length) in numSet:',
    '                length += 1',
    '            longest = max(length, longest)',
    '    return longest'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const numSet = new Set(nums);
    let longest = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, numSet: [...numSet], n: null, longest, phase: 'init', curLength: 0, curNum: null,
      explTitle: 'Create Hash Set',
      explText: `Dump all numbers into a Hash Set for O(1) lookups.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      const n = nums[i];
      domPushState(seq, {
        kind: 'visit', line: 5, color: 'blue',
        nums, numSet: [...numSet], n, longest, phase: 'check_start', curLength: 0, curNum: null,
        explTitle: `Check ${n}`,
        explText: `Does ${n - 1} exist in the set?`
      }, ctx);

      if (!numSet.has(n - 1)) {
        domPushState(seq, {
          kind: 'is_start', line: 6, color: 'emerald',
          nums, numSet: [...numSet], n, longest, phase: 'start_found', curLength: 0, curNum: null,
          explTitle: `Sequence Start!`,
          explText: `${n - 1} is not in the set, so ${n} is the start of a sequence.`
        }, ctx);

        let length = 0;
        while (numSet.has(n + length)) {
          domPushState(seq, {
            kind: 'count', line: 8, color: 'amber',
            nums, numSet: [...numSet], n, longest, phase: 'counting', curLength: length, curNum: n + length,
            explTitle: `Count Upwards`,
            explText: `${n + length} exists in the set! Length is now ${length + 1}.`
          }, ctx);
          length++;
        }

        longest = Math.max(longest, length);
        domPushState(seq, {
          kind: 'update_max', line: 10, color: 'emerald',
          nums, numSet: [...numSet], n, longest, phase: 'update', curLength: length, curNum: null,
          explTitle: `Update Max`,
          explText: `Sequence length is ${length}. Max is now ${longest}.`
        }, ctx);
      } else {
        domPushState(seq, {
          kind: 'skip', line: 5, color: 'red',
          nums, numSet: [...numSet], n, longest, phase: 'skip', curLength: 0, curNum: null,
          explTitle: `Not a Start`,
          explText: `${n - 1} exists in the set, so ${n} is in the middle of a sequence. Skip it.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, numSet: [...numSet], n: null, longest, phase: 'done', curLength: 0, curNum: null,
      explTitle: `Done`,
      explText: `The longest consecutive sequence has length ${longest}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const setHTML = state.numSet.map(v => {
      let isN = v === state.n;
      let isCurCounting = state.phase === 'counting' && v === state.curNum;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let boxsh = '';
      
      if (isN) {
        if (state.phase === 'skip') { bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; }
        else if (state.phase === 'start_found' || state.phase === 'update') { bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; }
        else { bg = 'rgba(56,189,248,0.2)'; border = '#38bdf8'; }
      }
      
      if (isCurCounting) {
        bg = 'rgba(251,191,36,0.3)'; border = '#fbbf24'; boxsh = 'box-shadow: 0 0 15px #fbbf24;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="
            width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 50%; font-weight: bold; font-size:16px;
            ${isN || isCurCounting ? `transform: scale(1.1); ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');

    const isDone = state.phase === 'done';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Hash Set</div>
          <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center;">
            ${setHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; justify-content:center;">
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:150px;">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Current Sequence</div>
            <div style="font-size: 40px; font-weight: bold; color: ${state.phase === 'counting' ? '#fbbf24' : 'var(--text-dim)'};">
              ${state.curLength || 0}
            </div>
          </div>
          
          <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:150px; ${isDone ? 'border-color:#34d399; box-shadow:0 0 20px rgba(52,211,153,0.3);' : ''}">
            <div style="font-size: 14px; color: var(--text-dim); margin-bottom:5px;">Max Longest</div>
            <div style="font-size: 40px; font-weight: bold; color: ${isDone ? '#34d399' : '#38bdf8'}; transition: color 0.3s;">
              ${state.longest}
            </div>
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Next Permutation (DOM) ============== */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Next Permutation', short: 'Next Permutation',
  idea: '1. Scan from right to find first decreasing element `nums[i]`.<br/>2. Scan right to find element just larger than `nums[i]` and swap.<br/>3. Reverse the suffix from `i+1` onwards to make it as small as possible.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 1, 8, 7, 6, 5', hint: 'comma-separated array',
  code: [
    'def nextPermutation(nums):',
    '    i = len(nums) - 2',
    '    while i >= 0 and nums[i] >= nums[i + 1]:',
    '        i -= 1',
    '    if i >= 0:',
    '        j = len(nums) - 1',
    '        while nums[j] <= nums[i]:',
    '            j -= 1',
    '        nums[i], nums[j] = nums[j], nums[i]',
    '    ',
    '    nums[i + 1:] = reversed(nums[i + 1:])'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let arr = [...nums];
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], i: -1, j: -1, phase: 'init',
      explTitle: 'Initialization',
      explText: `We want to find the next lexicographical permutation.`
    }, ctx);

    // Step 1: Find first decreasing
    let i = arr.length - 2;
    while (i >= 0) {
      domPushState(seq, {
        kind: 'find_i', line: 3, color: 'blue',
        nums: [...arr], i, j: -1, phase: 'find_i',
        explTitle: `Step 1: Find Decreasing`,
        explText: `Check if ${arr[i]} < ${arr[i+1]}`
      }, ctx);

      if (arr[i] < arr[i + 1]) {
        domPushState(seq, {
          kind: 'found_i', line: 4, color: 'emerald',
          nums: [...arr], i, j: -1, phase: 'found_i',
          explTitle: `Pivot Found!`,
          explText: `${arr[i]} is smaller than ${arr[i+1]}. Pivot is at index ${i}.`
        }, ctx);
        break;
      }
      i--;
    }

    if (i >= 0) {
      // Step 2: Find just larger
      let j = arr.length - 1;
      while (j >= 0 && arr[j] <= arr[i]) {
        domPushState(seq, {
          kind: 'find_j', line: 7, color: 'amber',
          nums: [...arr], i, j, phase: 'find_j',
          explTitle: `Step 2: Find Just Larger`,
          explText: `Check if ${arr[j]} > pivot (${arr[i]}).`
        }, ctx);
        j--;
      }

      domPushState(seq, {
        kind: 'found_j', line: 8, color: 'emerald',
        nums: [...arr], i, j, phase: 'found_j',
        explTitle: `Swap Target Found`,
        explText: `${arr[j]} is the smallest number greater than ${arr[i]} in the suffix.`
      }, ctx);

      // Swap
      [arr[i], arr[j]] = [arr[j], arr[i]];
      domPushState(seq, {
        kind: 'swap', line: 9, color: 'emerald',
        nums: [...arr], i, j, phase: 'swap',
        explTitle: `Swap`,
        explText: `Swapped nums[${i}] and nums[${j}].`
      }, ctx);
    } else {
      domPushState(seq, {
        kind: 'no_pivot', line: 5, color: 'red',
        nums: [...arr], i: -1, j: -1, phase: 'no_pivot',
        explTitle: `No Pivot`,
        explText: `Array is strictly decreasing. It's the highest permutation.`
      }, ctx);
    }

    // Step 3: Reverse suffix
    domPushState(seq, {
      kind: 'reverse_init', line: 11, color: 'blue',
      nums: [...arr], i, j: -1, phase: 'reverse_init',
      explTitle: `Step 3: Reverse Suffix`,
      explText: `Reverse elements from index ${i+1} to end.`
    }, ctx);

    let left = i + 1;
    let right = arr.length - 1;
    while (left < right) {
      domPushState(seq, {
        kind: 'reverse_swap', line: 11, color: 'amber',
        nums: [...arr], i, left, right, phase: 'reverse_swap',
        explTitle: `Swap Suffix`,
        explText: `Swap ${arr[left]} and ${arr[right]}.`
      }, ctx);

      [arr[left], arr[right]] = [arr[right], arr[left]];
      
      domPushState(seq, {
        kind: 'reverse_done_swap', line: 11, color: 'emerald',
        nums: [...arr], i, left, right, phase: 'reverse_swap',
        explTitle: `Swapped`,
        explText: `Swapped.`
      }, ctx);
      
      left++;
      right--;
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums: [...arr], i: -1, j: -1, phase: 'done',
      explTitle: `Done`,
      explText: `Next permutation is complete.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const isReverse = state.phase.startsWith('reverse');

    const numsHTML = state.nums.map((v, idx) => {
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let boxsh = '';
      
      let isI = idx === state.i && !isReverse;
      let isJ = idx === state.j && !isReverse;
      
      let isL = isReverse && idx === state.left;
      let isR = isReverse && idx === state.right;
      
      if (isI) { bg = 'rgba(56,189,248,0.3)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      if (isJ) { bg = 'rgba(251,191,36,0.3)'; border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      
      if (state.phase === 'swap' && (isI || isJ)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;';
      }

      if (isL || isR) {
        bg = 'rgba(251,191,36,0.3)'; border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;';
      }

      if (isReverse && idx > state.i && !isL && !isR) {
        bg = 'rgba(255,255,255,0.05)'; // subtle highlight for suffix
      }
      
      if (state.phase === 'done') {
        bg = 'rgba(52,211,153,0.1)'; border = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 8px; font-weight: bold; font-size:18px;
            ${isI || isJ || isL || isR ? `transform: scale(1.1); ${boxsh} z-index:2;` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isI ? '<div style="position:absolute; bottom:-20px; color:#38bdf8; font-size:12px; font-weight:bold;">i</div>' : ''}
          ${isJ ? '<div style="position:absolute; bottom:-20px; color:#fbbf24; font-size:12px; font-weight:bold;">j</div>' : ''}
          ${isL ? '<div style="position:absolute; bottom:-20px; color:#fbbf24; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-20px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array</div>
          <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 01 · Isomorphic Strings (DOM) ============ */
defineAlgoDom('01_arrays_hashing', {
  type: 'dom',
  title: 'Isomorphic Strings', short: 'Isomorphic',
  idea: 'We need to make sure mappings are 1-to-1. We can maintain two Hash Maps: <code>mapST</code> maps chars from S to T, and <code>mapTS</code> maps chars from T to S. If we see a contradiction, return False.',
  complexity: 'Time O(N) · Space O(N)',
  input: 'egg ; add', hint: 'string s ; string t',
  code: [
    'def isIsomorphic(s, t):',
    '    mapST, mapTS = {}, {}',
    '',
    '    for c1, c2 in zip(s, t):',
    '        if ((c1 in mapST and mapST[c1] != c2) or',
    '            (c2 in mapTS and mapTS[c2] != c1)):',
    '            return False',
    '        mapST[c1] = c2',
    '        mapTS[c2] = c1',
    '',
    '    return True'
  ],
  parse(str) {
    const parts = str.split(';');
    return { s: (parts[0] || '').trim(), t: (parts[1] || '').trim() };
  },
  buildStates({ s, t }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = Math.min(s.length, t.length);
    let mapST = {};
    let mapTS = {};

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, t, mapST: {...mapST}, mapTS: {...mapTS}, phase: 'init', i: -1, valid: true,
      explTitle: 'Initialization',
      explText: `Create two Hash Maps to track character mappings both ways.`
    }, ctx);

    for (let i = 0; i < n; i++) {
      const c1 = s[i];
      const c2 = t[i];

      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        s, t, mapST: {...mapST}, mapTS: {...mapTS}, phase: 'visit', i, valid: true,
        explTitle: `Check Pair [${c1}, ${c2}]`,
        explText: `Does ${c1} already map to something else? Does ${c2} map to something else?`
      }, ctx);

      if ((mapST[c1] && mapST[c1] !== c2) || (mapTS[c2] && mapTS[c2] !== c1)) {
        domPushState(seq, {
          kind: 'invalid', line: 6, color: 'red',
          s, t, mapST: {...mapST}, mapTS: {...mapTS}, phase: 'invalid', i, valid: false,
          explTitle: `Contradiction!`,
          explText: `Mapping breaks! Either ${c1} -> ${mapST[c1]} instead of ${c2}, OR ${c2} -> ${mapTS[c2]} instead of ${c1}.`
        }, ctx);
        return seq;
      }

      mapST[c1] = c2;
      mapTS[c2] = c1;

      domPushState(seq, {
        kind: 'add', line: 8, color: 'emerald',
        s, t, mapST: {...mapST}, mapTS: {...mapTS}, phase: 'add', i, valid: true,
        explTitle: `Valid Mapping`,
        explText: `Map ${c1} -> ${c2} and ${c2} -> ${c1}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      s, t, mapST: {...mapST}, mapTS: {...mapTS}, phase: 'done', i: -1, valid: true,
      explTitle: `Done`,
      explText: `All mappings are valid. Strings are isomorphic!`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const sHTML = state.s.split('').map((char, idx) => {
      let isCur = state.i === idx;
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      if (isCur && state.phase === 'invalid') { bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; }
      if (isCur && state.phase === 'add') { bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; }

      return `<div style="width:30px; height:35px; border:1px solid ${border}; background:${bg}; display:flex; align-items:center; justify-content:center; font-family:monospace; font-weight:bold; font-size:18px; border-radius:4px; ${isCur ? 'transform:scale(1.1);' : ''} transition:all 0.3s;">${char}</div>`;
    }).join('');

    const tHTML = state.t.split('').map((char, idx) => {
      let isCur = state.i === idx;
      let bg = isCur ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
      let border = isCur ? '#38bdf8' : 'var(--border)';
      if (isCur && state.phase === 'invalid') { bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; }
      if (isCur && state.phase === 'add') { bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; }

      return `<div style="width:30px; height:35px; border:1px solid ${border}; background:${bg}; display:flex; align-items:center; justify-content:center; font-family:monospace; font-weight:bold; font-size:18px; border-radius:4px; ${isCur ? 'transform:scale(1.1);' : ''} transition:all 0.3s;">${char}</div>`;
    }).join('');

    const stMapHTML = Object.entries(state.mapST).map(([k, v]) => `
      <div style="padding:4px 8px; background:rgba(255,255,255,0.05); border-radius:4px; font-family:monospace; color:#fbbf24; border: 1px solid var(--border);">
        ${k} &rarr; ${v}
      </div>
    `).join('');

    const tsMapHTML = Object.entries(state.mapTS).map(([k, v]) => `
      <div style="padding:4px 8px; background:rgba(255,255,255,0.05); border-radius:4px; font-family:monospace; color:#38bdf8; border: 1px solid var(--border);">
        ${k} &rarr; ${v}
      </div>
    `).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 15px; color: var(--accent);">Strings</div>
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            <div style="color:var(--text-dim); font-size:12px; width:10px;">s</div>
            <div style="display:flex; gap:5px;">${sHTML}</div>
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="color:var(--text-dim); font-size:12px; width:10px;">t</div>
            <div style="display:flex; gap:5px;">${tHTML}</div>
          </div>
        </div>
        
        <div style="display:flex; width:100%; gap:20px; max-width:600px;">
          <div class="glass-panel" style="flex:1; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: #fbbf24;">mapST (S &rarr; T)</div>
            <div style="display:flex; flex-direction:column; gap:5px; width:100%; min-height:80px;">
              ${stMapHTML || '<span style="color:var(--text-dim); font-style:italic; align-self:center;">Empty</span>'}
            </div>
          </div>
          <div class="glass-panel" style="flex:1; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <div class="panel-heading" style="margin-bottom: 15px; color: #38bdf8;">mapTS (T &rarr; S)</div>
            <div style="display:flex; flex-direction:column; gap:5px; width:100%; min-height:80px;">
              ${tsMapHTML || '<span style="color:var(--text-dim); font-style:italic; align-self:center;">Empty</span>'}
            </div>
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Valid Palindrome (DOM) ============== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Valid Palindrome', short: 'Valid Palindrome',
  idea: 'We can use two pointers (<code>L</code> from start, <code>R</code> from end). We skip non-alphanumeric characters. If the characters at <code>L</code> and <code>R</code> don\'t match (case-insensitive), it\'s not a palindrome. Otherwise, we move both inward.',
  complexity: 'Time O(N) · Space O(1)',
  input: 'A man, a plan, a canal: Panama', hint: 'string',
  code: [
    'def isPalindrome(s):',
    '    l, r = 0, len(s) - 1',
    '    while l < r:',
    '        while l < r and not s[l].isalnum():',
    '            l += 1',
    '        while l < r and not s[r].isalnum():',
    '            r -= 1',
    '        if s[l].lower() != s[r].lower():',
    '            return False',
    '        l += 1',
    '        r -= 1',
    '    return True'
  ],
  parse(str) {
    return { s: str.trim() };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let l = 0, r = s.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, l, r, phase: 'init', valid: true,
      explTitle: 'Initialization',
      explText: `Set L to start, R to end.`
    }, ctx);

    const isAlnum = (ch) => /^[a-z0-9]+$/i.test(ch);

    while (l < r) {
      while (l < r && !isAlnum(s[l])) {
        domPushState(seq, {
          kind: 'skip_l', line: 5, color: 'amber',
          s, l, r, phase: 'skip', valid: true,
          explTitle: `Skip Non-Alphanumeric`,
          explText: `'${s[l]}' is not alphanumeric. Move L right.`
        }, ctx);
        l++;
      }
      
      while (l < r && !isAlnum(s[r])) {
        domPushState(seq, {
          kind: 'skip_r', line: 7, color: 'amber',
          s, l, r, phase: 'skip', valid: true,
          explTitle: `Skip Non-Alphanumeric`,
          explText: `'${s[r]}' is not alphanumeric. Move R left.`
        }, ctx);
        r--;
      }

      if (l >= r) break;

      const cl = s[l].toLowerCase();
      const cr = s[r].toLowerCase();

      domPushState(seq, {
        kind: 'compare', line: 8, color: 'blue',
        s, l, r, phase: 'compare', valid: true,
        explTitle: `Compare Characters`,
        explText: `Compare '${cl}' and '${cr}'.`
      }, ctx);

      if (cl !== cr) {
        domPushState(seq, {
          kind: 'mismatch', line: 9, color: 'red',
          s, l, r, phase: 'invalid', valid: false,
          explTitle: `Mismatch!`,
          explText: `'${cl}' != '${cr}'. Not a palindrome.`
        }, ctx);
        return seq;
      }

      domPushState(seq, {
        kind: 'match', line: 10, color: 'emerald',
        s, l, r, phase: 'match', valid: true,
        explTitle: `Match!`,
        explText: `'${cl}' == '${cr}'. Move both pointers inward.`
      }, ctx);

      l++;
      r--;
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'emerald',
      s, l, r, phase: 'done', valid: true,
      explTitle: `Done`,
      explText: `All characters matched. String is a valid palindrome!`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const charsHTML = state.s.split('').map((char, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      
      let bg = 'var(--surface)';
      let border = 'transparent';
      let color = 'var(--text)';
      let boxsh = '';

      if (isL) { border = '#38bdf8'; bg = 'rgba(56,189,248,0.2)'; }
      if (isR) { border = '#fbbf24'; bg = 'rgba(251,191,36,0.2)'; }
      if (isL && isR) { border = '#a855f7'; bg = 'rgba(168,85,247,0.2)'; } // Meet in middle

      if (state.phase === 'compare' && (isL || isR)) {
        boxsh = `box-shadow: 0 0 10px ${border};`;
      }
      
      if (state.phase === 'invalid' && (isL || isR)) {
        bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
        boxsh = 'box-shadow: 0 0 15px #f43f5e;';
      }
      
      if (state.phase === 'match' && (isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; color = '#34d399';
        boxsh = 'box-shadow: 0 0 15px #34d399;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="
            width: 25px; height: 35px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border-bottom: 2px solid ${border}; font-weight: bold; font-size:20px; font-family:monospace; color:${color};
            ${isL || isR ? `transform: scale(1.1); ${boxsh}` : ''}
            transition: all 0.3s;
          ">${char === ' ' ? '&nbsp;' : char}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 20px; color: var(--accent);">String</div>
          <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:2px;">
            ${charsHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Valid Palindrome II (DOM) =========== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Valid Palindrome II', short: 'Valid Palindrome II',
  idea: 'Like Valid Palindrome, but we can delete AT MOST one character. When we find a mismatch <code>s[L] != s[R]</code>, we split into two cases: either delete <code>s[L]</code> and check if the rest is a palindrome, OR delete <code>s[R]</code> and check.',
  complexity: 'Time O(N) · Space O(N) (or O(1) iterative)',
  input: 'abca', hint: 'string',
  code: [
    'def validPalindrome(s):',
    '    l, r = 0, len(s) - 1',
    '    while l < r:',
    '        if s[l] != s[r]:',
    '            skipL = s[l + 1:r + 1]',
    '            skipR = s[l:r]',
    '            return skipL == skipL[::-1] or skipR == skipR[::-1]',
    '        l += 1',
    '        r -= 1',
    '    return True'
  ],
  parse(str) {
    return { s: str.trim() };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let l = 0, r = s.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, l, r, phase: 'init',
      explTitle: 'Initialization',
      explText: `Set L to start, R to end.`
    }, ctx);

    while (l < r) {
      domPushState(seq, {
        kind: 'compare', line: 4, color: 'blue',
        s, l, r, phase: 'compare',
        explTitle: `Compare Characters`,
        explText: `Compare '${s[l]}' and '${s[r]}'.`
      }, ctx);

      if (s[l] !== s[r]) {
        domPushState(seq, {
          kind: 'mismatch', line: 5, color: 'amber',
          s, l, r, phase: 'mismatch',
          explTitle: `Mismatch Found!`,
          explText: `'${s[l]}' != '${s[r]}'. We must use our 1 deletion here.`
        }, ctx);

        let skipL = s.substring(l + 1, r + 1);
        let skipR = s.substring(l, r);
        let lPal = skipL === skipL.split('').reverse().join('');
        let rPal = skipR === skipR.split('').reverse().join('');

        domPushState(seq, {
          kind: 'split', line: 7, color: 'amber',
          s, l, r, phase: 'split', skipL, skipR, lPal, rPal,
          explTitle: `Try Deletions`,
          explText: `Check if deleting L gives a palindrome ("${skipL}") OR deleting R gives a palindrome ("${skipR}").`
        }, ctx);
        
        let valid = lPal || rPal;
        domPushState(seq, {
          kind: 'done', line: 7, color: valid ? 'emerald' : 'red',
          s, l, r, phase: 'done', valid, skipL, skipR, lPal, rPal,
          explTitle: valid ? `Valid!` : `Invalid!`,
          explText: valid ? `One of the substrings is a palindrome.` : `Neither substring is a palindrome.`
        }, ctx);
        return seq;
      }

      domPushState(seq, {
        kind: 'match', line: 8, color: 'emerald',
        s, l, r, phase: 'match',
        explTitle: `Match!`,
        explText: `'${s[l]}' == '${s[r]}'. Move both inward.`
      }, ctx);

      l++;
      r--;
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      s, l, r, phase: 'done', valid: true,
      explTitle: `Done`,
      explText: `It's already a perfect palindrome!`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const charsHTML = state.s.split('').map((char, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      
      let bg = 'var(--surface)';
      let border = 'transparent';
      let color = 'var(--text)';
      let boxsh = '';

      if (isL) { border = '#38bdf8'; bg = 'rgba(56,189,248,0.2)'; }
      if (isR) { border = '#fbbf24'; bg = 'rgba(251,191,36,0.2)'; }

      if (state.phase === 'compare' && (isL || isR)) {
        boxsh = `box-shadow: 0 0 10px ${border};`;
      }
      
      if (state.phase === 'mismatch' && (isL || isR)) {
        bg = 'rgba(251,191,36,0.3)'; border = '#fbbf24'; color = '#fbbf24';
        boxsh = 'box-shadow: 0 0 15px #fbbf24;';
      }
      
      if (state.phase === 'match' && (isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; color = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="
            width: 30px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border-bottom: 2px solid ${border}; font-weight: bold; font-size:20px; font-family:monospace; color:${color};
            ${isL || isR ? `transform: scale(1.1); ${boxsh}` : ''}
            transition: all 0.3s;
          ">${char}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    let splitHTML = '';
    if (state.phase === 'split' || state.phase === 'done') {
      if (state.skipL !== undefined) {
        splitHTML = `
          <div style="display:flex; width:100%; gap:20px; margin-top:20px; justify-content:center;">
            <div class="glass-panel" style="padding: 15px; display:flex; flex-direction:column; align-items:center; ${state.lPal ? 'border-color:#34d399;' : 'border-color:#f43f5e;'}">
              <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Delete L</div>
              <div style="font-family:monospace; font-size:18px; color:${state.lPal ? '#34d399' : '#f43f5e'};">"${state.skipL}"</div>
              <div style="font-size:12px; margin-top:5px; color:${state.lPal ? '#34d399' : '#f43f5e'};">${state.lPal ? 'Is Palindrome' : 'Not Palindrome'}</div>
            </div>
            <div class="glass-panel" style="padding: 15px; display:flex; flex-direction:column; align-items:center; ${state.rPal ? 'border-color:#34d399;' : 'border-color:#f43f5e;'}">
              <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Delete R</div>
              <div style="font-family:monospace; font-size:18px; color:${state.rPal ? '#34d399' : '#f43f5e'};">"${state.skipR}"</div>
              <div style="font-size:12px; margin-top:5px; color:${state.rPal ? '#34d399' : '#f43f5e'};">${state.rPal ? 'Is Palindrome' : 'Not Palindrome'}</div>
            </div>
          </div>
        `;
      }
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 20px; color: var(--accent);">String</div>
          <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:5px;">
            ${charsHTML}
          </div>
          ${splitHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Remove Duplicates (DOM) ============= */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Remove Duplicates from Sorted Array', short: 'Remove Dups',
  idea: 'We use a slow pointer <code>L</code> to indicate where the next unique element should go, and a fast pointer <code>R</code> to scan for new unique elements.',
  complexity: 'Time O(N) · Space O(1)',
  input: '0, 0, 1, 1, 1, 2, 2, 3, 3, 4', hint: 'comma-separated sorted array',
  code: [
    'def removeDuplicates(nums):',
    '    l = 1',
    '    for r in range(1, len(nums)):',
    '        if nums[r] != nums[r - 1]:',
    '            nums[l] = nums[r]',
    '            l += 1',
    '    return l'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums];
    let l = 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], l, r: 1, phase: 'init',
      explTitle: 'Initialization',
      explText: `L starts at 1, R starts at 1. The first element is trivially unique.`
    }, ctx);

    for (let r = 1; r < arr.length; r++) {
      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        nums: [...arr], l, r, phase: 'compare',
        explTitle: `Check R (${arr[r]})`,
        explText: `Is nums[R] (${arr[r]}) different from nums[R-1] (${arr[r-1]})?`
      }, ctx);

      if (arr[r] !== arr[r - 1]) {
        domPushState(seq, {
          kind: 'new_unique', line: 5, color: 'emerald',
          nums: [...arr], l, r, phase: 'copy',
          explTitle: `New Unique Element!`,
          explText: `Found ${arr[r]}. Copy it to index L (${l}).`
        }, ctx);
        
        arr[l] = arr[r];
        
        domPushState(seq, {
          kind: 'increment', line: 6, color: 'amber',
          nums: [...arr], l, r, phase: 'inc',
          explTitle: `Increment L`,
          explText: `Increment L to ${l + 1} for the next unique element.`
        }, ctx);
        
        l++;
      } else {
        domPushState(seq, {
          kind: 'skip', line: 3, color: 'amber',
          nums: [...arr], l, r, phase: 'skip',
          explTitle: `Duplicate Found`,
          explText: `${arr[r]} is a duplicate. R continues scanning.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 7, color: 'emerald',
      nums: [...arr], l, r: -1, phase: 'done',
      explTitle: `Done`,
      explText: `Return L (${l}) which represents the number of unique elements.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l && state.phase !== 'done';
      let isR = idx === state.r;
      let isUniqueRegion = idx < state.l;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';

      if (isUniqueRegion) {
        bg = 'rgba(52,211,153,0.1)'; border = '#34d399';
      }

      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      if (isL && isR) { border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; }
      
      if (state.phase === 'copy' && isL) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Green region is unique prefix)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Remove Element (DOM) ================ */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Remove Element', short: 'Remove Elem',
  idea: 'We use a slow pointer <code>L</code> to indicate where the next valid element should go. The fast pointer <code>R</code> scans the array. If <code>nums[R] != val</code>, we copy it to <code>nums[L]</code> and increment <code>L</code>.',
  complexity: 'Time O(N) · Space O(1)',
  input: '3, 2, 2, 3 ; 3', hint: 'array ; val',
  code: [
    'def removeElement(nums, val):',
    '    l = 0',
    '    for r in range(len(nums)):',
    '        if nums[r] != val:',
    '            nums[l] = nums[r]',
    '            l += 1',
    '    return l'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), val: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, val }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums];
    let l = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], l, r: 0, val, phase: 'init',
      explTitle: 'Initialization',
      explText: `We want to remove all occurrences of ${val}. L starts at 0.`
    }, ctx);

    for (let r = 0; r < arr.length; r++) {
      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        nums: [...arr], l, r, val, phase: 'compare',
        explTitle: `Check R (${arr[r]})`,
        explText: `Is nums[R] (${arr[r]}) != val (${val})?`
      }, ctx);

      if (arr[r] !== val) {
        domPushState(seq, {
          kind: 'valid', line: 5, color: 'emerald',
          nums: [...arr], l, r, val, phase: 'copy',
          explTitle: `Valid Element!`,
          explText: `${arr[r]} is not ${val}. Copy it to index L (${l}).`
        }, ctx);
        
        arr[l] = arr[r];
        
        domPushState(seq, {
          kind: 'increment', line: 6, color: 'amber',
          nums: [...arr], l, r, val, phase: 'inc',
          explTitle: `Increment L`,
          explText: `Increment L to ${l + 1} for the next valid element.`
        }, ctx);
        
        l++;
      } else {
        domPushState(seq, {
          kind: 'skip', line: 3, color: 'red',
          nums: [...arr], l, r, val, phase: 'skip',
          explTitle: `Target Found`,
          explText: `${arr[r]} == ${val}. We ignore it. R continues scanning.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 7, color: 'emerald',
      nums: [...arr], l, r: -1, val, phase: 'done',
      explTitle: `Done`,
      explText: `Return L (${l}) which represents the number of valid elements.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l && state.phase !== 'done';
      let isR = idx === state.r;
      let isValidRegion = idx < state.l;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';

      if (isValidRegion) {
        bg = 'rgba(52,211,153,0.1)'; border = '#34d399';
      }

      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      if (isL && isR) { border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; }
      
      if (state.phase === 'copy' && isL) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      if (state.phase === 'skip' && isR) {
        bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Target val = <span style="color:#f43f5e;">${state.val}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Move Zeroes (DOM) =================== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Move Zeroes', short: 'Move Zeroes',
  idea: 'We use a slow pointer <code>L</code> to indicate the position of the first zero. A fast pointer <code>R</code> scans for non-zeroes. When <code>R</code> finds a non-zero, we swap <code>nums[L]</code> and <code>nums[R]</code>.',
  complexity: 'Time O(N) · Space O(1)',
  input: '0, 1, 0, 3, 12', hint: 'comma-separated array',
  code: [
    'def moveZeroes(nums):',
    '    l = 0',
    '    for r in range(len(nums)):',
    '        if nums[r]:',
    '            nums[l], nums[r] = nums[r], nums[l]',
    '            l += 1'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums];
    let l = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], l, r: 0, phase: 'init',
      explTitle: 'Initialization',
      explText: `L starts at 0. It will track the leftmost zero.`
    }, ctx);

    for (let r = 0; r < arr.length; r++) {
      domPushState(seq, {
        kind: 'visit', line: 4, color: 'blue',
        nums: [...arr], l, r, phase: 'compare',
        explTitle: `Check R (${arr[r]})`,
        explText: `Is nums[R] (${arr[r]}) != 0?`
      }, ctx);

      if (arr[r] !== 0) {
        domPushState(seq, {
          kind: 'swap_start', line: 5, color: 'emerald',
          nums: [...arr], l, r, phase: 'swap',
          explTitle: `Non-Zero Found!`,
          explText: `Swap nums[L] (${arr[l]}) and nums[R] (${arr[r]}).`
        }, ctx);
        
        let temp = arr[l];
        arr[l] = arr[r];
        arr[r] = temp;
        
        domPushState(seq, {
          kind: 'increment', line: 6, color: 'amber',
          nums: [...arr], l, r, phase: 'inc',
          explTitle: `Increment L`,
          explText: `Increment L to ${l + 1}.`
        }, ctx);
        
        l++;
      } else {
        domPushState(seq, {
          kind: 'skip', line: 3, color: 'red',
          nums: [...arr], l, r, phase: 'skip',
          explTitle: `Zero Found`,
          explText: `nums[R] is 0. R continues scanning.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 6, color: 'emerald',
      nums: [...arr], l, r: -1, phase: 'done',
      explTitle: `Done`,
      explText: `All zeroes have been moved to the end.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l && state.phase !== 'done';
      let isR = idx === state.r;
      let isZero = v === 0;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';

      if (isZero && state.phase === 'done') {
        color = 'var(--text-dim)';
        bg = 'rgba(255,255,255,0.02)';
      }

      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      if (isL && isR) { border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; }
      
      if (state.phase === 'swap' && (isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Two Sum II (DOM) ==================== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Two Sum II - Input Array Is Sorted', short: 'Two Sum II',
  idea: 'Because the array is sorted, we can put <code>L</code> at the start and <code>R</code> at the end. If <code>sum > target</code>, the sum is too big, so we decrease <code>R</code>. If <code>sum < target</code>, the sum is too small, so we increase <code>L</code>.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 7, 11, 15 ; 9', hint: 'sorted array ; target',
  code: [
    'def twoSum(numbers, target):',
    '    l, r = 0, len(numbers) - 1',
    '    while l < r:',
    '        curSum = numbers[l] + numbers[r]',
    '        if curSum > target:',
    '            r -= 1',
    '        elif curSum < target:',
    '            l += 1',
    '        else:',
    '            return [l + 1, r + 1]'
  ],
  parse(str) {
    const p = str.split(';');
    return { numbers: avArr(p[0]), target: parseInt(p[1] || '0', 10) };
  },
  buildStates({ numbers, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let l = 0;
    let r = numbers.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      numbers, l, r, target, phase: 'init', sum: null,
      explTitle: 'Initialization',
      explText: `Array is sorted. L starts at left (smallest), R starts at right (largest).`
    }, ctx);

    while (l < r) {
      let sum = numbers[l] + numbers[r];
      domPushState(seq, {
        kind: 'sum', line: 4, color: 'blue',
        numbers, l, r, target, phase: 'sum', sum,
        explTitle: `Calculate Sum`,
        explText: `sum = ${numbers[l]} + ${numbers[r]} = ${sum}. Target is ${target}.`
      }, ctx);

      if (sum > target) {
        domPushState(seq, {
          kind: 'decrease_r', line: 6, color: 'amber',
          numbers, l, r, target, phase: 'dec_r', sum,
          explTitle: `Sum is Too Big`,
          explText: `${sum} > ${target}. We need a smaller sum. Move R left.`
        }, ctx);
        r--;
      } else if (sum < target) {
        domPushState(seq, {
          kind: 'increase_l', line: 8, color: 'amber',
          numbers, l, r, target, phase: 'inc_l', sum,
          explTitle: `Sum is Too Small`,
          explText: `${sum} < ${target}. We need a larger sum. Move L right.`
        }, ctx);
        l++;
      } else {
        domPushState(seq, {
          kind: 'found', line: 10, color: 'emerald',
          numbers, l, r, target, phase: 'found', sum,
          explTitle: `Target Found!`,
          explText: `${sum} == ${target}. Return [${l + 1}, ${r + 1}].`
        }, ctx);
        return seq;
      }
    }

    domPushState(seq, {
      kind: 'not_found', line: 10, color: 'red',
      numbers, l, r, target, phase: 'not_found', sum: null,
      explTitle: `Not Found`,
      explText: `No valid pair exists.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.numbers.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';

      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      
      if (state.phase === 'found' && (isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isL ? '<div style="position:absolute; bottom:-18px; color:#38bdf8; font-size:12px; font-weight:bold;">L</div>' : ''}
          ${isR ? '<div style="position:absolute; bottom:-18px; color:#fbbf24; font-size:12px; font-weight:bold;">R</div>' : ''}
        </div>
      `;
    }).join('');

    let eqColor = 'var(--text)';
    if (state.phase === 'found') eqColor = '#34d399';
    if (state.phase === 'dec_r') eqColor = '#f43f5e';
    if (state.phase === 'inc_l') eqColor = '#38bdf8';

    let sumHTML = '';
    if (state.sum !== null) {
      let sign = '==';
      if (state.sum > state.target) sign = '&gt;';
      if (state.sum < state.target) sign = '&lt;';

      sumHTML = `
        <div style="display:flex; align-items:center; gap:15px; margin-top:20px; font-size:24px; font-family:monospace; background:rgba(255,255,255,0.05); padding:10px 20px; border-radius:8px; border:1px solid var(--border);">
          <span style="color:#38bdf8">${state.numbers[state.l]}</span> + <span style="color:#fbbf24">${state.numbers[state.r]}</span> 
          = <strong style="color:${eqColor}">${state.sum}</strong> <span style="color:${eqColor}">${sign}</span> <strong>${state.target}</strong>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted Array (Target = <span style="color:#a855f7;">${state.target}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
          ${sumHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · 3Sum (DOM) ========================== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: '3Sum', short: '3Sum',
  idea: 'Sort the array. Iterate with <code>i</code>. For each <code>i</code>, use two pointers <code>L</code> and <code>R</code> to find pairs that sum to <code>-nums[i]</code>. Skip duplicates to avoid duplicate triplets.',
  complexity: 'Time O(N²) · Space O(1) or O(N) depending on sorting',
  input: '-1, 0, 1, 2, -1, -4', hint: 'comma-separated array',
  code: [
    'def threeSum(nums):',
    '    res = []',
    '    nums.sort()',
    '    for i, a in enumerate(nums):',
    '        if i > 0 and a == nums[i - 1]:',
    '            continue',
    '        l, r = i + 1, len(nums) - 1',
    '        while l < r:',
    '            threeSum = a + nums[l] + nums[r]',
    '            if threeSum > 0:',
    '                r -= 1',
    '            elif threeSum < 0:',
    '                l += 1',
    '            else:',
    '                res.append([a, nums[l], nums[r]])',
    '                l += 1',
    '                while nums[l] == nums[l - 1] and l < r:',
    '                    l += 1',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums].sort((a, b) => a - b);
    const res = [];

    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      nums: [...arr], i: -1, l: -1, r: -1, phase: 'init', sum: null, res: [...res],
      explTitle: 'Initialization',
      explText: `First, we sort the array to easily use the two pointer approach.`
    }, ctx);

    for (let i = 0; i < arr.length; i++) {
      domPushState(seq, {
        kind: 'i_start', line: 4, color: 'blue',
        nums: [...arr], i, l: -1, r: -1, phase: 'i_start', sum: null, res: [...res],
        explTitle: `Loop i = ${i}`,
        explText: `We fix nums[${i}] = ${arr[i]} and search for a pair that sums to ${-arr[i]}.`
      }, ctx);

      if (i > 0 && arr[i] === arr[i - 1]) {
        domPushState(seq, {
          kind: 'i_skip', line: 6, color: 'red',
          nums: [...arr], i, l: -1, r: -1, phase: 'i_skip', sum: null, res: [...res],
          explTitle: `Skip Duplicate i`,
          explText: `${arr[i]} == ${arr[i-1]}. We skip to avoid duplicate triplets.`
        }, ctx);
        continue;
      }

      let l = i + 1;
      let r = arr.length - 1;

      domPushState(seq, {
        kind: 'ptr_init', line: 7, color: 'blue',
        nums: [...arr], i, l, r, phase: 'ptr_init', sum: null, res: [...res],
        explTitle: `Initialize L and R`,
        explText: `L starts at ${l}, R starts at ${r}.`
      }, ctx);

      while (l < r) {
        let sum = arr[i] + arr[l] + arr[r];
        domPushState(seq, {
          kind: 'sum', line: 9, color: 'blue',
          nums: [...arr], i, l, r, phase: 'sum', sum, res: [...res],
          explTitle: `Calculate Sum`,
          explText: `${arr[i]} + ${arr[l]} + ${arr[r]} = ${sum}. Target is 0.`
        }, ctx);

        if (sum > 0) {
          domPushState(seq, {
            kind: 'decrease_r', line: 11, color: 'amber',
            nums: [...arr], i, l, r, phase: 'dec_r', sum, res: [...res],
            explTitle: `Sum is Too Big`,
            explText: `${sum} > 0. Move R left.`
          }, ctx);
          r--;
        } else if (sum < 0) {
          domPushState(seq, {
            kind: 'increase_l', line: 13, color: 'amber',
            nums: [...arr], i, l, r, phase: 'inc_l', sum, res: [...res],
            explTitle: `Sum is Too Small`,
            explText: `${sum} < 0. Move L right.`
          }, ctx);
          l++;
        } else {
          res.push(`[${arr[i]}, ${arr[l]}, ${arr[r]}]`);
          domPushState(seq, {
            kind: 'found', line: 15, color: 'emerald',
            nums: [...arr], i, l, r, phase: 'found', sum, res: [...res],
            explTitle: `Triplet Found!`,
            explText: `${sum} == 0. Add [${arr[i]}, ${arr[l]}, ${arr[r]}] to results.`
          }, ctx);
          
          l++;
          domPushState(seq, {
            kind: 'l_inc_found', line: 16, color: 'amber',
            nums: [...arr], i, l, r, phase: 'l_inc_found', sum: null, res: [...res],
            explTitle: `Increment L`,
            explText: `Move L right to find other potential pairs.`
          }, ctx);

          while (arr[l] === arr[l - 1] && l < r) {
            domPushState(seq, {
              kind: 'l_skip', line: 18, color: 'amber',
              nums: [...arr], i, l, r, phase: 'l_skip', sum: null, res: [...res],
              explTitle: `Skip Duplicate L`,
              explText: `nums[L] is the same as previous. Move L right to avoid duplicate triplets.`
            }, ctx);
            l++;
          }
        }
      }
    }

    domPushState(seq, {
      kind: 'done', line: 19, color: 'emerald',
      nums: [...arr], i: -1, l: -1, r: -1, phase: 'done', sum: null, res: [...res],
      explTitle: `Done`,
      explText: `Found ${res.length} unique triplets.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isI = idx === state.i;
      let isL = idx === state.l;
      let isR = idx === state.r;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      let pt = [];
      if (isI) pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">i</div>');
      if (isL) pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR) pt.push('<div style="color:#fbbf24; font-size:12px; font-weight:bold;">R</div>');

      if (isI) { border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; }
      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      
      if (state.phase === 'found' && (isI || isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      if (state.phase === 'i_skip' && isI) {
        bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;'; color = '#f43f5e';
      }

      let bottomHTML = '';
      if (pt.length > 0) {
        bottomHTML = `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isI || isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');

    let eqColor = 'var(--text)';
    if (state.phase === 'found') eqColor = '#34d399';
    if (state.phase === 'dec_r') eqColor = '#f43f5e';
    if (state.phase === 'inc_l') eqColor = '#38bdf8';

    let sumHTML = '';
    if (state.sum !== null) {
      let sign = '==';
      if (state.sum > 0) sign = '&gt;';
      if (state.sum < 0) sign = '&lt;';

      sumHTML = `
        <div style="display:flex; align-items:center; gap:15px; margin-top:20px; font-size:24px; font-family:monospace; background:rgba(255,255,255,0.05); padding:10px 20px; border-radius:8px; border:1px solid var(--border);">
          <span style="color:#a855f7">${state.nums[state.i]}</span> + 
          <span style="color:#38bdf8">${state.nums[state.l]}</span> + 
          <span style="color:#fbbf24">${state.nums[state.r]}</span> 
          = <strong style="color:${eqColor}">${state.sum}</strong> <span style="color:${eqColor}">${sign}</span> <strong>0</strong>
        </div>
      `;
    }

    let resHTML = state.res.length > 0 
      ? `<div style="margin-top:20px; display:flex; flex-wrap:wrap; gap:10px; justify-content:center;">` + 
        state.res.map(r => `<span style="background:rgba(52,211,153,0.1); border:1px solid #34d399; padding:4px 8px; border-radius:4px; font-family:monospace;">${r}</span>`).join('') +
        `</div>`
      : `<div style="margin-top:20px; color:var(--text-dim); font-style:italic;">No triplets found yet.</div>`;

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
          ${sumHTML}
        </div>
        <div class="glass-panel" style="padding: 15px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Results (Triplets summing to 0)</div>
          ${resHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · 3Sum Closest (DOM) ================== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: '3Sum Closest', short: '3Sum Closest',
  idea: 'Sort array. Fix <code>i</code>, use <code>L</code> and <code>R</code>. Track the sum closest to <code>target</code>. Update closest when <code>abs(sum - target) < abs(closest - target)</code>.',
  complexity: 'Time O(N²) · Space O(1) or O(N)',
  input: '-1, 2, 1, -4 ; 1', hint: 'array ; target',
  code: [
    'def threeSumClosest(nums, target):',
    '    nums.sort()',
    '    res = sum(nums[:3])',
    '    for i in range(len(nums) - 2):',
    '        l, r = i + 1, len(nums) - 1',
    '        while l < r:',
    '            curSum = nums[i] + nums[l] + nums[r]',
    '            if abs(curSum - target) < abs(res - target):',
    '                res = curSum',
    '            if curSum < target:',
    '                l += 1',
    '            elif curSum > target:',
    '                r -= 1',
    '            else:',
    '                return res',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), target: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...nums].sort((a, b) => a - b);
    
    let res = arr[0] + arr[1] + arr[2];

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums: [...arr], target, i: -1, l: -1, r: -1, phase: 'init', sum: null, res,
      explTitle: 'Initialization',
      explText: `Sort array. Initial closest sum is sum of first 3 elements: ${res}.`
    }, ctx);

    for (let i = 0; i < arr.length - 2; i++) {
      let l = i + 1;
      let r = arr.length - 1;

      domPushState(seq, {
        kind: 'ptr_init', line: 4, color: 'blue',
        nums: [...arr], target, i, l, r, phase: 'ptr_init', sum: null, res,
        explTitle: `Loop i = ${i}`,
        explText: `Fix i at ${arr[i]}. L = ${l}, R = ${r}.`
      }, ctx);

      while (l < r) {
        let sum = arr[i] + arr[l] + arr[r];
        
        let diffNew = Math.abs(sum - target);
        let diffOld = Math.abs(res - target);
        
        let isBetter = diffNew < diffOld;
        
        domPushState(seq, {
          kind: 'sum', line: 7, color: 'blue',
          nums: [...arr], target, i, l, r, phase: 'sum', sum, res,
          diffNew, diffOld, isBetter,
          explTitle: `Calculate Sum`,
          explText: `${arr[i]} + ${arr[l]} + ${arr[r]} = ${sum}. Distance to target: ${diffNew}. Current best distance: ${diffOld}.`
        }, ctx);

        if (isBetter) {
          res = sum;
          domPushState(seq, {
            kind: 'update_res', line: 9, color: 'emerald',
            nums: [...arr], target, i, l, r, phase: 'update', sum, res,
            explTitle: `Update Closest`,
            explText: `${sum} is closer to ${target}! Update closest to ${res}.`
          }, ctx);
        }

        if (sum < target) {
          domPushState(seq, {
            kind: 'increase_l', line: 11, color: 'amber',
            nums: [...arr], target, i, l, r, phase: 'inc_l', sum, res,
            explTitle: `Sum is Too Small`,
            explText: `${sum} < ${target}. Move L right to increase sum.`
          }, ctx);
          l++;
        } else if (sum > target) {
          domPushState(seq, {
            kind: 'decrease_r', line: 13, color: 'amber',
            nums: [...arr], target, i, l, r, phase: 'dec_r', sum, res,
            explTitle: `Sum is Too Big`,
            explText: `${sum} > ${target}. Move R left to decrease sum.`
          }, ctx);
          r--;
        } else {
          domPushState(seq, {
            kind: 'exact_match', line: 15, color: 'emerald',
            nums: [...arr], target, i, l, r, phase: 'found', sum, res,
            explTitle: `Exact Match!`,
            explText: `${sum} == target! We can't get closer. Return ${res}.`
          }, ctx);
          return seq;
        }
      }
    }

    domPushState(seq, {
      kind: 'done', line: 16, color: 'emerald',
      nums: [...arr], target, i: -1, l: -1, r: -1, phase: 'done', sum: null, res,
      explTitle: `Done`,
      explText: `Return closest sum: ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isI = idx === state.i;
      let isL = idx === state.l;
      let isR = idx === state.r;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      let pt = [];
      if (isI) pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">i</div>');
      if (isL) pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR) pt.push('<div style="color:#fbbf24; font-size:12px; font-weight:bold;">R</div>');

      if (isI) { border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; }
      if (isR) { border = '#fbbf24'; boxsh = 'box-shadow: 0 0 10px #fbbf24;'; }
      if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
      
      if (state.phase === 'found' && (isI || isL || isR)) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      if (state.phase === 'update' && (isI || isL || isR)) {
        bg = 'rgba(52,211,153,0.15)'; border = '#34d399';
      }

      let bottomHTML = '';
      if (pt.length > 0) {
        bottomHTML = `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isI || isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');

    let eqColor = 'var(--text)';
    if (state.phase === 'found') eqColor = '#34d399';
    if (state.phase === 'dec_r') eqColor = '#f43f5e';
    if (state.phase === 'inc_l') eqColor = '#38bdf8';

    let sumHTML = '';
    if (state.sum !== null) {
      let sign = '==';
      if (state.sum > state.target) sign = '&gt;';
      if (state.sum < state.target) sign = '&lt;';

      sumHTML = `
        <div style="display:flex; align-items:center; gap:15px; margin-top:20px; font-size:24px; font-family:monospace; background:rgba(255,255,255,0.05); padding:10px 20px; border-radius:8px; border:1px solid var(--border);">
          <span style="color:#a855f7">${state.nums[state.i]}</span> + 
          <span style="color:#38bdf8">${state.nums[state.l]}</span> + 
          <span style="color:#fbbf24">${state.nums[state.r]}</span> 
          = <strong style="color:${eqColor}">${state.sum}</strong> <span style="color:${eqColor}">${sign}</span> <strong>${state.target}</strong>
        </div>
      `;
    }
    
    let comparisonHTML = '';
    if (state.sum !== null && state.phase !== 'ptr_init') {
        comparisonHTML = `
          <div style="margin-top:15px; font-size:14px; text-align:center; color:var(--text-dim);">
            Distance = abs(${state.sum} - ${state.target}) = <span style="color:${state.isBetter ? '#34d399' : 'var(--text)'}; font-weight:bold;">${state.diffNew}</span>
            <span style="margin:0 10px;">|</span>
            Best Distance = abs(${state.phase === 'update' ? state.sum : state.res} - ${state.target}) = <strong>${state.phase === 'update' ? state.diffNew : state.diffOld}</strong>
          </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted Array (Target = <span style="color:#f43f5e;">${state.target}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
          ${sumHTML}
          ${comparisonHTML}
        </div>
        <div class="glass-panel" style="padding: 15px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Closest Sum Found</div>
          <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.res}</div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Trapping Rain Water (DOM) ============ */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Trapping Rain Water', short: 'Trapping Water',
  idea: 'Use two pointers <code>L</code> and <code>R</code> from both ends. Maintain <code>maxL</code> and <code>maxR</code>. The smaller of the two maxes determines how much water can be trapped at the current pointer. Move the pointer with the smaller max inwards.',
  complexity: 'Time O(N) · Space O(1)',
  input: '0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1', hint: 'comma-separated array of heights',
  code: [
    'def trap(height):',
    '    if not height: return 0',
    '    l, r = 0, len(height) - 1',
    '    maxLeft, maxRight = height[l], height[r]',
    '    res = 0',
    '    while l < r:',
    '        if maxLeft < maxRight:',
    '            l += 1',
    '            maxLeft = max(maxLeft, height[l])',
    '            res += maxLeft - height[l]',
    '        else:',
    '            r -= 1',
    '            maxRight = max(maxRight, height[r])',
    '            res += maxRight - height[r]',
    '    return res'
  ],
  parse(str) {
    return { height: avArr(str) };
  },
  buildStates({ height }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (height.length === 0) {
      domPushState(seq, {
        kind: 'empty', line: 2, color: 'default',
        height, l: -1, r: -1, maxL: 0, maxR: 0, phase: 'done', res: 0,
        explTitle: 'Empty Array',
        explText: `Array is empty. Return 0.`
      }, ctx);
      return seq;
    }

    let l = 0;
    let r = height.length - 1;
    let maxL = height[l];
    let maxR = height[r];
    let res = 0;

    let waterLvl = new Array(height.length).fill(0);

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      height, l, r, maxL, maxR, phase: 'init', res, waterLvl: [...waterLvl],
      explTitle: 'Initialization',
      explText: `L starts at left end (${l}), R starts at right end (${r}). maxL = ${maxL}, maxR = ${maxR}.`
    }, ctx);

    while (l < r) {
      if (maxL < maxR) {
        domPushState(seq, {
          kind: 'compare_left', line: 7, color: 'blue',
          height, l, r, maxL, maxR, phase: 'compare_left', res, waterLvl: [...waterLvl],
          explTitle: `Compare maxL and maxR`,
          explText: `maxL (${maxL}) < maxR (${maxR}). The water level at L is bounded by maxL. We will process L.`
        }, ctx);

        l++;
        let oldMaxL = maxL;
        maxL = Math.max(maxL, height[l]);
        
        let trapped = Math.max(0, maxL - height[l]);
        res += trapped;
        waterLvl[l] = trapped;

        domPushState(seq, {
          kind: 'process_left', line: 10, color: 'emerald',
          height, l, r, maxL, maxR, phase: 'process_left', res, waterLvl: [...waterLvl], trapped, oldMax: oldMaxL, currH: height[l],
          explTitle: `Process L`,
          explText: `Move L to ${l}. maxL updates to max(${oldMaxL}, ${height[l]}) = ${maxL}. Water trapped = ${maxL} - ${height[l]} = ${trapped}. Total water = ${res}.`
        }, ctx);
      } else {
        domPushState(seq, {
          kind: 'compare_right', line: 11, color: 'blue',
          height, l, r, maxL, maxR, phase: 'compare_right', res, waterLvl: [...waterLvl],
          explTitle: `Compare maxL and maxR`,
          explText: `maxL (${maxL}) >= maxR (${maxR}). The water level at R is bounded by maxR. We will process R.`
        }, ctx);

        r--;
        let oldMaxR = maxR;
        maxR = Math.max(maxR, height[r]);
        
        let trapped = Math.max(0, maxR - height[r]);
        res += trapped;
        waterLvl[r] = trapped;

        domPushState(seq, {
          kind: 'process_right', line: 14, color: 'amber',
          height, l, r, maxL, maxR, phase: 'process_right', res, waterLvl: [...waterLvl], trapped, oldMax: oldMaxR, currH: height[r],
          explTitle: `Process R`,
          explText: `Move R to ${r}. maxR updates to max(${oldMaxR}, ${height[r]}) = ${maxR}. Water trapped = ${maxR} - ${height[r]} = ${trapped}. Total water = ${res}.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 15, color: 'emerald',
      height, l: -1, r: -1, maxL, maxR, phase: 'done', res, waterLvl: [...waterLvl],
      explTitle: `Done`,
      explText: `L and R met. Total water trapped is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    let maxH = Math.max(...state.height, 1);
    
    // Draw columns
    const columnsHTML = state.height.map((h, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let w = state.waterLvl ? state.waterLvl[idx] : 0;
      
      let heightPx = (h / maxH) * 150;
      let waterPx = (w / maxH) * 150;
      
      let border = 'var(--border)';
      if (isL) border = '#38bdf8';
      if (isR) border = '#fbbf24';
      
      let glow = '';
      if (isL) glow = 'box-shadow: 0 0 10px #38bdf8;';
      if (isR) glow = 'box-shadow: 0 0 10px #fbbf24;';
      
      if (state.phase === 'process_left' && isL) glow = 'box-shadow: 0 0 15px #34d399;';
      if (state.phase === 'process_right' && isR) glow = 'box-shadow: 0 0 15px #f43f5e;';

      let lLabel = isL ? `<div style="position:absolute; bottom:-25px; color:#38bdf8; font-weight:bold; font-size:12px;">L</div>` : '';
      let rLabel = isR ? `<div style="position:absolute; bottom:-25px; color:#fbbf24; font-weight:bold; font-size:12px;">R</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; justify-content:flex-end; align-items:center; position:relative; height: 160px; width:30px;">
          <div style="font-size:10px; color:var(--text-dim); position:absolute; top:-20px;">${idx}</div>
          
          <div style="width:100%; display:flex; flex-direction:column; justify-content:flex-end; position:relative;">
            <!-- Water block -->
            ${w > 0 ? `<div style="width:100%; height:${waterPx}px; background:rgba(56, 189, 248, 0.4); border-top:2px solid #38bdf8; display:flex; justify-content:center; align-items:center; z-index:2; transition: height 0.3s;">
                <span style="font-size:10px; color:#0ea5e9; font-weight:bold;">${w}</span>
            </div>` : ''}
            
            <!-- Ground block -->
            <div style="width:100%; height:${heightPx}px; background:var(--surface); border:2px solid ${border}; border-radius: 4px 4px 0 0; ${glow} display:flex; justify-content:center; align-items:flex-end; z-index:3; transition: all 0.3s;">
                <span style="font-size:12px; font-weight:bold; padding-bottom:4px; ${isL?'color:#38bdf8;':''}${isR?'color:#fbbf24;':''}">${h}</span>
            </div>
          </div>
          
          ${lLabel}
          ${rLabel}
        </div>
      `;
    }).join('');

    let infoHTML = '';
    if (state.phase !== 'done') {
        infoHTML = `
            <div style="display:flex; gap:20px; margin-top:20px;">
                <div style="padding:10px 15px; border-radius:6px; background:rgba(56, 189, 248, 0.1); border:1px solid #38bdf8;">
                    maxLeft = <strong style="color:#38bdf8; font-size:18px;">${state.maxL}</strong>
                </div>
                <div style="padding:10px 15px; border-radius:6px; background:rgba(251, 191, 36, 0.1); border:1px solid #fbbf24;">
                    maxRight = <strong style="color:#fbbf24; font-size:18px;">${state.maxR}</strong>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 40px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center;">
          <div class="panel-heading" style="margin-bottom: 35px; color: var(--accent);">Elevation Map</div>
          
          <div style="display:flex; gap:8px; align-items:flex-end; border-bottom: 2px solid var(--border); padding-bottom:0; height:180px;">
            ${columnsHTML}
          </div>
          
          ${infoHTML}
        </div>
        
        <div class="glass-panel" style="padding: 15px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Total Water Trapped</div>
          <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.res}</div>
        </div>
      </div>
    `;
  }
});

/* ================================ 02 · Boats to Save People (DOM) ========== */
defineAlgoDom('02_two_pointers', {
  type: 'dom',
  title: 'Boats to Save People', short: 'Boats to Save People',
  idea: 'Sort people by weight. Use two pointers <code>L</code> (lightest) and <code>R</code> (heaviest). If <code>people[L] + people[R] <= limit</code>, they can share a boat. Otherwise, the heaviest person <code>R</code> must go alone.',
  complexity: 'Time O(N log N) · Space O(1) or O(N)',
  input: '3, 2, 2, 1 ; 3', hint: 'comma-separated array of weights ; limit',
  code: [
    'def numRescueBoats(people, limit):',
    '    people.sort()',
    '    res = 0',
    '    l, r = 0, len(people) - 1',
    '    while l <= r:',
    '        remain = limit - people[r]',
    '        r -= 1',
    '        res += 1',
    '        if l <= r and remain >= people[l]:',
    '            l += 1',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { people: avArr(p[0]), limit: parseInt(p[1] || '0', 10) };
  },
  buildStates({ people, limit }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const arr = [...people].sort((a, b) => a - b);
    let res = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      people: [...arr], limit, l: -1, r: -1, phase: 'init', res, boats: [],
      explTitle: 'Initialization',
      explText: `Sort the people array from lightest to heaviest.`
    }, ctx);

    let l = 0;
    let r = arr.length - 1;
    let boats = [];

    domPushState(seq, {
      kind: 'ptr_init', line: 4, color: 'blue',
      people: [...arr], limit, l, r, phase: 'ptr_init', res, boats: [...boats],
      explTitle: `Pointers`,
      explText: `L starts at lightest (${arr[l]}), R starts at heaviest (${arr[r]}). Boat limit is ${limit}.`
    }, ctx);

    while (l <= r) {
      let rWeight = arr[r];
      let remain = limit - rWeight;
      
      domPushState(seq, {
        kind: 'process_r', line: 6, color: 'amber',
        people: [...arr], limit, l, r, phase: 'process_r', res, boats: [...boats], remain,
        explTitle: `Heaviest Person Enters Boat`,
        explText: `Heaviest remaining person is ${rWeight}. Remaining capacity in this boat is ${limit} - ${rWeight} = ${remain}.`
      }, ctx);

      res++;
      
      let canPair = false;
      let boatStr = `[${rWeight}`;

      if (l < r && remain >= arr[l]) {
        canPair = true;
        boatStr += `, ${arr[l]}]`;
        domPushState(seq, {
          kind: 'pair', line: 10, color: 'emerald',
          people: [...arr], limit, l, r, phase: 'pair', res, boats: [...boats], remain,
          explTitle: `Lightest Can Join!`,
          explText: `Lightest person ${arr[l]} <= remaining capacity ${remain}. They pair up in this boat!`
        }, ctx);
        l++;
        r--;
      } else if (l === r) {
        boatStr += `]`;
        domPushState(seq, {
          kind: 'last_alone', line: 9, color: 'blue',
          people: [...arr], limit, l, r, phase: 'alone', res, boats: [...boats], remain,
          explTitle: `Last Person`,
          explText: `Only one person left. They take a boat alone.`
        }, ctx);
        r--;
      } else {
        boatStr += `]`;
        domPushState(seq, {
          kind: 'alone', line: 9, color: 'red',
          people: [...arr], limit, l, r, phase: 'alone', res, boats: [...boats], remain,
          explTitle: `Lightest Cannot Join`,
          explText: `Lightest person ${arr[l]} > remaining capacity ${remain}. Heaviest person must go alone.`
        }, ctx);
        r--;
      }
      
      boats.push(boatStr);
      
      domPushState(seq, {
        kind: 'boat_dispatched', line: 8, color: 'blue',
        people: [...arr], limit, l, r, phase: 'dispatch', res, boats: [...boats], remain: null,
        explTitle: `Boat Dispatched`,
        explText: `Boat ${res} sent with ${boatStr}. Total boats: ${res}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      people: [...arr], limit, l: -1, r: -1, phase: 'done', res, boats: [...boats], remain: null,
      explTitle: `Done`,
      explText: `All people rescued! Total boats used: ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.people.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let isSaved = idx < state.l || idx > state.r;
      if (state.phase === 'done') isSaved = true;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (isSaved) {
        color = 'var(--text-dim)';
        bg = 'rgba(255,255,255,0.02)';
      } else {
        if (isL) { border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;'; }
        if (isR) { border = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;'; }
        
        if (state.phase === 'pair' && (isL || isR)) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
        }
      }

      let pt = [];
      if (isL && !isSaved) pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && !isSaved) pt.push('<div style="color:#f43f5e; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = '';
      if (pt.length > 0) {
        bottomHTML = `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>`;
      }
      
      let saveIcon = isSaved ? `<div style="position:absolute; top:-12px; right:-12px; background:#10b981; border-radius:50%; width:20px; height:20px; display:flex; justify-content:center; align-items:center; font-size:10px; z-index:3;">✓</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${saveIcon}
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let infoHTML = '';
    if (state.phase === 'process_r' || state.phase === 'pair' || state.phase === 'alone') {
        let lW = state.people[state.l];
        let opColor = state.phase === 'pair' ? '#34d399' : (state.phase === 'alone' ? '#f43f5e' : 'var(--text)');
        let msg = state.phase === 'pair' ? '✓ Fits' : (state.phase === 'alone' ? '✗ Too Heavy' : '...');
        
        if (state.l === state.r) {
            infoHTML = `
                <div style="margin-top:20px; padding:15px; background:rgba(255,255,255,0.05); border:1px solid var(--border); border-radius:8px; text-align:center;">
                    <span style="color:#f43f5e; font-weight:bold; font-size:20px;">${state.people[state.r]}</span> 
                    <span style="margin:0 10px;">is the last person. They get their own boat.</span>
                </div>
            `;
        } else {
            infoHTML = `
                <div style="margin-top:20px; padding:15px; background:rgba(255,255,255,0.05); border:1px solid var(--border); border-radius:8px; text-align:center;">
                    Remaining Capacity: <span style="font-family:monospace; font-size:20px;">${state.limit} - <span style="color:#f43f5e;">${state.people[state.r]}</span> = <strong>${state.remain}</strong></span>
                    <br><br>
                    Can <span style="color:#38bdf8;">${lW}</span> join? 
                    <span style="font-family:monospace; font-size:18px; color:${opColor}; margin-left:10px;">${lW} &le; ${state.remain} ? ${msg}</span>
                </div>
            `;
        }
    }
    
    let boatsHTML = state.boats.length > 0 
      ? `<div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-top:15px;">` + 
        state.boats.map((b, i) => `<div style="background:rgba(245, 158, 11, 0.1); border:2px solid #f59e0b; padding:8px 15px; border-radius:20px; display:flex; align-items:center; gap:8px;">
            <span style="font-size:16px;">⛵</span>
            <span style="font-family:monospace; font-weight:bold; color:#fbbf24;">${b}</span>
        </div>`).join('') +
        `</div>`
      : `<div style="margin-top:15px; color:var(--text-dim); font-style:italic;">No boats dispatched yet.</div>`;

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted People (Boat Limit = <span style="color:#a855f7;">${state.limit}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
          ${infoHTML}
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; display:flex; justify-content:space-between; width:100%;">
            <span>Dispatched Boats</span>
            <span style="color:#f59e0b; font-size:16px;">Total: ${state.res}</span>
          </div>
          ${boatsHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Max Average Subarray I (DOM) ======== */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Maximum Average Subarray I', short: 'Max Avg Subarray',
  idea: 'Use a fixed sliding window of size <code>k</code>. Compute the sum of the first <code>k</code> elements. Then slide the window by adding the new element and subtracting the oldest element. Keep track of the maximum sum seen, then divide by <code>k</code>.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 12, -5, -6, 50, 3 ; 4', hint: 'comma-separated array ; k',
  code: [
    'def findMaxAverage(nums, k):',
    '    cur_sum = sum(nums[:k])',
    '    max_sum = cur_sum',
    '    for i in range(k, len(nums)):',
    '        cur_sum += nums[i] - nums[i - k]',
    '        max_sum = max(max_sum, cur_sum)',
    '    return max_sum / k'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (k > nums.length) k = nums.length;
    if (k <= 0) return seq;

    let curSum = 0;
    for (let i = 0; i < k; i++) curSum += nums[i];
    let maxSum = curSum;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, l: 0, r: k - 1, phase: 'init', curSum, maxSum, added: null, removed: null,
      explTitle: 'Initialization',
      explText: `Initial window of size ${k}. Sum = ${curSum}. Max Sum = ${maxSum}.`
    }, ctx);

    for (let i = k; i < nums.length; i++) {
      let added = nums[i];
      let removed = nums[i - k];

      domPushState(seq, {
        kind: 'slide', line: 5, color: 'blue',
        nums, k, l: i - k + 1, r: i, phase: 'slide', curSum, maxSum, added, removed,
        explTitle: `Slide Window`,
        explText: `Slide right. Add ${added} and remove ${removed}.`
      }, ctx);
      
      curSum += added - removed;

      let isNewMax = curSum > maxSum;
      maxSum = Math.max(maxSum, curSum);

      domPushState(seq, {
        kind: 'update', line: 6, color: isNewMax ? 'emerald' : 'amber',
        nums, k, l: i - k + 1, r: i, phase: 'update', curSum, maxSum, added, removed, isNewMax,
        explTitle: isNewMax ? `New Maximum Found!` : `Check Max`,
        explText: `New window sum = ${curSum}. ${isNewMax ? `It's greater than our previous max! Updated max_sum.` : `It's not greater than ${maxSum}.`}`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 7, color: 'emerald',
      nums, k, l: -1, r: -1, phase: 'done', curSum, maxSum, added: null, removed: null,
      explTitle: `Done`,
      explText: `Max Sum is ${maxSum}. Return ${maxSum} / ${k} = ${(maxSum / k).toFixed(5)}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let inWin = idx >= state.l && idx <= state.r;
      let isAdded = state.phase === 'slide' && idx === state.r;
      let isRemoved = state.phase === 'slide' && idx === state.l - 1;
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
      }
      
      if (isAdded) {
        bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      if (isRemoved) {
        bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;';
        inWin = false; // Override
      }

      if (state.phase === 'update' && state.isNewMax && inWin) {
        bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${inWin || isAdded || isRemoved ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${isAdded ? `<div style="position:absolute; bottom:-20px; color:#34d399; font-size:12px; font-weight:bold;">+</div>` : ''}
          ${isRemoved ? `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold;">-</div>` : ''}
        </div>
      `;
    }).join('');
    
    let infoHTML = '';
    if (state.phase === 'slide' || state.phase === 'update') {
      infoHTML = `
        <div style="margin-top:20px; padding:15px; background:rgba(255,255,255,0.05); border:1px solid var(--border); border-radius:8px; text-align:center; font-family:monospace; font-size:18px;">
          Cur Sum = ${state.curSum - (state.phase === 'slide' ? state.added - state.removed : 0)} 
          <span style="color:#f43f5e; margin:0 10px;">- ${state.removed}</span> 
          <span style="color:#34d399; margin:0 10px;">+ ${state.added}</span>
          = <strong style="color:#38bdf8; font-size:22px;">${state.curSum}</strong>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Window Size k = <span style="color:#38bdf8;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
          ${infoHTML}
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:600px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Current Sum</div>
              <div style="font-size:28px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8;">${state.phase !== 'done' ? state.curSum : '-'}</div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Sum Seen</div>
              <div style="font-size:28px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.maxSum}</div>
            </div>
        </div>
        
        ${state.phase === 'done' ? `
            <div class="glass-panel" style="padding: 15px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px; border-color:#a855f7; box-shadow: 0 0 20px rgba(168, 85, 247, 0.2);">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Maximum Average</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#a855f7;">${(state.maxSum / state.k).toFixed(5)}</div>
            </div>
        ` : ''}
      </div>
    `;
  }
});

/* ================================ 03 · Maximum Number of Vowels (DOM) ======= */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Maximum Number of Vowels in a Substring of Given Length', short: 'Max Vowels',
  idea: 'Fixed sliding window of size <code>k</code>. Count vowels in the first <code>k</code> chars. Then slide right: if the newly added char is a vowel, increment count. If the removed char is a vowel, decrement count. Keep track of the max.',
  complexity: 'Time O(N) · Space O(1)',
  input: 'abciiidef ; 3', hint: 'string ; k',
  code: [
    'def maxVowels(s, k):',
    '    vowels = set("aeiou")',
    '    cur_vowels = sum(1 for c in s[:k] if c in vowels)',
    '    max_vowels = cur_vowels',
    '    for i in range(k, len(s)):',
    '        if s[i] in vowels:',
    '            cur_vowels += 1',
    '        if s[i - k] in vowels:',
    '            cur_vowels -= 1',
    '        max_vowels = max(max_vowels, cur_vowels)',
    '    return max_vowels'
  ],
  parse(str) {
    const p = str.split(';');
    return { s: p[0].trim(), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ s, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const isVowel = c => ['a','e','i','o','u'].includes(c.toLowerCase());
    
    if (k > s.length) k = s.length;
    if (k <= 0) return seq;

    let curVowels = 0;
    for (let i = 0; i < k; i++) if (isVowel(s[i])) curVowels++;
    let maxVowels = curVowels;

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      s, k, l: 0, r: k - 1, phase: 'init', curVowels, maxVowels, added: null, removed: null,
      explTitle: 'Initialization',
      explText: `Initial window of size ${k}. Vowels count = ${curVowels}.`
    }, ctx);

    for (let i = k; i < s.length; i++) {
      let added = s[i];
      let removed = s[i - k];

      domPushState(seq, {
        kind: 'slide', line: 5, color: 'blue',
        s, k, l: i - k + 1, r: i, phase: 'slide', curVowels, maxVowels, added, removed,
        explTitle: `Slide Window`,
        explText: `Slide right. Adding '${added}' and removing '${removed}'.`
      }, ctx);
      
      if (isVowel(added)) curVowels++;
      if (isVowel(removed)) curVowels--;

      let isNewMax = curVowels > maxVowels;
      maxVowels = Math.max(maxVowels, curVowels);

      domPushState(seq, {
        kind: 'update', line: 10, color: isNewMax ? 'emerald' : 'amber',
        s, k, l: i - k + 1, r: i, phase: 'update', curVowels, maxVowels, added, removed, isNewMax,
        explTitle: isNewMax ? `New Maximum Found!` : `Check Max`,
        explText: `Current vowels = ${curVowels}. ${isNewMax ? `Updated max_vowels.` : `Max remains ${maxVowels}.`}`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      s, k, l: -1, r: -1, phase: 'done', curVowels, maxVowels, added: null, removed: null,
      explTitle: `Done`,
      explText: `Max vowels found in any window of size ${k} is ${maxVowels}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const isVowel = c => ['a','e','i','o','u'].includes(c.toLowerCase());
    
    const charsHTML = state.s.split('').map((c, idx) => {
      let inWin = idx >= state.l && idx <= state.r;
      let isAdded = state.phase === 'slide' && idx === state.r;
      let isRemoved = state.phase === 'slide' && idx === state.l - 1;
      let vowel = isVowel(c);
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = vowel ? '#a855f7' : 'var(--text)'; // Highlight vowels generally
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
      }
      
      if (isAdded) {
        bg = vowel ? 'rgba(52,211,153,0.4)' : 'rgba(255,255,255,0.1)'; 
        border = vowel ? '#34d399' : 'var(--border)'; 
        boxsh = vowel ? 'box-shadow: 0 0 15px #34d399;' : ''; 
      }
      
      if (isRemoved) {
        bg = vowel ? 'rgba(244,63,94,0.4)' : 'rgba(255,255,255,0.1)'; 
        border = vowel ? '#f43f5e' : 'var(--border)'; 
        boxsh = vowel ? 'box-shadow: 0 0 15px #f43f5e;' : ''; 
        inWin = false; 
      }

      if (state.phase === 'update' && state.isNewMax && inWin) {
        bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:22px; color:${color};
            ${inWin || isAdded || isRemoved ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s; font-family:monospace;
          ">${c}</div>
          ${isAdded && vowel ? `<div style="position:absolute; bottom:-20px; color:#34d399; font-size:12px; font-weight:bold;">+1</div>` : ''}
          ${isRemoved && vowel ? `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold;">-1</div>` : ''}
        </div>
      `;
    }).join('');
    
    let infoHTML = '';
    if (state.phase === 'slide' || state.phase === 'update') {
      let addVal = isVowel(state.added) ? 1 : 0;
      let remVal = isVowel(state.removed) ? 1 : 0;
      let oldSum = state.phase === 'slide' ? state.curVowels : state.curVowels - addVal + remVal;
      
      infoHTML = `
        <div style="margin-top:20px; padding:15px; background:rgba(255,255,255,0.05); border:1px solid var(--border); border-radius:8px; text-align:center; font-family:monospace; font-size:18px;">
          Cur Vowels = ${oldSum} 
          <span style="color:#f43f5e; margin:0 10px;">- ${remVal}</span> 
          <span style="color:#34d399; margin:0 10px;">+ ${addVal}</span>
          = <strong style="color:#a855f7; font-size:22px;">${state.curVowels}</strong>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">String (Window Size k = <span style="color:#38bdf8;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${charsHTML}
          </div>
          ${infoHTML}
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:600px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Current Vowels</div>
              <div style="font-size:28px; font-weight:bold; font-family:monospace; margin-top:5px; color:#a855f7;">${state.phase !== 'done' ? state.curVowels : '-'}</div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Vowels Seen</div>
              <div style="font-size:28px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.maxVowels}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Contains Duplicate II (DOM) ========= */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Contains Duplicate II', short: 'Contains Dup II',
  idea: 'Maintain a <b>Hash Set</b> (or window) of the last <code>k</code> elements. As you scan, if the current element is already in the set, you found a duplicate within distance <code>k</code>. Otherwise, add it and remove the element that fell out of the window.',
  complexity: 'Time O(N) · Space O(K)',
  input: '1, 2, 3, 1 ; 3', hint: 'comma-separated array ; k',
  code: [
    'def containsNearbyDuplicate(nums, k):',
    '    window = set()',
    '    for i in range(len(nums)):',
    '        if i > k:',
    '            window.remove(nums[i - k - 1])',
    '        if nums[i] in window:',
    '            return True',
    '        window.add(nums[i])',
    '    return False'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const window = new Set();
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, i: -1, phase: 'init', window: Array.from(window),
      explTitle: 'Initialization',
      explText: `We keep a Hash Set of at most ${k} elements. If we see a number already in the set, return True.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
      let removed = null;
      if (i > k) {
        removed = nums[i - k - 1];
        window.delete(removed);
        domPushState(seq, {
          kind: 'evict', line: 5, color: 'amber',
          nums, k, i, phase: 'evict', window: Array.from(window), removed,
          explTitle: `Evict from Window`,
          explText: `i=${i} > k=${k}. Remove ${removed} from set to maintain window size <= ${k}.`
        }, ctx);
      }

      domPushState(seq, {
        kind: 'check', line: 6, color: 'blue',
        nums, k, i, phase: 'check', window: Array.from(window), current: nums[i],
        explTitle: `Check Set`,
        explText: `Is ${nums[i]} in the set?`
      }, ctx);

      if (window.has(nums[i])) {
        domPushState(seq, {
          kind: 'found', line: 7, color: 'emerald',
          nums, k, i, phase: 'found', window: Array.from(window), current: nums[i],
          explTitle: `Found Duplicate!`,
          explText: `${nums[i]} is already in the set! We found a duplicate within distance ${k}. Return True.`
        }, ctx);
        return seq;
      }

      window.add(nums[i]);
      domPushState(seq, {
        kind: 'add', line: 8, color: 'default',
        nums, k, i, phase: 'add', window: Array.from(window), current: nums[i],
        explTitle: `Add to Set`,
        explText: `${nums[i]} wasn't in the set. Add it.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'not_found', line: 9, color: 'red',
      nums, k, i: -1, phase: 'done', window: Array.from(window),
      explTitle: `Not Found`,
      explText: `Finished scanning array without finding any nearby duplicates. Return False.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      let isRemoved = state.phase === 'evict' && idx === state.i - state.k - 1;
      let inWindow = idx > (state.i - state.k - 1) && idx < state.i && state.phase !== 'done';
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      let transform = '';
      let zIndex = 1;
      
      if (inWindow) {
        border = '#38bdf8';
      }
      
      if (isCurrent) {
        border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; transform = 'scale(1.1)'; zIndex = 2;
        if (state.phase === 'found') {
            bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
        }
      } else {
          transform = 'scale(1)'; zIndex = 1;
      }
      
      if (isRemoved) {
        bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative; z-index:${zIndex};">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            transform: ${transform};
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');
    
    let setHTML = state.window.length > 0 
      ? state.window.map(v => {
          let h = '';
          if (state.phase === 'found' && v === state.current) {
              h = 'background:rgba(52,211,153,0.3); border-color:#34d399; box-shadow:0 0 10px #34d399; color:#34d399;';
          }
          return `<div style="width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; border-radius: 6px; font-weight: bold; font-size:18px; transition: all 0.3s; ${h}">${v}</div>`;
      }).join('')
      : `<div style="color:var(--text-dim); font-style:italic; line-height:45px; padding:0 10px;">Set is empty</div>`;

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (k = <span style="color:#38bdf8;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
        <div class="glass-panel" style="padding: 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:600px;">
          <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:15px;">Hash Set Window</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; min-height:45px;">
            ${setHTML}
          </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Max Consecutive Ones III (DOM) ====== */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Max Consecutive Ones III', short: 'Max Consecutive Ones',
  idea: 'Use a dynamic sliding window <code>[L, R]</code>. Expand <code>R</code> and if we see a 0, decrement our <code>k</code> allowance. If <code>k < 0</code>, we have too many 0s, so shrink from <code>L</code> until we discard a 0 (and increment <code>k</code>). The window size <code>R - L + 1</code> is our candidate length.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1,1,1,0,0,0,1,1,1,1,0 ; 2', hint: 'comma-separated binary array ; k (flips)',
  code: [
    'def longestOnes(nums, k):',
    '    l = 0',
    '    max_len = 0',
    '    for r in range(len(nums)):',
    '        if nums[r] == 0:',
    '            k -= 1',
    '        while k < 0:',
    '            if nums[l] == 0:',
    '                k += 1',
    '            l += 1',
    '        max_len = max(max_len, r - l + 1)',
    '    return max_len'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let l = 0;
    let maxLen = 0;
    let origK = k;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, l: 0, r: -1, phase: 'init', k, maxLen, origK,
      explTitle: 'Initialization',
      explText: `We can flip at most ${k} zeros to ones. Track max window length.`
    }, ctx);

    for (let r = 0; r < nums.length; r++) {
      domPushState(seq, {
        kind: 'expand', line: 4, color: 'blue',
        nums, l, r, phase: 'expand', k, maxLen, origK, current: nums[r],
        explTitle: `Expand Window`,
        explText: `Move R to ${r}. Added element is ${nums[r]}.`
      }, ctx);

      if (nums[r] === 0) {
        k--;
        domPushState(seq, {
          kind: 'flip', line: 6, color: 'amber',
          nums, l, r, phase: 'flip', k, maxLen, origK, current: nums[r],
          explTitle: `Flip Zero`,
          explText: `Found a 0. We flip it. Allowance k becomes ${k}.`
        }, ctx);
      }

      while (k < 0) {
        domPushState(seq, {
          kind: 'invalid', line: 7, color: 'red',
          nums, l, r, phase: 'shrink', k, maxLen, origK, leftVal: nums[l],
          explTitle: `Invalid Window`,
          explText: `k < 0. We flipped too many 0s. Must shrink from L (${l}) to recover flips.`
        }, ctx);

        if (nums[l] === 0) {
          k++;
          domPushState(seq, {
            kind: 'recover', line: 9, color: 'emerald',
            nums, l, r, phase: 'shrink', k, maxLen, origK, leftVal: nums[l],
            explTitle: `Recover Flip`,
            explText: `Element at L was 0. By removing it from our window, we recover 1 flip. k becomes ${k}.`
          }, ctx);
        }
        l++;
      }

      let curLen = r - l + 1;
      let isNewMax = curLen > maxLen;
      maxLen = Math.max(maxLen, curLen);

      domPushState(seq, {
        kind: 'update', line: 11, color: isNewMax ? 'emerald' : 'default',
        nums, l, r, phase: 'valid', k, maxLen, origK, curLen, isNewMax,
        explTitle: `Valid Window`,
        explText: `Window [${l}, ${r}] is valid. Length is ${curLen}. ${isNewMax ? `New max!` : `Max remains ${maxLen}.`}`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'emerald',
      nums, l: -1, r: -1, phase: 'done', k, maxLen, origK,
      explTitle: `Done`,
      explText: `Longest sequence of 1s (with $\\le$ ${origK} flips) has length ${maxLen}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = v === 1 ? '#34d399' : 'var(--text-dim)'; // 1s are green, 0s are dim
      let boxsh = '';
      
      let flipped = inWin && v === 0;
      
      if (inWin) {
        border = '#38bdf8';
        if (flipped) {
            bg = 'rgba(245, 158, 11, 0.2)'; // Amber background for flipped 0s
            color = '#f59e0b';
            border = '#f59e0b';
        }
      }
      
      if (state.phase === 'shrink' && isL) {
          border = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
      } else if (isR && state.phase === 'expand') {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;';
      }

      if (state.phase === 'valid' && state.isNewMax && inWin) {
          boxsh = 'box-shadow: 0 0 10px #34d399;';
          border = '#34d399';
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${inWin || isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${flipped ? '1' : v}</div>
          ${flipped ? `<div style="position:absolute; top:-8px; right:-8px; font-size:10px; background:#f59e0b; color:#fff; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center;">F</div>` : ''}
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let kColor = state.k < 0 ? '#f43f5e' : (state.k === 0 ? '#f59e0b' : '#34d399');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Binary Array</div>
          <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:650px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Flips Left (k)</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:${kColor};">${state.phase !== 'done' ? state.k : '-'}</div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Window Length</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.maxLen}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Longest Repeating Char Replacement == */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Longest Repeating Character Replacement', short: 'Char Replacement',
  idea: 'Sliding window. Keep a frequency map of characters in the window. The window is valid if <code>(window_length) - (max_freq) <= k</code>. If invalid, shrink from <code>L</code> until it becomes valid. Update max length.',
  complexity: 'Time O(N) · Space O(1) (map of 26 chars)',
  input: 'A,B,A,B,B,A ; 2', hint: 'comma-separated string chars ; k',
  code: [
    'def characterReplacement(s, k):',
    '    counts = {}',
    '    res = 0',
    '    l = 0',
    '    maxf = 0',
    '    for r in range(len(s)):',
    '        counts[s[r]] = counts.get(s[r], 0) + 1',
    '        maxf = max(maxf, counts[s[r]])',
    '        while (r - l + 1) - maxf > k:',
    '            counts[s[l]] -= 1',
    '            l += 1',
    '        res = max(res, r - l + 1)',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    const chars = String(p[0] || '').split(/[\s,]+/).filter(Boolean).map(c => c.trim());
    return { s: chars, k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ s, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let counts = {};
    let l = 0;
    let res = 0;
    let maxf = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      s, l: 0, r: -1, phase: 'init', k, res, maxf, counts: {...counts},
      explTitle: 'Initialization',
      explText: `We can replace at most ${k} characters to form a repeating sequence.`
    }, ctx);

    for (let r = 0; r < s.length; r++) {
      let charR = s[r];
      counts[charR] = (counts[charR] || 0) + 1;
      let prevMaxF = maxf;
      maxf = Math.max(maxf, counts[charR]);

      domPushState(seq, {
        kind: 'expand', line: 8, color: 'blue',
        s, l, r, phase: 'expand', k, res, maxf, counts: {...counts},
        explTitle: `Expand Window`,
        explText: `Add '${charR}' to window. maxf updates from ${prevMaxF} to ${maxf}.`
      }, ctx);

      let winLen = r - l + 1;
      let toReplace = winLen - maxf;

      domPushState(seq, {
        kind: 'check', line: 9, color: toReplace > k ? 'red' : 'emerald',
        s, l, r, phase: 'check', k, res, maxf, counts: {...counts},
        explTitle: `Check Validity`,
        explText: `Window length = ${winLen}. Max freq element = ${maxf}. Elements to replace = ${winLen} - ${maxf} = ${toReplace}. ${toReplace > k ? `> ${k} (Invalid)` : `$\\le$ ${k} (Valid)`}`
      }, ctx);

      while ((r - l + 1) - maxf > k) {
        let charL = s[l];
        counts[charL] -= 1;
        l++;
        domPushState(seq, {
          kind: 'shrink', line: 11, color: 'amber',
          s, l, r, phase: 'shrink', k, res, maxf, counts: {...counts},
          explTitle: `Shrink Window`,
          explText: `Removed '${charL}' from window. L is now ${l}.`
        }, ctx);
      }

      let isNewMax = (r - l + 1) > res;
      res = Math.max(res, r - l + 1);

      domPushState(seq, {
        kind: 'update', line: 12, color: isNewMax ? 'emerald' : 'default',
        s, l, r, phase: 'valid', k, res, maxf, counts: {...counts},
        explTitle: `Update Max`,
        explText: `Valid window [${l}, ${r}] has length ${r - l + 1}. Max length is ${res}.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      s, l: -1, r: -1, phase: 'done', k, res, maxf, counts: {...counts},
      explTitle: `Done`,
      explText: `Longest repeating character replacement is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const charsHTML = state.s.map((c, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8';
      }
      
      if (state.phase === 'check') {
          if (idx >= state.l && idx <= state.r) {
              let winLen = state.r - state.l + 1;
              if (winLen - state.maxf > state.k) {
                  border = '#f43f5e'; bg = 'rgba(244,63,94,0.15)'; color = '#f43f5e';
              }
          }
      }

      if (state.phase === 'shrink' && isL - 1 === idx) {
          border = '#f59e0b'; bg = 'rgba(245,158,11,0.2)'; color = '#f59e0b';
          inWin = false;
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${inWin || isL || isR ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${c}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let countsArray = Object.entries(state.counts).filter(([_, count]) => count > 0);
    countsArray.sort((a,b) => b[1] - a[1]); // Sort by frequency descending
    
    let countsHTML = countsArray.length > 0 ? countsArray.map(([c, count]) => {
        let isMax = count === state.maxf && state.phase !== 'init' && state.phase !== 'done';
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:rgba(255,255,255,0.05); border:1px solid ${isMax ? '#34d399' : 'var(--border)'}; border-radius:6px; padding:5px 10px; min-width:40px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${isMax ? '#34d399' : 'var(--text)'};">${c}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">${count}</div>
            </div>
        `;
    }).join('') : '<div style="color:var(--text-dim); font-size:14px; font-style:italic;">Empty map</div>';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">String (k = <span style="color:#a855f7;">${state.k}</span>)</div>
          <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center;">
            ${charsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:650px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px;">Frequencies (counts)</div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Window Length</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Min Size Subarray Sum (DOM) ========= */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Minimum Size Subarray Sum', short: 'Min Size Subarray',
  idea: 'Use a dynamic sliding window <code>[L, R]</code>. Expand <code>R</code> to add to the running sum. When <code>sum >= target</code>, update the minimum length found and shrink from <code>L</code> to find an even smaller valid window.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 3, 1, 2, 4, 3 ; 7', hint: 'comma-separated array ; target',
  code: [
    'def minSubArrayLen(target, nums):',
    '    l = 0',
    '    cur_sum = 0',
    '    res = float("inf")',
    '    for r in range(len(nums)):',
    '        cur_sum += nums[r]',
    '        while cur_sum >= target:',
    '            res = min(res, r - l + 1)',
    '            cur_sum -= nums[l]',
    '            l += 1',
    '    return res if res != float("inf") else 0'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), target: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let l = 0;
    let curSum = 0;
    let res = Infinity;

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      nums, target, l: 0, r: -1, phase: 'init', curSum, res,
      explTitle: 'Initialization',
      explText: `Target sum is ${target}. Looking for minimum length contiguous subarray.`
    }, ctx);

    for (let r = 0; r < nums.length; r++) {
      curSum += nums[r];
      domPushState(seq, {
        kind: 'expand', line: 6, color: 'blue',
        nums, target, l, r, phase: 'expand', curSum, res, added: nums[r],
        explTitle: `Expand Window`,
        explText: `Add ${nums[r]} to window. Current sum = ${curSum}.`
      }, ctx);

      while (curSum >= target) {
        let isNewMin = (r - l + 1) < res;
        res = Math.min(res, r - l + 1);
        
        domPushState(seq, {
          kind: 'valid', line: 8, color: 'emerald',
          nums, target, l, r, phase: 'valid', curSum, res, isNewMin,
          explTitle: `Valid Subarray`,
          explText: `Sum ${curSum} >= target ${target}. Window length is ${r - l + 1}. ${isNewMin ? 'New minimum found!' : ''}`
        }, ctx);

        let removed = nums[l];
        curSum -= removed;
        l += 1;
        
        domPushState(seq, {
          kind: 'shrink', line: 10, color: 'amber',
          nums, target, l, r, phase: 'shrink', curSum, res, removed,
          explTitle: `Shrink Window`,
          explText: `Remove ${removed} from left (L is now ${l}). New sum = ${curSum}.`
        }, ctx);
      }
    }

    let finalRes = res === Infinity ? 0 : res;
    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, target, l: -1, r: -1, phase: 'done', curSum, res: finalRes,
      explTitle: `Done`,
      explText: res === Infinity ? `No subarray found with sum >= ${target}. Return 0.` : `Minimum length subarray with sum >= ${target} is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
      }
      
      if (state.phase === 'valid' && inWin) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      if (state.phase === 'shrink' && idx === state.l - 1) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;';
          inWin = false;
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${inWin || isL || isR || (state.phase === 'shrink' && idx === state.l - 1) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let sumColor = state.curSum >= state.target ? '#34d399' : '#38bdf8';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Target Sum &ge; <span style="color:#a855f7;">${state.target}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:650px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Current Window Sum</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:${state.phase !== 'done' ? sumColor : 'var(--text-dim)'};">${state.phase !== 'done' ? state.curSum : '-'}</div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Minimum Length</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#a855f7; text-shadow: 0 0 10px rgba(168,85,247,0.3);">${state.res === Infinity ? '&infin;' : state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Fruit Into Baskets (DOM) ============ */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Fruit Into Baskets', short: 'Fruit Baskets',
  idea: 'Find the longest contiguous subarray containing at most 2 distinct elements. Maintain a frequency map for the sliding window. If map size > 2, shrink from <code>L</code> until map size <= 2.',
  complexity: 'Time O(N) · Space O(1) (Hash Map holds at most 3 keys)',
  input: '1, 2, 3, 2, 2', hint: 'comma-separated array of fruit types',
  code: [
    'def totalFruit(fruits):',
    '    counts = {}',
    '    res = 0',
    '    l = 0',
    '    for r in range(len(fruits)):',
    '        counts[fruits[r]] = counts.get(fruits[r], 0) + 1',
    '        while len(counts) > 2:',
    '            counts[fruits[l]] -= 1',
    '            if counts[fruits[l]] == 0:',
    '                del counts[fruits[l]]',
    '            l += 1',
    '        res = max(res, r - l + 1)',
    '    return res'
  ],
  parse(str) {
    return { fruits: avArr(str) };
  },
  buildStates({ fruits }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let l = 0;
    let counts = {};
    let res = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      fruits, l: 0, r: -1, phase: 'init', res, counts: {...counts},
      explTitle: 'Initialization',
      explText: `We can have at most 2 distinct fruit types in our baskets.`
    }, ctx);

    for (let r = 0; r < fruits.length; r++) {
      let typeR = fruits[r];
      counts[typeR] = (counts[typeR] || 0) + 1;
      let distinct = Object.keys(counts).length;

      domPushState(seq, {
        kind: 'expand', line: 6, color: 'blue',
        fruits, l, r, phase: 'expand', res, counts: {...counts}, added: typeR, distinct,
        explTitle: `Expand Window`,
        explText: `Add fruit type ${typeR}. Window now has ${distinct} distinct type(s).`
      }, ctx);

      while (Object.keys(counts).length > 2) {
        domPushState(seq, {
          kind: 'invalid', line: 7, color: 'red',
          fruits, l, r, phase: 'invalid', res, counts: {...counts},
          explTitle: `Too Many Types`,
          explText: `We have ${Object.keys(counts).length} distinct types (> 2). Must shrink window from L.`
        }, ctx);

        let typeL = fruits[l];
        counts[typeL] -= 1;
        if (counts[typeL] === 0) {
          delete counts[typeL];
          domPushState(seq, {
            kind: 'delete', line: 10, color: 'emerald',
            fruits, l, r, phase: 'shrink', res, counts: {...counts}, removed: typeL,
            explTitle: `Type Evicted`,
            explText: `Count of type ${typeL} reached 0, so it's removed from our baskets.`
          }, ctx);
        } else {
            domPushState(seq, {
              kind: 'shrink', line: 8, color: 'amber',
              fruits, l, r, phase: 'shrink', res, counts: {...counts}, removed: typeL,
              explTitle: `Remove Fruit`,
              explText: `Removed 1 of type ${typeL} from L.`
            }, ctx);
        }
        l++;
      }

      let winLen = r - l + 1;
      let isNewMax = winLen > res;
      res = Math.max(res, winLen);

      domPushState(seq, {
        kind: 'valid', line: 12, color: isNewMax ? 'emerald' : 'default',
        fruits, l, r, phase: 'valid', res, counts: {...counts}, winLen, isNewMax,
        explTitle: `Valid Window`,
        explText: `Window is valid with $\\le$ 2 types. Length is ${winLen}. ${isNewMax ? 'New max!' : ''}`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      fruits, l: -1, r: -1, phase: 'done', res, counts: {...counts},
      explTitle: `Done`,
      explText: `Max fruits we can collect is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    const typeColors = ['#f43f5e', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'];
    const getColorForType = (type) => typeColors[Math.abs(type) % typeColors.length];

    const numsHTML = state.fruits.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let fruitColor = getColorForType(v);
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      let opacity = 0.5;
      
      if (inWin) {
        bg = fruitColor + '33'; // 20% opacity hex
        border = fruitColor;
        color = fruitColor;
        opacity = 1;
      }
      
      if (state.phase === 'invalid' && inWin) {
          border = '#f43f5e';
          boxsh = 'box-shadow: 0 0 10px #f43f5e;';
      } else if (state.phase === 'valid' && state.isNewMax && inWin) {
          boxsh = `box-shadow: 0 0 15px ${fruitColor}66;`;
      }

      if (state.phase === 'shrink' && idx === state.l - 1) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; opacity = 1;
          inWin = false;
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative; opacity:${opacity};">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 50%; font-weight: bold; font-size:18px; color:${color};
            ${inWin || isL || isR || (state.phase === 'shrink' && idx === state.l - 1) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">
            <span style="font-size:24px; position:absolute; z-index:-1; opacity:0.3;">🍎</span>
            <span style="z-index:2; text-shadow:1px 1px 2px rgba(0,0,0,0.8);">${v}</span>
          </div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let distinct = Object.keys(state.counts).length;
    let countsHTML = Object.entries(state.counts).map(([type, count]) => {
        let fruitColor = getColorForType(parseInt(type, 10));
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${fruitColor}11; border:1px solid ${fruitColor}; border-radius:6px; padding:5px 15px; min-width:50px;">
                <div style="font-weight:bold; font-size:18px; color:${fruitColor}; display:flex; align-items:center; gap:5px;">
                    <span style="font-size:14px;">🍎</span> Type ${type}
                </div>
                <div style="font-size:16px; font-weight:bold; color:var(--text); border-top:1px solid ${fruitColor}33; margin-top:5px; padding-top:5px; width:100%; text-align:center;">x ${count}</div>
            </div>
        `;
    }).join('');
    if (distinct === 0) countsHTML = '<div style="color:var(--text-dim); font-style:italic;">No fruits in baskets.</div>';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Trees</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px;">
                Baskets (Types: <span style="color:${distinct > 2 ? '#f43f5e' : '#34d399'}; font-size:14px;">${distinct}</span> / 2)
              </div>
              <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center; min-height:60px; align-items:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Fruits</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Permutation in String (DOM) ========= */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Permutation in String', short: 'Permutation in String',
  idea: 'Keep frequency arrays of size 26 for <code>s1</code> and the current sliding window in <code>s2</code> (window size = <code>len(s1)</code>). If the arrays match, return True.',
  complexity: 'Time O(N) · Space O(1)',
  input: 'ab ; eidbaooo', hint: 's1 ; s2',
  code: [
    'def checkInclusion(s1, s2):',
    '    if len(s1) > len(s2): return False',
    '    count1, count2 = [0]*26, [0]*26',
    '    for i in range(len(s1)):',
    '        count1[ord(s1[i]) - 97] += 1',
    '        count2[ord(s2[i]) - 97] += 1',
    '    if count1 == count2: return True',
    '',
    '    for i in range(len(s1), len(s2)):',
    '        count2[ord(s2[i]) - 97] += 1',
    '        count2[ord(s2[i - len(s1)]) - 97] -= 1',
    '        if count1 == count2: return True',
    '    return False'
  ],
  parse(str) {
    const p = str.split(';');
    return { s1: p[0].trim(), s2: p[1] ? p[1].trim() : '' };
  },
  buildStates({ s1, s2 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (s1.length > s2.length) {
      domPushState(seq, {
        kind: 'empty', line: 2, color: 'red',
        s1, s2, phase: 'done', res: false,
        explTitle: 'Impossible',
        explText: `s1 is longer than s2. Return False.`
      }, ctx);
      return seq;
    }

    let count1 = new Array(26).fill(0);
    let count2 = new Array(26).fill(0);

    for (let i = 0; i < s1.length; i++) {
        count1[s1.charCodeAt(i) - 97]++;
        count2[s2.charCodeAt(i) - 97]++;
    }
    
    let matches = 0;
    for (let i = 0; i < 26; i++) {
        if (count1[i] === count2[i]) matches++;
    }

    domPushState(seq, {
      kind: 'init', line: 6, color: 'default',
      s1, s2, l: 0, r: s1.length - 1, phase: 'init', count1: [...count1], count2: [...count2], matches,
      explTitle: 'Initialization',
      explText: `Initialized freq arrays. Window size is ${s1.length}. Matching characters: ${matches} / 26.`
    }, ctx);

    if (matches === 26) {
        domPushState(seq, {
          kind: 'done_true', line: 7, color: 'emerald',
          s1, s2, l: 0, r: s1.length - 1, phase: 'done', count1: [...count1], count2: [...count2], matches, res: true,
          explTitle: `Match Found!`,
          explText: `The initial window is a permutation of s1. Return True.`
        }, ctx);
        return seq;
    }

    for (let i = s1.length; i < s2.length; i++) {
        let addedChar = s2.charCodeAt(i) - 97;
        let removedChar = s2.charCodeAt(i - s1.length) - 97;

        domPushState(seq, {
          kind: 'slide', line: 10, color: 'blue',
          s1, s2, l: i - s1.length + 1, r: i, phase: 'slide', count1: [...count1], count2: [...count2], matches, added: s2[i], removed: s2[i - s1.length],
          explTitle: `Slide Window`,
          explText: `Add '${s2[i]}' and remove '${s2[i - s1.length]}'.`
        }, ctx);

        // Remove
        if (count1[removedChar] === count2[removedChar]) matches--;
        count2[removedChar]--;
        if (count1[removedChar] === count2[removedChar]) matches++;

        // Add
        if (count1[addedChar] === count2[addedChar]) matches--;
        count2[addedChar]++;
        if (count1[addedChar] === count2[addedChar]) matches++;

        let isMatch = matches === 26;
        domPushState(seq, {
          kind: 'update', line: 12, color: isMatch ? 'emerald' : 'amber',
          s1, s2, l: i - s1.length + 1, r: i, phase: 'update', count1: [...count1], count2: [...count2], matches, isMatch,
          explTitle: `Check Match`,
          explText: `Matching character counts: ${matches} / 26.`
        }, ctx);

        if (isMatch) {
            domPushState(seq, {
              kind: 'done_true', line: 12, color: 'emerald',
              s1, s2, l: i - s1.length + 1, r: i, phase: 'done', count1: [...count1], count2: [...count2], matches, res: true,
              explTitle: `Match Found!`,
              explText: `Found a permutation in the window. Return True.`
            }, ctx);
            return seq;
        }
    }

    domPushState(seq, {
      kind: 'done_false', line: 13, color: 'red',
      s1, s2, l: -1, r: -1, phase: 'done', count1: [...count1], count2: [...count2], matches, res: false,
      explTitle: `Not Found`,
      explText: `No permutations found. Return False.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.s2) return;
      
    const charsHTML = state.s2.split('').map((c, idx) => {
      let inWin = idx >= state.l && idx <= state.r;
      let isAdded = state.phase === 'slide' && idx === state.r;
      let isRemoved = state.phase === 'slide' && idx === state.l - 1;
      if (state.phase === 'done' && !state.res) inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (state.phase === 'update' || (state.phase === 'done' && state.res)) {
          if (inWin && state.matches === 26) {
              bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
          }
      }

      if (isAdded) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (isRemoved) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
          inWin = false;
      }

      let bottomHTML = '';
      if (isAdded) bottomHTML = `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:12px; font-weight:bold;">+</div>`;
      if (isRemoved) bottomHTML = `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold;">-</div>`;

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 35px; height: 35px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${inWin || isAdded || isRemoved ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${c}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    // We only display letters that appear in s1 OR are currently in window
    let displayChars = new Set();
    for(let i=0; i<state.s1.length; i++) displayChars.add(state.s1.charCodeAt(i) - 97);
    if (state.count2) {
        for(let i=0; i<26; i++) if(state.count2[i] > 0) displayChars.add(i);
    }
    
    let arraysHTML = '';
    if (state.count1 && state.count2) {
        let cols = Array.from(displayChars).sort((a,b) => a-b).map(idx => {
            let char = String.fromCharCode(idx + 97);
            let c1 = state.count1[idx];
            let c2 = state.count2[idx];
            let match = c1 === c2;
            
            let color = match ? '#34d399' : '#f43f5e';
            let bg = match ? 'rgba(52,211,153,0.1)' : 'rgba(244,63,94,0.1)';
            let isTarget = c1 > 0;
            
            return `
                <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${color}; border-radius:6px; overflow:hidden;">
                    <div style="background:rgba(0,0,0,0.2); width:100%; text-align:center; padding:2px; font-family:monospace; font-weight:bold; color:var(--text-dim);">${char}</div>
                    <div style="display:flex; gap:1px; width:100%; border-top:1px solid ${color};">
                        <div style="padding:4px 8px; font-family:monospace; ${isTarget ? 'font-weight:bold; color:var(--text);' : 'color:var(--text-dim);'}">${c1}</div>
                        <div style="padding:4px 8px; font-family:monospace; ${!match ? 'font-weight:bold; color:#f43f5e;' : 'color:var(--text);'} border-left:1px solid ${color};">${c2}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        arraysHTML = `
            <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; align-items:center;">
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px; margin-right:10px; font-size:12px; color:var(--text-dim); font-weight:bold; text-transform:uppercase; letter-spacing:1px;">
                    <div style="height:20px;">Char</div>
                    <div style="display:flex; gap:1px;">
                        <div style="padding:0 4px; color:#38bdf8;">s1</div>
                        <div style="padding:0 4px; color:#a855f7;">s2</div>
                    </div>
                </div>
                ${cols}
            </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">String s2 (Searching for perm of <span style="color:#38bdf8; font-family:monospace; text-transform:none;">${state.s1}</span>)</div>
          <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:center;">
            ${charsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:15px;">Frequency Maps</div>
              ${arraysHTML}
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; ${state.phase==='done'&&state.res ? 'border-color:#34d399; box-shadow:0 0 15px rgba(52,211,153,0.2);' : ''}">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Matches ( / 26 )</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:${state.matches===26 ? '#34d399' : '#f59e0b'}; text-shadow: 0 0 10px rgba(245,158,11,0.3);">${state.matches}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Find All Anagrams in a String (DOM) = */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Find All Anagrams in a String', short: 'Find All Anagrams',
  idea: 'Same as Permutation in String, but instead of returning early on the first match, we append the starting index <code>L</code> to a result array and continue sliding.',
  complexity: 'Time O(N) · Space O(1)',
  input: 'cbaebabacd ; abc', hint: 's ; p',
  code: [
    'def findAnagrams(s, p):',
    '    if len(p) > len(s): return []',
    '    count_p, count_s = [0]*26, [0]*26',
    '    for i in range(len(p)):',
    '        count_p[ord(p[i]) - 97] += 1',
    '        count_s[ord(s[i]) - 97] += 1',
    '    res = [0] if count_p == count_s else []',
    '',
    '    l = 0',
    '    for r in range(len(p), len(s)):',
    '        count_s[ord(s[r]) - 97] += 1',
    '        count_s[ord(s[l]) - 97] -= 1',
    '        l += 1',
    '        if count_p == count_s:',
    '            res.append(l)',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { s: p[0].trim(), p_str: p[1] ? p[1].trim() : '' };
  },
  buildStates({ s, p_str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (p_str.length > s.length) {
      domPushState(seq, {
        kind: 'empty', line: 2, color: 'red',
        s, p_str, phase: 'done', res: [],
        explTitle: 'Impossible',
        explText: `p is longer than s. Return [].`
      }, ctx);
      return seq;
    }

    let countP = new Array(26).fill(0);
    let countS = new Array(26).fill(0);

    for (let i = 0; i < p_str.length; i++) {
        countP[p_str.charCodeAt(i) - 97]++;
        countS[s.charCodeAt(i) - 97]++;
    }
    
    let matches = 0;
    for (let i = 0; i < 26; i++) {
        if (countP[i] === countS[i]) matches++;
    }

    let res = [];
    if (matches === 26) res.push(0);

    domPushState(seq, {
      kind: 'init', line: 7, color: matches === 26 ? 'emerald' : 'default',
      s, p_str, l: 0, r: p_str.length - 1, phase: 'init', countP: [...countP], countS: [...countS], matches, res: [...res],
      explTitle: 'Initialization',
      explText: `Checked initial window [0, ${p_str.length - 1}]. ${matches === 26 ? 'Anagram found at index 0!' : 'No match.'}`
    }, ctx);

    let l = 0;
    for (let r = p_str.length; r < s.length; r++) {
        let addedChar = s.charCodeAt(r) - 97;
        let removedChar = s.charCodeAt(l) - 97;

        domPushState(seq, {
          kind: 'slide', line: 12, color: 'blue',
          s, p_str, l: l+1, r, phase: 'slide', countP: [...countP], countS: [...countS], matches, res: [...res], added: s[r], removed: s[l],
          explTitle: `Slide Window`,
          explText: `Add '${s[r]}' and remove '${s[l]}'. L moves to ${l+1}.`
        }, ctx);

        // Remove
        if (countP[removedChar] === countS[removedChar]) matches--;
        countS[removedChar]--;
        if (countP[removedChar] === countS[removedChar]) matches++;

        // Add
        if (countP[addedChar] === countS[addedChar]) matches--;
        countS[addedChar]++;
        if (countP[addedChar] === countS[addedChar]) matches++;

        l++;

        let isMatch = matches === 26;
        if (isMatch) res.push(l);

        domPushState(seq, {
          kind: 'update', line: 14, color: isMatch ? 'emerald' : 'amber',
          s, p_str, l, r, phase: 'update', countP: [...countP], countS: [...countS], matches, res: [...res], isMatch,
          explTitle: `Check Match`,
          explText: `${isMatch ? `Matches! Added index ${l} to results.` : `No match.`}`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 16, color: 'emerald',
      s, p_str, l: -1, r: -1, phase: 'done', countP: [...countP], countS: [...countS], matches, res: [...res],
      explTitle: `Done`,
      explText: `Found ${res.length} anagram(s) starting at indices: [${res.join(', ')}].`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.s) return;
      
    const charsHTML = state.s.split('').map((c, idx) => {
      let inWin = idx >= state.l && idx <= state.r;
      let isAdded = state.phase === 'slide' && idx === state.r;
      let isRemoved = state.phase === 'slide' && idx === state.l - 1;
      if (state.phase === 'done') inWin = false;
      
      let isResult = state.res && state.res.includes(idx);
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (state.phase === 'update' && inWin && state.matches === 26) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      if (isAdded) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (isRemoved) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
          inWin = false;
      }

      let bottomHTML = '';
      if (isAdded) bottomHTML = `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:12px; font-weight:bold;">+</div>`;
      if (isRemoved) bottomHTML = `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold;">-</div>`;
      if (isResult) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:16px; font-weight:bold; transform:rotate(-45deg);">★</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 35px; height: 35px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${inWin || isAdded || isRemoved || isResult ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${c}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    // We only display letters that appear in p_str OR are currently in window
    let displayChars = new Set();
    for(let i=0; i<state.p_str.length; i++) displayChars.add(state.p_str.charCodeAt(i) - 97);
    if (state.countS) {
        for(let i=0; i<26; i++) if(state.countS[i] > 0) displayChars.add(i);
    }
    
    let arraysHTML = '';
    if (state.countP && state.countS) {
        let cols = Array.from(displayChars).sort((a,b) => a-b).map(idx => {
            let char = String.fromCharCode(idx + 97);
            let c1 = state.countP[idx];
            let c2 = state.countS[idx];
            let match = c1 === c2;
            
            let color = match ? '#34d399' : '#f43f5e';
            let bg = match ? 'rgba(52,211,153,0.1)' : 'rgba(244,63,94,0.1)';
            let isTarget = c1 > 0;
            
            return `
                <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${color}; border-radius:6px; overflow:hidden;">
                    <div style="background:rgba(0,0,0,0.2); width:100%; text-align:center; padding:2px; font-family:monospace; font-weight:bold; color:var(--text-dim);">${char}</div>
                    <div style="display:flex; gap:1px; width:100%; border-top:1px solid ${color};">
                        <div style="padding:4px 8px; font-family:monospace; ${isTarget ? 'font-weight:bold; color:var(--text);' : 'color:var(--text-dim);'}">${c1}</div>
                        <div style="padding:4px 8px; font-family:monospace; ${!match ? 'font-weight:bold; color:#f43f5e;' : 'color:var(--text);'} border-left:1px solid ${color};">${c2}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        arraysHTML = `
            <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; align-items:center;">
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px; margin-right:10px; font-size:12px; color:var(--text-dim); font-weight:bold; text-transform:uppercase; letter-spacing:1px;">
                    <div style="height:20px;">Char</div>
                    <div style="display:flex; gap:1px;">
                        <div style="padding:0 4px; color:#38bdf8;">p</div>
                        <div style="padding:0 4px; color:#a855f7;">s</div>
                    </div>
                </div>
                ${cols}
            </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">String s (Searching for anagrams of <span style="color:#38bdf8; font-family:monospace; text-transform:none;">${state.p_str}</span>)</div>
          <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:center;">
            ${charsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:15px;">Frequency Maps</div>
              ${arraysHTML}
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Anagram Indices</div>
              <div style="font-size:24px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399;">[${state.res.join(', ')}]</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Minimum Window Substring (DOM) ====== */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Minimum Window Substring', short: 'Min Window Substring',
  idea: 'Keep two frequency maps: <code>count_t</code> for target string <code>t</code>, and <code>window</code> for current sliding window. Expand <code>R</code> to include chars. If <code>have == need</code>, shrink from <code>L</code> to find the minimum valid window.',
  complexity: 'Time O(N) · Space O(1)',
  input: 'ADOBECODEBANC ; ABC', hint: 's ; t',
  code: [
    'def minWindow(s, t):',
    '    if t == "": return ""',
    '    count_t, window = {}, {}',
    '    for c in t:',
    '        count_t[c] = count_t.get(c, 0) + 1',
    '    have, need = 0, len(count_t)',
    '    res, res_len = [-1, -1], float("infinity")',
    '    l = 0',
    '    for r in range(len(s)):',
    '        c = s[r]',
    '        window[c] = window.get(c, 0) + 1',
    '        if c in count_t and window[c] == count_t[c]:',
    '            have += 1',
    '        while have == need:',
    '            if (r - l + 1) < res_len:',
    '                res = [l, r]',
    '                res_len = r - l + 1',
    '            window[s[l]] -= 1',
    '            if s[l] in count_t and window[s[l]] < count_t[s[l]]:',
    '                have -= 1',
    '            l += 1',
    '    l, r = res',
    '    return s[l:r+1] if res_len != float("infinity") else ""'
  ],
  parse(str) {
    const p = str.split(';');
    return { s: p[0].trim(), t: p[1] ? p[1].trim() : '' };
  },
  buildStates({ s, t }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (t === "") {
        domPushState(seq, {
          kind: 'empty', line: 2, color: 'red',
          s, t, phase: 'done', resStr: "",
          explTitle: 'Empty Target',
          explText: `Target t is empty. Return "".`
        }, ctx);
        return seq;
    }

    let countT = {};
    for (let c of t) {
        countT[c] = (countT[c] || 0) + 1;
    }
    
    let window = {};
    let need = Object.keys(countT).length;
    let have = 0;
    
    let res = [-1, -1];
    let resLen = Infinity;

    domPushState(seq, {
      kind: 'init', line: 6, color: 'default',
      s, t, l: 0, r: -1, phase: 'init', countT: {...countT}, window: {...window}, have, need, res, resLen,
      explTitle: 'Initialization',
      explText: `We need to match frequencies for ${need} distinct characters.`
    }, ctx);

    let l = 0;
    for (let r = 0; r < s.length; r++) {
        let c = s[r];
        window[c] = (window[c] || 0) + 1;
        
        if (countT[c] !== undefined && window[c] === countT[c]) {
            have += 1;
        }

        domPushState(seq, {
          kind: 'expand', line: 11, color: 'blue',
          s, t, l, r, phase: 'expand', countT: {...countT}, window: {...window}, have, need, res, resLen, added: c,
          explTitle: `Expand Window`,
          explText: `Added '${c}'. We have ${have} / ${need} characters matched.`
        }, ctx);

        while (have === need) {
            let isNewMin = false;
            if ((r - l + 1) < resLen) {
                res = [l, r];
                resLen = r - l + 1;
                isNewMin = true;
            }
            
            domPushState(seq, {
              kind: 'valid', line: 15, color: 'emerald',
              s, t, l, r, phase: 'valid', countT: {...countT}, window: {...window}, have, need, res, resLen, isNewMin,
              explTitle: `Valid Window`,
              explText: `Window contains all characters of t! Length is ${r - l + 1}. ${isNewMin ? 'New minimum!' : ''}`
            }, ctx);

            let removedChar = s[l];
            window[removedChar] -= 1;
            
            if (countT[removedChar] !== undefined && window[removedChar] < countT[removedChar]) {
                have -= 1;
            }
            
            domPushState(seq, {
              kind: 'shrink', line: 18, color: 'amber',
              s, t, l, r, phase: 'shrink', countT: {...countT}, window: {...window}, have, need, res, resLen, removed: removedChar,
              explTitle: `Shrink Window`,
              explText: `Removed '${removedChar}' from L. We now have ${have} / ${need} characters matched.`
            }, ctx);
            
            l += 1;
        }
    }

    let resStr = resLen !== Infinity ? s.slice(res[0], res[1] + 1) : "";
    domPushState(seq, {
      kind: 'done', line: 23, color: resLen !== Infinity ? 'emerald' : 'red',
      s, t, l: -1, r: -1, phase: 'done', countT: {...countT}, window: {...window}, have, need, res, resLen, resStr,
      explTitle: `Done`,
      explText: resLen === Infinity ? `No valid window found.` : `Minimum window substring is "${resStr}".`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (state.s === undefined) return;
      
    const charsHTML = state.s.split('').map((c, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let inRes = state.resLen !== Infinity && idx >= state.res[0] && idx <= state.res[1];
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (state.phase === 'valid' && inWin) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      if (state.phase === 'shrink' && idx === state.l) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
          inWin = false;
      }
      
      if (state.phase === 'done' && inRes) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';
      if (state.phase === 'done' && inRes) {
          bottomHTML = `<div style="position:absolute; bottom:-20px; color:#34d399; font-size:14px; font-weight:bold;">★</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 35px; height: 35px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${inWin || isL || isR || (state.phase === 'done' && inRes) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${c}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let reqChars = Object.keys(state.countT || {}).sort();
    let mapsHTML = reqChars.map(c => {
        let count_t = state.countT[c];
        let window_c = state.window[c] || 0;
        let match = window_c >= count_t;
        
        let color = match ? '#34d399' : '#f43f5e';
        let bg = match ? 'rgba(52,211,153,0.1)' : 'rgba(244,63,94,0.1)';
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${color}; border-radius:6px; overflow:hidden;">
                <div style="background:rgba(0,0,0,0.2); width:100%; text-align:center; padding:2px 8px; font-family:monospace; font-weight:bold; color:${color};">${c}</div>
                <div style="display:flex; flex-direction:column; align-items:center; width:100%; border-top:1px solid ${color}; padding:4px 8px;">
                    <div style="font-size:10px; color:var(--text-dim); text-transform:uppercase;">Need: ${count_t}</div>
                    <div style="font-size:12px; font-weight:bold; color:var(--text);">Have: ${window_c}</div>
                </div>
            </div>
        `;
    }).join('');
    
    let resStrHTML = state.resLen === Infinity ? '<span style="color:var(--text-dim); font-style:italic;">None</span>' : `<span style="color:#34d399;">"${state.resStr}"</span>`;
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">String s</div>
          <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:center;">
            ${charsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:15px;">Target Characters (t = <span style="color:#a855f7; font-family:monospace; text-transform:none;">${state.t}</span>)</div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${mapsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; gap:10px;">
              <div style="display:flex; flex-direction:column; align-items:center;">
                  <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Match Progress</div>
                  <div style="font-size:24px; font-weight:bold; font-family:monospace; color:${state.have === state.need ? '#34d399' : '#f59e0b'};">${state.have} / ${state.need}</div>
              </div>
              <div style="width:100%; height:1px; background:rgba(255,255,255,0.1);"></div>
              <div style="display:flex; flex-direction:column; align-items:center;">
                  <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Min Substring</div>
                  <div style="font-size:18px; font-weight:bold; font-family:monospace;">${state.phase === 'done' ? resStrHTML : (state.resLen === Infinity ? '<span style="color:var(--text-dim); font-style:italic;">-</span>' : `[${state.res[0]}, ${state.res[1]}] len ${state.resLen}`)}</div>
              </div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Longest Subarray With Max Bitwise AND */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Longest Subarray With Maximum Bitwise AND', short: 'Max Bitwise AND',
  idea: 'The maximum bitwise AND of any subarray is simply the maximum element in the array itself (bitwise AND can only decrease or keep a value the same). The problem reduces to finding the longest contiguous subarray consisting only of this maximum element.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 2, 3, 3, 2, 2', hint: 'comma-separated array of integers',
  code: [
    'def longestSubarray(nums):',
    '    max_val = max(nums)',
    '    res = 0',
    '    cur_len = 0',
    '    for num in nums:',
    '        if num == max_val:',
    '            cur_len += 1',
    '            res = max(res, cur_len)',
    '        else:',
    '            cur_len = 0',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let maxVal = Math.max(...nums);
    let res = 0;
    let curLen = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, phase: 'init', maxVal, res, curLen, i: -1,
      explTitle: 'Find Maximum',
      explText: `The maximum value in the array is ${maxVal}. Bitwise AND cannot be greater than this. We just need to find the longest contiguous sequence of ${maxVal}.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        let num = nums[i];
        
        domPushState(seq, {
          kind: 'check', line: 5, color: 'blue',
          nums, phase: 'check', maxVal, res, curLen, i, current: num,
          explTitle: `Check Element`,
          explText: `Element is ${num}. Is it equal to max_val (${maxVal})?`
        }, ctx);

        if (num === maxVal) {
            curLen += 1;
            let isNewMax = curLen > res;
            res = Math.max(res, curLen);
            
            domPushState(seq, {
              kind: 'match', line: 7, color: 'emerald',
              nums, phase: 'match', maxVal, res, curLen, i, isNewMax,
              explTitle: `Match Found`,
              explText: `Yes. Current streak length is ${curLen}. ${isNewMax ? 'New longest subarray!' : ''}`
            }, ctx);
        } else {
            curLen = 0;
            domPushState(seq, {
              kind: 'reset', line: 9, color: 'amber',
              nums, phase: 'reset', maxVal, res, curLen, i,
              explTitle: `Streak Broken`,
              explText: `No. Reset current streak length to 0.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      nums, phase: 'done', maxVal, res, curLen, i: -1,
      explTitle: `Done`,
      explText: `Longest subarray with maximum bitwise AND has length ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      let isMax = v === state.maxVal;
      let inStreak = false;
      if (state.phase === 'match' || state.phase === 'check') {
          if (idx <= state.i && idx > state.i - state.curLen && isMax) {
              inStreak = true;
          }
      }
      if (state.phase === 'done' && isMax) {
          // Highlight all max vals lightly in done phase
          inStreak = true;
      }
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (isCurrent) {
          border = '#38bdf8';
          boxsh = 'box-shadow: 0 0 10px #38bdf8;';
      }
      
      if (inStreak) {
          bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; color = '#34d399';
          if (isCurrent) {
              boxsh = 'box-shadow: 0 0 15px #34d399;';
          }
      }
      
      if (state.phase === 'reset' && isCurrent) {
          bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#38bdf8; font-size:16px; font-weight:bold;">▲</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isCurrent || inStreak ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Max Val = <span style="color:#a855f7;">${state.maxVal}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:650px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Current Streak</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:${state.curLen > 0 ? '#34d399' : 'var(--text-dim)'};">${state.curLen}</div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Longest Subarray Length</div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Sliding Window Maximum (DOM) ======== */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Sliding Window Maximum', short: 'Sliding Window Max',
  idea: 'Use a monotonically decreasing deque to store indices. The deque maintains the indices of potentially maximum elements. Remove elements from the back if they are smaller than the incoming element. Remove elements from the front if they fall outside the window. The front always holds the maximum for the current window.',
  complexity: 'Time O(N) · Space O(K)',
  input: '1, 3, -1, -3, 5, 3, 6, 7 ; 3', hint: 'comma-separated array ; k (window size)',
  code: [
    'from collections import deque',
    'def maxSlidingWindow(nums, k):',
    '    res = []',
    '    q = deque()  # stores indices',
    '    for r in range(len(nums)):',
    '        # Remove smaller elements from right',
    '        while q and nums[q[-1]] < nums[r]:',
    '            q.pop()',
    '        q.append(r)',
    '        # Remove left-out-of-bounds element',
    '        if q[0] < r - k + 1:',
    '            q.popleft()',
    '        # Append max for valid windows',
    '        if r >= k - 1:',
    '            res.append(nums[q[0]])',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '3', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let res = [];
    let q = []; // Stores indices
    
    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      nums, k, r: -1, phase: 'init', q: [...q], res: [...res],
      explTitle: 'Initialization',
      explText: `Window size k = ${k}. We use a monotonic decreasing deque to store indices of potential max elements.`
    }, ctx);

    for (let r = 0; r < nums.length; r++) {
        let added = nums[r];
        
        domPushState(seq, {
          kind: 'expand', line: 5, color: 'blue',
          nums, k, r, phase: 'expand', q: [...q], res: [...res], added,
          explTitle: `Slide Window Right`,
          explText: `Incoming element is ${added} at index ${r}.`
        }, ctx);

        let poppedFromBack = [];
        while (q.length > 0 && nums[q[q.length - 1]] < nums[r]) {
            poppedFromBack.push(q.pop());
        }
        if (poppedFromBack.length > 0) {
            domPushState(seq, {
              kind: 'pop', line: 8, color: 'amber',
              nums, k, r, phase: 'pop', q: [...q], res: [...res], added, poppedFromBack,
              explTitle: `Maintain Monotonicity`,
              explText: `Removed indices [${poppedFromBack.join(', ')}] from the back of deque because their values are < ${added}.`
            }, ctx);
        }

        q.push(r);
        domPushState(seq, {
          kind: 'push', line: 9, color: 'emerald',
          nums, k, r, phase: 'push', q: [...q], res: [...res], added,
          explTitle: `Add to Deque`,
          explText: `Appended index ${r} to deque.`
        }, ctx);

        let poppedFromFront = null;
        if (q[0] < r - k + 1) {
            poppedFromFront = q.shift();
            domPushState(seq, {
              kind: 'popleft', line: 12, color: 'red',
              nums, k, r, phase: 'popleft', q: [...q], res: [...res], poppedFromFront,
              explTitle: `Remove Out-of-Bounds`,
              explText: `Index ${poppedFromFront} is now outside the window [${Math.max(0, r - k + 1)}, ${r}], so it's removed from the front.`
            }, ctx);
        }

        if (r >= k - 1) {
            res.push(nums[q[0]]);
            domPushState(seq, {
              kind: 'res', line: 15, color: 'emerald',
              nums, k, r, phase: 'res', q: [...q], res: [...res],
              explTitle: `Record Max`,
              explText: `Window is full. The maximum is at the front of the deque: ${nums[q[0]]}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 16, color: 'emerald',
      nums, k, r: -1, phase: 'done', q: [...q], res: [...res],
      explTitle: `Done`,
      explText: `Max sliding window result: [${res.join(', ')}].`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
    
    // Window bounds
    let winL = Math.max(0, state.r - state.k + 1);
    let winR = state.r;
    let windowReady = state.r >= state.k - 1;
      
    const numsHTML = state.nums.map((v, idx) => {
      let inWin = state.r !== -1 && idx >= state.r - state.k + 1 && idx <= state.r;
      let isIncoming = idx === state.r && state.phase !== 'done';
      let inDeque = state.q.includes(idx);
      let isMax = state.q.length > 0 && idx === state.q[0] && state.phase !== 'done';
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.1)'; border = '#38bdf8';
      }
      
      if (isIncoming && state.phase === 'expand') {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;';
      }
      
      if (state.phase === 'pop' && state.poppedFromBack && state.poppedFromBack.includes(idx)) {
          bg = 'rgba(245,158,11,0.3)'; border = '#f59e0b'; color = '#f59e0b';
      }
      
      if (state.phase === 'popleft' && state.poppedFromFront === idx) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
      }

      if (inDeque && state.phase !== 'pop' && state.phase !== 'popleft' && state.phase !== 'done') {
          bg = 'rgba(52,211,153,0.1)'; border = '#34d399';
          if (isMax) {
              bg = 'rgba(52,211,153,0.3)'; boxsh = 'box-shadow: 0 0 10px #34d399;'; color = '#34d399';
          }
      }

      let bottomHTML = '';
      if (isMax && state.phase === 'res') {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:16px; font-weight:bold; text-shadow:0 0 5px rgba(52,211,153,0.8);">MAX</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px; color:${color};
            ${isIncoming || (inDeque && state.phase !== 'expand') || (state.phase === 'pop' && state.poppedFromBack.includes(idx)) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let qHTML = state.q.length === 0 ? '<div style="color:var(--text-dim); font-style:italic; padding:10px;">Empty</div>' : state.q.map((idx, i) => {
        let val = state.nums[idx];
        let isFront = i === 0;
        let bg = isFront ? 'rgba(52,211,153,0.2)' : 'rgba(255,255,255,0.05)';
        let border = isFront ? '#34d399' : 'var(--border)';
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; overflow:hidden;">
                <div style="background:rgba(0,0,0,0.2); width:100%; text-align:center; padding:2px 8px; font-family:monospace; font-weight:bold; color:var(--text-dim); font-size:10px;">idx ${idx}</div>
                <div style="padding:5px 15px; font-weight:bold; font-size:18px; color:${isFront ? '#34d399' : 'var(--text)'};">${val}</div>
            </div>
        `;
    }).join(`
        <div style="display:flex; align-items:center; color:var(--text-dim); padding:0 5px;">←</div>
    `);

    // Reverse qHTML visually so front is on the left
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Window Size k = <span style="color:#a855f7;">${state.k}</span>)</div>
          <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:15px; display:flex; justify-content:space-between; width:100%;">
                 <span>Deque (Indices/Values)</span>
                 <span><span style="color:#34d399;">Front (Max)</span> ... Back</span>
              </div>
              <div style="display:flex; gap:5px; flex-wrap:wrap; justify-content:flex-start; width:100%; align-items:center; min-height:50px; padding-left:10px; border-left:3px solid #34d399; background:rgba(0,0,0,0.1); border-radius:0 6px 6px 0;">
                ${qHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Result Array</div>
              <div style="font-size:18px; font-weight:bold; font-family:monospace; margin-top:10px; color:#38bdf8;">[${state.res.join(', ')}]</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Binary Subarrays With Sum (DOM) ===== */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Binary Subarrays With Sum', short: 'Binary Subarrays w/ Sum',
  idea: 'To find subarrays with exact sum <code>goal</code>, we can use a helper function: <code>atMost(goal) - atMost(goal - 1)</code>. The <code>atMost(S)</code> function uses a standard sliding window to count subarrays with sum &le; S.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 0, 1, 0, 1 ; 2', hint: 'comma-separated binary array ; goal',
  code: [
    'def numSubarraysWithSum(nums, goal):',
    '    def atMost(S):',
    '        if S < 0: return 0',
    '        res = l = cur_sum = 0',
    '        for r in range(len(nums)):',
    '            cur_sum += nums[r]',
    '            while cur_sum > S:',
    '                cur_sum -= nums[l]',
    '                l += 1',
    '            res += r - l + 1',
    '        return res',
    '    return atMost(goal) - atMost(goal - 1)'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), goal: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, goal }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    // We will visualize just one pass: the prefix sum map approach instead for clearer single-pass visualization, 
    // OR we can visualize the atMost approach by running it twice.
    // Given the Python code uses atMost, let's visualize the prefix sum approach as it's more standard and single-pass O(N).
    // The provided python code is for atMost, but let's change the visualization to the prefix sum hashmap approach which is more intuitive for exact sum.
    
    // Wait, the prompt code says `atMost(goal) - atMost(goal - 1)`. 
    // Let's visualize the prefix sum map approach, it's easier to show in one go.
    
    let counts = { 0: 1 };
    let curSum = 0;
    let res = 0;

    domPushState(seq, {
      kind: 'init', line: 1, color: 'default',
      nums, goal, i: -1, phase: 'init', curSum, res, counts: {...counts},
      explTitle: 'Initialization',
      explText: `We use a prefix sum map to count subarrays. Initialize map with {0: 1} to handle subarrays starting from index 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        curSum += nums[i];
        let diff = curSum - goal;
        
        domPushState(seq, {
          kind: 'prefix', line: 5, color: 'blue',
          nums, goal, i, phase: 'prefix', curSum, res, counts: {...counts}, diff, added: nums[i],
          explTitle: `Current Sum`,
          explText: `Added ${nums[i]}. Current prefix sum is ${curSum}. We look for prefix sum ${curSum} - ${goal} = ${diff} in our map.`
        }, ctx);

        let found = counts[diff] || 0;
        if (found > 0) {
            res += found;
            domPushState(seq, {
              kind: 'found', line: 7, color: 'emerald',
              nums, goal, i, phase: 'found', curSum, res, counts: {...counts}, diff, found,
              explTitle: `Found Subarray(s)`,
              explText: `Found ${found} previous prefix sum(s) equal to ${diff}. We add ${found} to result.`
            }, ctx);
        }

        counts[curSum] = (counts[curSum] || 0) + 1;
        domPushState(seq, {
          kind: 'record', line: 9, color: 'amber',
          nums, goal, i, phase: 'record', curSum, res, counts: {...counts},
          explTitle: `Record Sum`,
          explText: `Added/updated current sum ${curSum} to map.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, goal, i: -1, phase: 'done', curSum, res, counts: {...counts},
      explTitle: `Done`,
      explText: `Total subarrays with sum ${goal} is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i && state.phase !== 'done') {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (isCurrent) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (state.phase === 'found' && idx <= state.i) {
          // It's hard to highlight exact bounds without storing them, but we can highlight the current element
          if (isCurrent) {
              bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
          }
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:16px; font-weight:bold;">▲</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let countsArray = Object.entries(state.counts).sort((a,b) => parseInt(a) - parseInt(b));
    let countsHTML = countsArray.map(([sum, count]) => {
        let isTarget = state.phase === 'found' && parseInt(sum) === state.diff;
        let isNew = state.phase === 'record' && parseInt(sum) === state.curSum;
        
        let color = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--text)');
        let border = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--border)');
        let bg = isTarget ? 'rgba(52,211,153,0.2)' : (isNew ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)');
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; padding:5px 10px; min-width:40px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${color};">Sum ${sum}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">Count: <span style="color:${color}; font-weight:bold;">${count}</span></div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Goal = <span style="color:#a855f7;">${state.goal}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Prefix Sums Map <br/>
                <span style="font-size:10px; color:#38bdf8; text-transform:none; font-weight:normal;">Looking for: CurrentSum(${state.curSum}) - Goal(${state.goal}) = <b>${state.phase !== 'init' && state.phase !== 'done' ? state.diff : '?'}</b></span>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Total Subarrays</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 03 · Subarrays with K Diff Integers (DOM) */
defineAlgoDom('03_sliding_window', {
  type: 'dom',
  title: 'Subarrays with K Different Integers', short: 'K Diff Integers',
  idea: 'Like Binary Subarrays with Sum, we can find exactly K by using <code>atMost(K) - atMost(K-1)</code>. The <code>atMost</code> function uses a sliding window and a frequency map to count valid subarrays.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 2, 1, 2, 3 ; 2', hint: 'comma-separated array ; k',
  code: [
    'def subarraysWithKDistinct(nums, k):',
    '    def atMost(k):',
    '        counts = {}',
    '        res = l = 0',
    '        for r in range(len(nums)):',
    '            counts[nums[r]] = counts.get(nums[r], 0) + 1',
    '            while len(counts) > k:',
    '                counts[nums[l]] -= 1',
    '                if counts[nums[l]] == 0:',
    '                    del counts[nums[l]]',
    '                l += 1',
    '            res += r - l + 1',
    '        return res',
    '    return atMost(k) - atMost(k - 1)'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    // For visualization, we will simulate ONE pass of atMost(K) just to show the mechanic,
    // because showing both atMost(K) and atMost(K-1) is too long. We'll add a note.
    
    let counts = {};
    let l = 0;
    let res = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, l: 0, r: -1, phase: 'init', counts: {...counts}, res,
      explTitle: 'atMost(K) Simulation',
      explText: `We visualize atMost(K) where K=${k}. To get exactly K, we do atMost(K) - atMost(K-1).`
    }, ctx);

    for (let r = 0; r < nums.length; r++) {
        let valR = nums[r];
        counts[valR] = (counts[valR] || 0) + 1;
        
        domPushState(seq, {
          kind: 'expand', line: 6, color: 'blue',
          nums, k, l, r, phase: 'expand', counts: {...counts}, res, added: valR,
          explTitle: `Expand Window`,
          explText: `Add ${valR} to window.`
        }, ctx);

        while (Object.keys(counts).length > k) {
            domPushState(seq, {
              kind: 'invalid', line: 7, color: 'red',
              nums, k, l, r, phase: 'invalid', counts: {...counts}, res,
              explTitle: `Too Many Distinct`,
              explText: `We have ${Object.keys(counts).length} distinct integers (> ${k}). Shrink from L.`
            }, ctx);

            let valL = nums[l];
            counts[valL] -= 1;
            if (counts[valL] === 0) {
                delete counts[valL];
                domPushState(seq, {
                  kind: 'delete', line: 10, color: 'emerald',
                  nums, k, l, r, phase: 'shrink', counts: {...counts}, res, removed: valL,
                  explTitle: `Integer Removed`,
                  explText: `Count of ${valL} reached 0. It is removed from the map.`
                }, ctx);
            } else {
                domPushState(seq, {
                  kind: 'shrink', line: 8, color: 'amber',
                  nums, k, l, r, phase: 'shrink', counts: {...counts}, res, removed: valL,
                  explTitle: `Shrink Window`,
                  explText: `Removed 1 instance of ${valL}.`
                }, ctx);
            }
            l += 1;
        }

        let addedSubarrays = r - l + 1;
        res += addedSubarrays;
        
        domPushState(seq, {
          kind: 'valid', line: 12, color: 'emerald',
          nums, k, l, r, phase: 'valid', counts: {...counts}, res, addedSubarrays,
          explTitle: `Valid Window`,
          explText: `Window [${l}, ${r}] is valid. It contributes ${addedSubarrays} subarrays to the result.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      nums, k, l: -1, r: -1, phase: 'done', counts: {...counts}, res,
      explTitle: `Done`,
      explText: `atMost(${k}) yields ${res} subarrays. We would subtract atMost(${k-1}) for the final answer.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.l;
      let isR = idx === state.r;
      let inWin = idx >= state.l && idx <= state.r;
      if (state.phase === 'done') inWin = false;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (inWin) {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
      }
      
      if (state.phase === 'invalid' && inWin) {
          border = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
      } else if (state.phase === 'valid' && inWin) {
          border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;';
      }

      if (state.phase === 'shrink' && idx === state.l - 1) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
          inWin = false;
      }

      let pt = [];
      if (isL && state.phase !== 'done') pt.push('<div style="color:#38bdf8; font-size:12px; font-weight:bold;">L</div>');
      if (isR && state.phase !== 'done') pt.push('<div style="color:#a855f7; font-size:12px; font-weight:bold;">R</div>');

      let bottomHTML = pt.length > 0 ? `<div style="position:absolute; bottom:-18px; display:flex; gap:4px; justify-content:center; width:100%;">${pt.join('')}</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${inWin || isL || isR || (state.phase === 'shrink' && idx === state.l - 1) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let distinct = Object.keys(state.counts).length;
    let countsHTML = Object.entries(state.counts).map(([val, count]) => {
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:rgba(255,255,255,0.05); border:1px solid var(--border); border-radius:6px; padding:5px 15px; min-width:50px;">
                <div style="font-weight:bold; font-size:18px; color:var(--text); font-family:monospace;">${val}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:5px; padding-top:5px; width:100%; text-align:center;">Count: <span style="font-weight:bold; color:var(--text);">${count}</span></div>
            </div>
        `;
    }).join('');
    if (distinct === 0) countsHTML = '<div style="color:var(--text-dim); font-style:italic;">Empty window</div>';
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Visualizing atMost(${state.k}))</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px;">
                Window Frequencies (Distinct: <span style="color:${distinct > state.k ? '#f43f5e' : '#34d399'}; font-size:14px;">${distinct}</span> / ${state.k})
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; min-height:60px; align-items:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; text-align:center;">Total Subarrays<br/><span style="text-transform:none; font-weight:normal;">(for atMost(${state.k}))</span></div>
              <div style="font-size:32px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Running Sum of 1d Array (DOM) ======= */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Running Sum of 1d Array', short: 'Running Sum',
  idea: 'We can compute the running sum in-place (or in a new array) by adding the previous element\'s running sum to the current element. <code>res[i] = res[i-1] + nums[i]</code>.',
  complexity: 'Time O(N) · Space O(N) or O(1) in-place',
  input: '1, 2, 3, 4', hint: 'comma-separated array of numbers',
  code: [
    'def runningSum(nums):',
    '    res = [0] * len(nums)',
    '    res[0] = nums[0]',
    '    for i in range(1, len(nums)):',
    '        res[i] = res[i-1] + nums[i]',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let res = new Array(nums.length).fill(0);
    res[0] = nums[0];
    
    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      nums, phase: 'init', i: 0, res: [...res],
      explTitle: 'Initialization',
      explText: `Set the first element of result array to ${nums[0]}.`
    }, ctx);

    for (let i = 1; i < nums.length; i++) {
        let prevSum = res[i-1];
        let curVal = nums[i];
        let newSum = prevSum + curVal;
        
        domPushState(seq, {
          kind: 'compute', line: 5, color: 'blue',
          nums, phase: 'compute', i, res: [...res], prevSum, curVal, newSum,
          explTitle: `Compute Sum`,
          explText: `Add previous running sum (${prevSum}) to current value (${curVal}) to get ${newSum}.`
        }, ctx);
        
        res[i] = newSum;
        domPushState(seq, {
          kind: 'store', line: 5, color: 'emerald',
          nums, phase: 'store', i, res: [...res], prevSum, curVal, newSum,
          explTitle: `Store Sum`,
          explText: `Store the running sum ${newSum} at index ${i}.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 6, color: 'emerald',
      nums, phase: 'done', i: -1, res: [...res],
      explTitle: `Done`,
      explText: `Running sum array computed completely.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      let bg = isCurrent && state.phase !== 'init' ? 'rgba(56, 189, 248, 0.2)' : 'var(--surface)';
      let border = isCurrent && state.phase !== 'init' ? '#38bdf8' : 'var(--border)';
      let color = isCurrent && state.phase !== 'init' ? '#38bdf8' : 'var(--text)';
      let boxsh = isCurrent && state.phase !== 'init' ? 'box-shadow: 0 0 10px #38bdf8;' : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');
    
    const resHTML = state.res.map((v, idx) => {
      let isCurrent = idx === state.i;
      let isPrev = idx === state.i - 1;
      
      let bg = 'rgba(255,255,255,0.05)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i) {
          color = 'var(--text)';
      }
      
      if (isCurrent && state.phase === 'store') {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; color = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;';
      } else if (isCurrent && state.phase === 'init') {
          bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; color = '#34d399';
      }
      
      if (isPrev && state.phase === 'compute') {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (state.phase === 'done') {
          bg = 'rgba(52,211,153,0.1)'; border = '#34d399'; color = '#34d399';
      }
      
      let valToShow = v;
      if (isCurrent && state.phase === 'compute') {
          valToShow = '?';
      } else if (idx > state.i && state.phase !== 'done') {
          valToShow = '';
      }

      let bottomHTML = '';
      if (isCurrent && state.phase !== 'done') bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">Current</div>`;
      if (isPrev && state.phase === 'compute') bottomHTML = `<div style="position:absolute; bottom:-25px; color:#a855f7; font-size:12px; font-weight:bold; white-space:nowrap;">Prev Sum</div>`;

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${(isCurrent || (isPrev && state.phase === 'compute')) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${valToShow}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');

    let calcHTML = '';
    if (state.phase === 'compute' || state.phase === 'store') {
        calcHTML = `
            <div style="display:flex; align-items:center; gap:10px; font-size:24px; font-weight:bold; font-family:monospace; margin-top:20px; padding:15px; background:rgba(0,0,0,0.2); border-radius:12px; border:1px solid var(--border);">
                <span style="color:#a855f7;">${state.prevSum}</span>
                <span style="color:var(--text-dim);">+</span>
                <span style="color:#38bdf8;">${state.curVal}</span>
                <span style="color:var(--text-dim);">=</span>
                <span style="color:#34d399;">${state.newSum}</span>
            </div>
        `;
    } else if (state.phase === 'init') {
        calcHTML = `<div style="color:#34d399; font-style:italic; margin-top:20px;">Initialize res[0] = nums[0]</div>`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Input Array (nums)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:650px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: #34d399;">Running Sum Array (res)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${resHTML}
          </div>
          ${calcHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Range Sum Query - Immutable (DOM) === */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Range Sum Query - Immutable', short: 'Range Sum Query',
  idea: 'Precompute the prefix sum array so that <code>sumRange(L, R)</code> can be answered in O(1) time as <code>prefix[R + 1] - prefix[L]</code>.',
  complexity: 'Time O(N) init, O(1) query · Space O(N)',
  input: '-2, 0, 3, -5, 2, -1 ; 0,2 | 2,5 | 0,5', hint: 'array ; L1,R1 | L2,R2',
  code: [
    'class NumArray:',
    '    def __init__(self, nums):',
    '        self.prefix = [0] * (len(nums) + 1)',
    '        for i in range(len(nums)):',
    '            self.prefix[i + 1] = self.prefix[i] + nums[i]',
    '',
    '    def sumRange(self, left, right):',
    '        return self.prefix[right + 1] - self.prefix[left]'
  ],
  parse(str) {
    const p = str.split(';');
    let nums = avArr(p[0]);
    let queries = [];
    if (p[1]) {
        queries = p[1].split('|').map(s => {
            let parts = s.split(',').map(n => parseInt(n.trim(), 10));
            return {L: parts[0], R: parts[1]};
        });
    }
    return { nums, queries };
  },
  buildStates({ nums, queries }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    let prefix = [0];
    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      nums, phase: 'init', prefix: [...prefix], currQ: null,
      explTitle: 'Initialization',
      explText: `Initialize prefix sum array with a leading 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        prefix.push(prefix[i] + nums[i]);
    }
    
    domPushState(seq, {
      kind: 'prefix', line: 5, color: 'blue',
      nums, phase: 'prefix_done', prefix: [...prefix], currQ: null,
      explTitle: `Prefix Sum Computed`,
      explText: `Prefix sum array computed. prefix[i] stores sum of nums[0...i-1].`
    }, ctx);

    for (let q = 0; q < queries.length; q++) {
        let L = queries[q].L;
        let R = queries[q].R;
        if (L < 0) L = 0;
        if (R >= nums.length) R = nums.length - 1;
        if (L > R) { let temp = L; L = R; R = temp; }
        
        let ans = prefix[R + 1] - prefix[L];
        
        domPushState(seq, {
          kind: 'query', line: 8, color: 'emerald',
          nums, phase: 'query', prefix: [...prefix], currQ: {L, R, ans, rightVal: prefix[R+1], leftVal: prefix[L]},
          explTitle: `Query sumRange(${L}, ${R})`,
          explText: `Sum = prefix[${R + 1}] - prefix[${L}] = ${prefix[R+1]} - ${prefix[L]} = ${ans}.`
        }, ctx);
    }
    
    if (queries.length === 0) {
        domPushState(seq, {
          kind: 'done', line: 8, color: 'emerald',
          nums, phase: 'done', prefix: [...prefix], currQ: null,
          explTitle: `Done`,
          explText: `No queries provided.`
        }, ctx);
    }

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let inQuery = state.currQ && idx >= state.currQ.L && idx <= state.currQ.R;
      
      let bg = inQuery ? 'rgba(56, 189, 248, 0.2)' : 'var(--surface)';
      let border = inQuery ? '#38bdf8' : 'var(--border)';
      let color = inQuery ? '#38bdf8' : 'var(--text)';
      let boxsh = inQuery ? 'box-shadow: 0 0 10px #38bdf8;' : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px; color:${color};
            ${inQuery ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
        </div>
      `;
    }).join('');
    
    const prefixHTML = state.prefix.map((v, idx) => {
      let isLeft = state.currQ && idx === state.currQ.L;
      let isRight = state.currQ && idx === state.currQ.R + 1;
      
      let bg = 'rgba(255,255,255,0.05)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (isRight) {
          bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; color = '#34d399'; boxsh = 'box-shadow: 0 0 10px #34d399;';
      } else if (isLeft) {
          bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
      }

      let bottomHTML = '';
      if (isRight) bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">R+1</div>`;
      if (isLeft) bottomHTML = `<div style="position:absolute; bottom:-25px; color:#f43f5e; font-size:12px; font-weight:bold; white-space:nowrap;">L</div>`;

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px; color:${color}; font-family:monospace;
            ${(isLeft || isRight) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');

    let calcHTML = '';
    if (state.currQ) {
        calcHTML = `
            <div style="display:flex; align-items:center; gap:15px; font-size:24px; font-weight:bold; font-family:monospace; margin-top:20px; padding:15px; background:rgba(0,0,0,0.2); border-radius:12px; border:1px solid var(--border);">
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <span style="font-size:12px; color:var(--text-dim); font-family:sans-serif;">prefix[R+1]</span>
                    <span style="color:#34d399;">${state.currQ.rightVal}</span>
                </div>
                <span style="color:var(--text-dim);">-</span>
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <span style="font-size:12px; color:var(--text-dim); font-family:sans-serif;">prefix[L]</span>
                    <span style="color:#f43f5e;">${state.currQ.leftVal}</span>
                </div>
                <span style="color:var(--text-dim);">=</span>
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <span style="font-size:12px; color:var(--text-dim); font-family:sans-serif;">Sum</span>
                    <span style="color:#38bdf8; text-shadow:0 0 10px rgba(56,189,248,0.5);">${state.currQ.ans}</span>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Input Array (nums)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: #a855f7;">Prefix Sum Array</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${prefixHTML}
          </div>
          ${calcHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Find Pivot Index (DOM) ============== */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Find Pivot Index', short: 'Pivot Index',
  idea: 'Calculate the <code>total_sum</code> first. Then iterate, keeping track of <code>left_sum</code>. The right sum can be derived as <code>total_sum - left_sum - nums[i]</code>. Return the index if they are equal.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 7, 3, 6, 5, 6', hint: 'comma-separated array of numbers',
  code: [
    'def pivotIndex(nums):',
    '    total_sum = sum(nums)',
    '    left_sum = 0',
    '    for i in range(len(nums)):',
    '        right_sum = total_sum - left_sum - nums[i]',
    '        if left_sum == right_sum:',
    '            return i',
    '        left_sum += nums[i]',
    '    return -1'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let totalSum = nums.reduce((a,b)=>a+b, 0);
    let leftSum = 0;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, phase: 'init', i: -1, totalSum, leftSum, rightSum: '?', pivot: -1,
      explTitle: 'Initialization',
      explText: `Calculate total sum = ${totalSum}. Initialize left_sum = 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        let rightSum = totalSum - leftSum - nums[i];
        
        domPushState(seq, {
          kind: 'check', line: 5, color: 'blue',
          nums, phase: 'check', i, totalSum, leftSum, rightSum, pivot: -1,
          explTitle: `Check Index ${i}`,
          explText: `Right Sum = Total (${totalSum}) - Left (${leftSum}) - nums[${i}] (${nums[i]}) = ${rightSum}.`
        }, ctx);
        
        if (leftSum === rightSum) {
            domPushState(seq, {
              kind: 'found', line: 7, color: 'emerald',
              nums, phase: 'found', i, totalSum, leftSum, rightSum, pivot: i,
              explTitle: `Pivot Found!`,
              explText: `left_sum (${leftSum}) == right_sum (${rightSum}). Index ${i} is the pivot.`
            }, ctx);
            return seq; // Stop early
        }

        leftSum += nums[i];
        domPushState(seq, {
          kind: 'update', line: 8, color: 'amber',
          nums, phase: 'update', i, totalSum, leftSum, rightSum, pivot: -1,
          explTitle: `Update Left Sum`,
          explText: `Add nums[${i}] (${nums[i]}) to left_sum. left_sum is now ${leftSum}.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 9, color: 'red',
      nums, phase: 'done', i: -1, totalSum, leftSum, rightSum: '?', pivot: -1,
      explTitle: `Done`,
      explText: `No pivot index found. Return -1.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      let isLeft = idx < state.i;
      let isRight = idx > state.i;
      
      if (state.phase === 'update') {
          isLeft = idx <= state.i;
          isRight = idx > state.i;
      }
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text)';
      let boxsh = '';
      
      if (state.phase !== 'init' && state.phase !== 'done') {
          if (isCurrent && state.phase !== 'update') {
              border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;';
          } else if (isLeft) {
              bg = 'rgba(56, 189, 248, 0.2)'; border = '#38bdf8'; color = '#38bdf8';
          } else if (isRight) {
              bg = 'rgba(244, 63, 94, 0.2)'; border = '#f43f5e'; color = '#f43f5e';
          }
      }
      
      if (state.phase === 'found' && idx === state.pivot) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 20px #34d399;'; color = '#34d399';
      }

      let bottomHTML = '';
      if (isCurrent && state.phase !== 'done' && state.phase !== 'found') {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#a855f7; font-size:12px; font-weight:bold; white-space:nowrap;">Current</div>`;
      }
      if (state.phase === 'found' && idx === state.pivot) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">Pivot</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color};
            ${isCurrent || (state.phase === 'found' && idx === state.pivot) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Total Sum = <span style="color:white;">${state.totalSum}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 20px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; border:2px solid ${state.phase === 'found' ? '#34d399' : '#38bdf8'}; background:rgba(56, 189, 248, 0.05);">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Left Sum</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#38bdf8;">${state.leftSum}</div>
            </div>
            
            <div style="display:flex; align-items:center; font-size:24px; font-weight:bold; color:${state.phase === 'found' ? '#34d399' : 'var(--text-dim)'};">
                ${state.phase === 'found' ? '==' : (state.phase === 'check' ? '?' : '!=')}
            </div>
            
            <div class="glass-panel" style="padding: 20px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; border:2px solid ${state.phase === 'found' ? '#34d399' : '#f43f5e'}; background:rgba(244, 63, 94, 0.05);">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Right Sum</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#f43f5e;">${state.rightSum}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Subarray Sum Equals K (DOM) ========= */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Subarray Sum Equals K', short: 'Subarray Sum = K',
  idea: 'We track the running sum (prefix sum) and use a hash map to store frequencies of prefix sums we have seen. If <code>cur_sum - k</code> is in the map, it means there is a sub-array summing to <code>k</code>.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 1, 1 ; 2', hint: 'comma-separated array ; k',
  code: [
    'def subarraySum(nums, k):',
    '    res = 0',
    '    cur_sum = 0',
    '    prefix_counts = {0: 1}',
    '    for num in nums:',
    '        cur_sum += num',
    '        diff = cur_sum - k',
    '        res += prefix_counts.get(diff, 0)',
    '        prefix_counts[cur_sum] = prefix_counts.get(cur_sum, 0) + 1',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '0', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let res = 0;
    let curSum = 0;
    let prefixCounts = {0: 1};

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      nums, k, phase: 'init', i: -1, res, curSum, prefixCounts: {...prefixCounts}, diff: null, found: 0,
      explTitle: 'Initialization',
      explText: `Initialize map with {0: 1} to handle sub-arrays starting from index 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        curSum += nums[i];
        let diff = curSum - k;
        
        domPushState(seq, {
          kind: 'compute', line: 7, color: 'blue',
          nums, k, phase: 'compute', i, res, curSum, prefixCounts: {...prefixCounts}, diff, found: 0,
          explTitle: `Compute Prefix Sum`,
          explText: `Added ${nums[i]}. Current Sum = ${curSum}. Look for prefix sum ${curSum} - ${k} = ${diff} in map.`
        }, ctx);
        
        let found = prefixCounts[diff] || 0;
        if (found > 0) {
            res += found;
            domPushState(seq, {
              kind: 'found', line: 8, color: 'emerald',
              nums, k, phase: 'found', i, res, curSum, prefixCounts: {...prefixCounts}, diff, found,
              explTitle: `Found Matching Prefix`,
              explText: `Map contains ${diff} with count ${found}. Add ${found} to result.`
            }, ctx);
        }

        prefixCounts[curSum] = (prefixCounts[curSum] || 0) + 1;
        domPushState(seq, {
          kind: 'record', line: 9, color: 'amber',
          nums, k, phase: 'record', i, res, curSum, prefixCounts: {...prefixCounts}, diff, found,
          explTitle: `Update Map`,
          explText: `Add/update current sum ${curSum} in map.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      nums, k, phase: 'done', i: -1, res, curSum, prefixCounts: {...prefixCounts}, diff: null, found: 0,
      explTitle: `Done`,
      explText: `Total subarrays with sum ${k} is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i && state.phase !== 'done') {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (isCurrent) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (state.phase === 'found' && idx <= state.i) {
          if (isCurrent) {
              bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
          }
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:16px; font-weight:bold;">▲</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let countsArray = Object.entries(state.prefixCounts).sort((a,b) => parseInt(a) - parseInt(b));
    let countsHTML = countsArray.map(([sum, count]) => {
        let isTarget = state.phase === 'found' && parseInt(sum) === state.diff;
        let isNew = state.phase === 'record' && parseInt(sum) === state.curSum;
        
        let color = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--text)');
        let border = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--border)');
        let bg = isTarget ? 'rgba(52,211,153,0.2)' : (isNew ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)');
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; padding:5px 10px; min-width:50px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${color};">Sum ${sum}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">Count: <span style="color:${color}; font-weight:bold;">${count}</span></div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Target k = <span style="color:#a855f7;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Prefix Sums Map <br/>
                <span style="font-size:10px; color:#38bdf8; text-transform:none; font-weight:normal;">Looking for: CurrentSum(${state.curSum}) - k(${state.k}) = <b>${state.phase !== 'init' && state.phase !== 'done' ? state.diff : '?'}</b></span>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Total Valid Subarrays</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Contiguous Array (DOM) ============== */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Contiguous Array', short: 'Contiguous Array',
  idea: 'Replace 0s with -1s. The problem then becomes finding the longest subarray with a sum of 0. We track the running sum and store the first time we see each sum in a hash map.',
  complexity: 'Time O(N) · Space O(N)',
  input: '0, 1, 0, 0, 1, 1, 0', hint: 'comma-separated array of 0s and 1s',
  code: [
    'def findMaxLength(nums):',
    '    res = 0',
    '    cur_sum = 0',
    '    first_seen = {0: -1}',
    '    for i, num in enumerate(nums):',
    '        cur_sum += 1 if num == 1 else -1',
    '        if cur_sum in first_seen:',
    '            res = max(res, i - first_seen[cur_sum])',
    '        else:',
    '            first_seen[cur_sum] = i',
    '    return res'
  ],
  parse(str) {
    return { nums: avArr(str) };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let res = 0;
    let curSum = 0;
    let firstSeen = {0: -1};

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      nums, phase: 'init', i: -1, res, curSum, firstSeen: {...firstSeen}, len: 0,
      explTitle: 'Initialization',
      explText: `Initialize map with {0: -1} to handle sub-arrays starting from index 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        let valToAdd = nums[i] === 1 ? 1 : -1;
        curSum += valToAdd;
        
        domPushState(seq, {
          kind: 'compute', line: 6, color: 'blue',
          nums, phase: 'compute', i, res, curSum, valToAdd, firstSeen: {...firstSeen}, len: 0,
          explTitle: `Compute Prefix Sum`,
          explText: `nums[${i}] is ${nums[i]}, so add ${valToAdd} to running sum. Current Sum = ${curSum}.`
        }, ctx);
        
        if (firstSeen[curSum] !== undefined) {
            let prevIndex = firstSeen[curSum];
            let len = i - prevIndex;
            
            domPushState(seq, {
              kind: 'found', line: 8, color: 'emerald',
              nums, phase: 'found', i, res, curSum, valToAdd, firstSeen: {...firstSeen}, len, prevIndex,
              explTitle: `Found Matching Prefix`,
              explText: `Map contains ${curSum} at index ${prevIndex}. Subarray length = ${i} - ${prevIndex} = ${len}.`
            }, ctx);
            
            if (len > res) {
                res = len;
                domPushState(seq, {
                  kind: 'update_res', line: 8, color: 'emerald',
                  nums, phase: 'update_res', i, res, curSum, valToAdd, firstSeen: {...firstSeen}, len, prevIndex,
                  explTitle: `Update Max Length`,
                  explText: `New max length is ${res}.`
                }, ctx);
            }
        } else {
            firstSeen[curSum] = i;
            domPushState(seq, {
              kind: 'record', line: 10, color: 'amber',
              nums, phase: 'record', i, res, curSum, valToAdd, firstSeen: {...firstSeen}, len: 0,
              explTitle: `Update Map`,
              explText: `Add current sum ${curSum} to map at index ${i}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, phase: 'done', i: -1, res, curSum, firstSeen: {...firstSeen}, len: 0,
      explTitle: `Done`,
      explText: `Maximum contiguous subarray length with equal 0s and 1s is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i && state.phase !== 'done') {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (isCurrent) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if ((state.phase === 'found' || state.phase === 'update_res') && idx > state.prevIndex && idx <= state.i) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }
      
      let innerText = v;
      if (idx <= state.i && state.phase !== 'done') {
          innerText = v === 1 ? '1' : '-1';
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:16px; font-weight:bold;">▲</div>` : '';
      if ((state.phase === 'found' || state.phase === 'update_res') && idx === state.prevIndex) {
          bottomHTML = `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold; white-space:nowrap;">firstSeen</div>`;
          border = '#f43f5e'; bg = 'rgba(244,63,94,0.2)';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:16px; color:${color}; font-family:monospace;
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${innerText}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let seenArray = Object.entries(state.firstSeen).sort((a,b) => parseInt(a) - parseInt(b));
    let seenHTML = seenArray.map(([sum, index]) => {
        let isTarget = (state.phase === 'found' || state.phase === 'update_res') && parseInt(sum) === state.curSum;
        let isNew = state.phase === 'record' && parseInt(sum) === state.curSum;
        
        let color = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--text)');
        let border = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--border)');
        let bg = isTarget ? 'rgba(52,211,153,0.2)' : (isNew ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)');
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; padding:5px 10px; min-width:50px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${color};">Sum ${sum}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">Idx: <span style="color:${color}; font-weight:bold;">${index}</span></div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (0 mapped to -1)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                First Seen Sum Map <br/>
                <span style="font-size:10px; color:#38bdf8; text-transform:none; font-weight:normal;">Current Sum: <b>${state.phase !== 'init' && state.phase !== 'done' ? state.curSum : '?'}</b></span>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${seenHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Max Subarray Length</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Range Sum Query 2D - Immutable (DOM) */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Range Sum Query 2D - Immutable', short: 'Range Sum 2D',
  idea: 'Create a 2D prefix sum array where <code>prefix[r+1][c+1]</code> is the sum of all elements in the rectangle from <code>(0,0)</code> to <code>(r,c)</code>. Then a query <code>(r1,c1)</code> to <code>(r2,c2)</code> is computed using inclusion-exclusion.',
  complexity: 'Time O(R*C) init, O(1) query · Space O(R*C)',
  input: '3,0,1,4,2 ; 5,6,3,2,1 ; 1,2,0,1,5 ; 4,1,0,1,7 ; 1,0,3,0,5 | 2,1,4,3 | 1,1,2,2', hint: 'rows separated by ; | query: r1,c1,r2,c2',
  code: [
    'class NumMatrix:',
    '    def __init__(self, matrix):',
    '        ROWS, COLS = len(matrix), len(matrix[0])',
    '        self.prefix = [[0] * (COLS + 1) for _ in range(ROWS + 1)]',
    '        for r in range(ROWS):',
    '            for c in range(COLS):',
    '                self.prefix[r+1][c+1] = (self.prefix[r][c+1] + ',
    '                                         self.prefix[r+1][c] - ',
    '                                         self.prefix[r][c] + ',
    '                                         matrix[r][c])',
    '',
    '    def sumRegion(self, r1, c1, r2, c2):',
    '        return (self.prefix[r2+1][c2+1] - ',
    '                self.prefix[r1][c2+1] - ',
    '                self.prefix[r2+1][c1] + ',
    '                self.prefix[r1][c1])'
  ],
  parse(str) {
    let parts = str.split('|');
    let rowsStr = parts[0].split(';');
    let matrix = [];
    for (let rs of rowsStr) {
        if (rs.trim()) matrix.push(avArr(rs));
    }
    let queries = [];
    if (parts.length > 1) {
        for (let i = 1; i < parts.length; i++) {
            let qStr = parts[i].split(',').map(n => parseInt(n.trim(), 10));
            if (qStr.length === 4) queries.push(qStr);
        }
    }
    return { matrix, queries };
  },
  buildStates({ matrix, queries }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (matrix.length === 0 || matrix[0].length === 0) return seq;

    const R = matrix.length;
    const C = matrix[0].length;
    
    let prefix = Array(R + 1).fill().map(() => Array(C + 1).fill(0));

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      matrix, phase: 'init', prefix: JSON.parse(JSON.stringify(prefix)), r: -1, c: -1, currQ: null,
      explTitle: 'Initialization',
      explText: `Initialize a (R+1) x (C+1) prefix sum matrix with zeros.`
    }, ctx);

    // Compute Prefix Sums visually step by step, but we will skip some if matrix is large.
    for (let r = 0; r < R; r++) {
        for (let c = 0; c < C; c++) {
            let top = prefix[r][c+1];
            let left = prefix[r+1][c];
            let topleft = prefix[r][c];
            let val = matrix[r][c];
            
            prefix[r+1][c+1] = top + left - topleft + val;
            
            if ((r < 2 && c < 2) || (r === R-1 && c === C-1)) {
                domPushState(seq, {
                  kind: 'compute', line: 7, color: 'blue',
                  matrix, phase: 'compute', prefix: JSON.parse(JSON.stringify(prefix)), r, c, top, left, topleft, val, currQ: null,
                  explTitle: `Compute Prefix(${r+1}, ${c+1})`,
                  explText: `Prefix = Top(${top}) + Left(${left}) - TopLeft(${topleft}) + Matrix(${val}) = ${prefix[r+1][c+1]}`
                }, ctx);
            }
        }
    }
    
    domPushState(seq, {
      kind: 'prefix_done', line: 10, color: 'emerald',
      matrix, phase: 'prefix_done', prefix: JSON.parse(JSON.stringify(prefix)), r: -1, c: -1, currQ: null,
      explTitle: `Prefix Matrix Ready`,
      explText: `The 2D prefix sum matrix is fully computed.`
    }, ctx);

    for (let q of queries) {
        let r1 = q[0], c1 = q[1], r2 = q[2], c2 = q[3];
        if (r1 < 0) r1 = 0;
        if (c1 < 0) c1 = 0;
        if (r2 >= R) r2 = R - 1;
        if (c2 >= C) c2 = C - 1;
        
        let br = prefix[r2+1][c2+1];
        let top = prefix[r1][c2+1];
        let left = prefix[r2+1][c1];
        let topleft = prefix[r1][c1];
        
        let ans = br - top - left + topleft;
        
        domPushState(seq, {
          kind: 'query', line: 13, color: 'amber',
          matrix, phase: 'query', prefix: JSON.parse(JSON.stringify(prefix)), currQ: {r1, c1, r2, c2, br, top, left, topleft, ans},
          explTitle: `Query sumRegion(${r1}, ${c1}, ${r2}, ${c2})`,
          explText: `Sum = BotRight(${br}) - Top(${top}) - Left(${left}) + TopLeft(${topleft}) = ${ans}.`
        }, ctx);
    }
    
    if (queries.length === 0) {
        domPushState(seq, {
          kind: 'done', line: 13, color: 'emerald',
          matrix, phase: 'done', prefix: JSON.parse(JSON.stringify(prefix)), r: -1, c: -1, currQ: null,
          explTitle: `Done`,
          explText: `No queries provided.`
        }, ctx);
    }

    return seq;
  },
  renderDOM(container, state) {
    if (!state.matrix) return;
      
    const R = state.matrix.length;
    const C = state.matrix[0].length;
      
    let matrixHTML = '';
    for (let r = 0; r < R; r++) {
        let rowHTML = '';
        for (let c = 0; c < C; c++) {
            let isCurrent = state.phase === 'compute' && r === state.r && c === state.c;
            let inQuery = state.currQ && r >= state.currQ.r1 && r <= state.currQ.r2 && c >= state.currQ.c1 && c <= state.currQ.c2;
            
            let bg = inQuery ? 'rgba(56, 189, 248, 0.3)' : 'var(--surface)';
            let border = inQuery ? '#38bdf8' : 'var(--border)';
            let color = inQuery ? '#38bdf8' : 'var(--text)';
            let boxsh = inQuery ? 'box-shadow: 0 0 10px #38bdf8;' : '';

            if (isCurrent) {
                border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7'; bg = 'rgba(168,85,247,0.2)';
            }
            
            rowHTML += `
              <div style="
                width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
                background: ${bg}; border: 1px solid ${border}; font-weight: bold; font-size:14px; color:${color};
                ${(isCurrent || inQuery) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
                transition: all 0.3s;
              ">${state.matrix[r][c]}</div>
            `;
        }
        matrixHTML += `<div style="display:flex; gap:2px;">${rowHTML}</div>`;
    }
    
    let prefixHTML = '';
    for (let r = 0; r <= R; r++) {
        let rowHTML = '';
        for (let c = 0; c <= C; c++) {
            let isCurrent = state.phase === 'compute' && r === state.r + 1 && c === state.c + 1;
            let isTop = state.phase === 'compute' && r === state.r && c === state.c + 1;
            let isLeft = state.phase === 'compute' && r === state.r + 1 && c === state.c;
            let isTopLeft = state.phase === 'compute' && r === state.r && c === state.c;
            
            let isQBR = state.currQ && r === state.currQ.r2 + 1 && c === state.currQ.c2 + 1;
            let isQTop = state.currQ && r === state.currQ.r1 && c === state.currQ.c2 + 1;
            let isQLeft = state.currQ && r === state.currQ.r2 + 1 && c === state.currQ.c1;
            let isQTopLeft = state.currQ && r === state.currQ.r1 && c === state.currQ.c1;
            
            let bg = 'rgba(255,255,255,0.02)';
            let border = 'var(--border)';
            let color = 'var(--text-dim)';
            let boxsh = '';
            
            let valToShow = state.prefix[r][c];
            
            if (isCurrent) {
                bg = 'rgba(168,85,247,0.3)'; border = '#a855f7'; color = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;';
            } else if (isTop) {
                bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e';
            } else if (isLeft) {
                bg = 'rgba(56,189,248,0.3)'; border = '#38bdf8'; color = '#38bdf8';
            } else if (isTopLeft) {
                bg = 'rgba(250,204,21,0.3)'; border = '#facc15'; color = '#facc15';
            } else if (state.phase === 'compute' && (r > state.r + 1 || (r === state.r + 1 && c > state.c + 1))) {
                valToShow = ''; // Not computed yet
            } else if (state.phase !== 'init' && state.phase !== 'compute') {
                color = 'var(--text)';
            }
            
            if (isQBR) {
                bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; color = '#34d399'; boxsh = 'box-shadow: 0 0 10px #34d399;';
            } else if (isQTop) {
                bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
            } else if (isQLeft) {
                bg = 'rgba(56,189,248,0.3)'; border = '#38bdf8'; color = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
            } else if (isQTopLeft) {
                bg = 'rgba(250,204,21,0.3)'; border = '#facc15'; color = '#facc15'; boxsh = 'box-shadow: 0 0 10px #facc15;';
            }
            
            rowHTML += `
              <div style="
                width: 35px; height: 35px; display: flex; align-items: center; justify-content: center;
                background: ${bg}; border: 1px solid ${border}; font-weight: bold; font-size:12px; color:${color}; font-family:monospace;
                ${(isCurrent || isTop || isLeft || isTopLeft || isQBR || isQTop || isQLeft || isQTopLeft) ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
                transition: all 0.3s;
              ">${valToShow}</div>
            `;
        }
        prefixHTML += `<div style="display:flex; gap:2px;">${rowHTML}</div>`;
    }

    let calcHTML = '';
    if (state.phase === 'compute') {
        calcHTML = `
            <div style="display:flex; align-items:center; gap:10px; font-size:16px; font-weight:bold; font-family:monospace; margin-top:20px; padding:10px; background:rgba(0,0,0,0.2); border-radius:12px; border:1px solid var(--border);">
                <span style="color:#f43f5e;">Top(${state.top})</span> + 
                <span style="color:#38bdf8;">Left(${state.left})</span> - 
                <span style="color:#facc15;">TopLeft(${state.topleft})</span> + 
                <span style="color:#a855f7;">Mat(${state.val})</span> = 
                <span style="color:#34d399;">${state.prefix[state.r+1][state.c+1]}</span>
            </div>
        `;
    } else if (state.currQ) {
        calcHTML = `
            <div style="display:flex; align-items:center; gap:10px; font-size:18px; font-weight:bold; font-family:monospace; margin-top:20px; padding:10px; background:rgba(0,0,0,0.2); border-radius:12px; border:1px solid var(--border);">
                <span style="color:#34d399;">BR(${state.currQ.br})</span> - 
                <span style="color:#f43f5e;">Top(${state.currQ.top})</span> - 
                <span style="color:#38bdf8;">Left(${state.currQ.left})</span> + 
                <span style="color:#facc15;">TopLeft(${state.currQ.topleft})</span> = 
                <span style="color:#a855f7; text-shadow:0 0 10px rgba(168,85,247,0.5);">${state.currQ.ans}</span>
            </div>
        `;
    }

    container.innerHTML = `
      <div style="display:flex; gap:30px; justify-content:center; width:100%; max-width:900px; flex-wrap:wrap;">
        <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:300px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Original Matrix</div>
          <div style="display:flex; flex-direction:column; gap:2px; justify-content:center; padding:10px;">
            ${matrixHTML}
          </div>
        </div>
        
        <div class="glass-panel" style="padding: 20px; display: flex; flex-direction: column; align-items: center; min-width:350px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: #a855f7;">Prefix Matrix (R+1 x C+1)</div>
          <div style="display:flex; flex-direction:column; gap:2px; justify-content:center; padding:10px;">
            ${prefixHTML}
          </div>
          ${calcHTML}
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Subarray Sums Divisible by K (DOM) */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Subarray Sums Divisible by K', short: 'Divisible by K',
  idea: 'Use a hash map to store frequencies of <code>prefix_sum % K</code>. If we see a remainder again, it means the sub-array sum between these points is divisible by K. Handle negative remainders correctly.',
  complexity: 'Time O(N) · Space O(K)',
  input: '4, 5, 0, -2, -3, 1 ; 5', hint: 'comma-separated array ; K',
  code: [
    'def subarraysDivByK(nums, k):',
    '    res = 0',
    '    cur_sum = 0',
    '    rem_counts = {0: 1}',
    '    for num in nums:',
    '        cur_sum += num',
    '        rem = cur_sum % k',
    '        if rem < 0:',
    '            rem += k',
    '        res += rem_counts.get(rem, 0)',
    '        rem_counts[rem] = rem_counts.get(rem, 0) + 1',
    '    return res'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '5', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let res = 0;
    let curSum = 0;
    let remCounts = {0: 1};

    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      nums, k, phase: 'init', i: -1, res, curSum, remCounts: {...remCounts}, rem: null,
      explTitle: 'Initialization',
      explText: `Initialize map with {0: 1}.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        curSum += nums[i];
        let rem = curSum % k;
        if (rem < 0) rem += k;
        
        domPushState(seq, {
          kind: 'compute', line: 7, color: 'blue',
          nums, k, phase: 'compute', i, res, curSum, remCounts: {...remCounts}, rem,
          explTitle: `Compute Remainder`,
          explText: `Current Sum = ${curSum}. Remainder = ${curSum} % ${k} = ${rem}.`
        }, ctx);
        
        let found = remCounts[rem] || 0;
        if (found > 0) {
            res += found;
            domPushState(seq, {
              kind: 'found', line: 10, color: 'emerald',
              nums, k, phase: 'found', i, res, curSum, remCounts: {...remCounts}, rem, found,
              explTitle: `Found Matching Remainder`,
              explText: `Map contains remainder ${rem} with count ${found}. Add to result.`
            }, ctx);
        }

        remCounts[rem] = (remCounts[rem] || 0) + 1;
        domPushState(seq, {
          kind: 'record', line: 11, color: 'amber',
          nums, k, phase: 'record', i, res, curSum, remCounts: {...remCounts}, rem,
          explTitle: `Update Map`,
          explText: `Increment count for remainder ${rem}.`
        }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'emerald',
      nums, k, phase: 'done', i: -1, res, curSum, remCounts: {...remCounts}, rem: null,
      explTitle: `Done`,
      explText: `Total subarrays divisible by ${k} is ${res}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i && state.phase !== 'done') {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (isCurrent) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if (state.phase === 'found' && idx <= state.i) {
          if (isCurrent) {
              bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
          }
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:16px; font-weight:bold;">▲</div>` : '';

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let countsArray = Object.entries(state.remCounts).sort((a,b) => parseInt(a) - parseInt(b));
    let countsHTML = countsArray.map(([rem, count]) => {
        let isTarget = state.phase === 'found' && parseInt(rem) === state.rem;
        let isNew = state.phase === 'record' && parseInt(rem) === state.rem;
        
        let color = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--text)');
        let border = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--border)');
        let bg = isTarget ? 'rgba(52,211,153,0.2)' : (isNew ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)');
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; padding:5px 10px; min-width:50px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${color};">Rem ${rem}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">Count: <span style="color:${color}; font-weight:bold;">${count}</span></div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:700px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Divisor K = <span style="color:#a855f7;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:700px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Remainders Map <br/>
                <span style="font-size:10px; color:#38bdf8; text-transform:none; font-weight:normal;">Current Sum (${state.curSum}) % ${state.k} = <b>${state.phase !== 'init' && state.phase !== 'done' ? state.rem : '?'}</b></span>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${countsHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Total Valid Subarrays</div>
              <div style="font-size:36px; font-weight:bold; font-family:monospace; margin-top:5px; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3);">${state.res}</div>
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 04 · Continuous Subarray Sum (DOM) ======= */
defineAlgoDom('04_prefix_sum', {
  type: 'dom',
  title: 'Continuous Subarray Sum', short: 'Subarray Sum (mod k)',
  idea: 'Track running sum mod k. Store the first time we see each remainder. If we see a remainder again, and the distance is at least 2, we found a valid subarray.',
  complexity: 'Time O(N) · Space O(K)',
  input: '23, 2, 4, 6, 7 ; 6', hint: 'comma-separated array ; k',
  code: [
    'def checkSubarraySum(nums, k):',
    '    rem_map = {0: -1}',
    '    cur_sum = 0',
    '    for i, num in enumerate(nums):',
    '        cur_sum += num',
    '        rem = cur_sum % k',
    '        if rem in rem_map:',
    '            if i - rem_map[rem] > 1:',
    '                return True',
    '        else:',
    '            rem_map[rem] = i',
    '    return False'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), k: parseInt(p[1] || '6', 10) };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let curSum = 0;
    let remMap = {0: -1};

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, k, phase: 'init', i: -1, curSum, remMap: {...remMap}, rem: null,
      explTitle: 'Initialization',
      explText: `Initialize map with {0: -1} to handle sub-arrays starting from index 0.`
    }, ctx);

    for (let i = 0; i < nums.length; i++) {
        curSum += nums[i];
        let rem = curSum % k;
        
        domPushState(seq, {
          kind: 'compute', line: 6, color: 'blue',
          nums, k, phase: 'compute', i, curSum, remMap: {...remMap}, rem,
          explTitle: `Compute Remainder`,
          explText: `Current Sum = ${curSum}. Remainder = ${rem}.`
        }, ctx);
        
        if (remMap[rem] !== undefined) {
            let prevIndex = remMap[rem];
            let len = i - prevIndex;
            
            domPushState(seq, {
              kind: 'found', line: 7, color: 'emerald',
              nums, k, phase: 'found', i, curSum, remMap: {...remMap}, rem, len, prevIndex,
              explTitle: `Found Matching Remainder`,
              explText: `Map contains remainder ${rem} at index ${prevIndex}. Length = ${len}.`
            }, ctx);
            
            if (len > 1) {
                domPushState(seq, {
                  kind: 'done', line: 9, color: 'emerald',
                  nums, k, phase: 'done', i, curSum, remMap: {...remMap}, rem, len, prevIndex, res: true,
                  explTitle: `Valid Subarray Found`,
                  explText: `Length > 1. Return True!`
                }, ctx);
                return seq;
            } else {
                 domPushState(seq, {
                  kind: 'skip', line: 8, color: 'amber',
                  nums, k, phase: 'skip', i, curSum, remMap: {...remMap}, rem, len, prevIndex,
                  explTitle: `Length Too Short`,
                  explText: `Length is ${len}. We need at least 2. Skip update.`
                }, ctx);
            }
        } else {
            remMap[rem] = i;
            domPushState(seq, {
              kind: 'record', line: 11, color: 'amber',
              nums, k, phase: 'record', i, curSum, remMap: {...remMap}, rem,
              explTitle: `Update Map`,
              explText: `Record remainder ${rem} at index ${i}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'red',
      nums, k, phase: 'done', i: -1, curSum, remMap: {...remMap}, rem: null, res: false,
      explTitle: `Done`,
      explText: `No valid subarray found. Return False.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isCurrent = idx === state.i;
      
      let bg = 'var(--surface)';
      let border = 'var(--border)';
      let color = 'var(--text-dim)';
      let boxsh = '';
      
      if (idx <= state.i && state.phase !== 'done') {
        bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = 'var(--text)';
      }
      
      if (isCurrent) {
          border = '#a855f7'; boxsh = 'box-shadow: 0 0 10px #a855f7;'; color = '#a855f7';
      }
      
      if ((state.phase === 'found' || state.phase === 'done') && state.res === true && idx > state.prevIndex && idx <= state.i) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399';
      }

      let bottomHTML = isCurrent && state.phase !== 'done' ? `<div style="position:absolute; bottom:-20px; color:#a855f7; font-size:16px; font-weight:bold;">▲</div>` : '';
      if ((state.phase === 'found' || state.phase === 'skip' || (state.phase === 'done' && state.res === true)) && idx === state.prevIndex) {
          bottomHTML = `<div style="position:absolute; bottom:-20px; color:#f43f5e; font-size:12px; font-weight:bold; white-space:nowrap;">firstSeen</div>`;
          border = '#f43f5e'; bg = 'rgba(244,63,94,0.2)';
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isCurrent ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let seenArray = Object.entries(state.remMap).sort((a,b) => parseInt(a) - parseInt(b));
    let seenHTML = seenArray.map(([rem, index]) => {
        let isTarget = (state.phase === 'found' || state.phase === 'skip' || (state.phase === 'done' && state.res === true)) && parseInt(rem) === state.rem;
        let isNew = state.phase === 'record' && parseInt(rem) === state.rem;
        
        let color = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--text)');
        let border = isTarget ? '#34d399' : (isNew ? '#f59e0b' : 'var(--border)');
        let bg = isTarget ? 'rgba(52,211,153,0.2)' : (isNew ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)');
        
        return `
            <div style="display:flex; flex-direction:column; align-items:center; background:${bg}; border:1px solid ${border}; border-radius:6px; padding:5px 10px; min-width:50px;">
                <div style="font-family:monospace; font-weight:bold; font-size:16px; color:${color};">Rem ${rem}</div>
                <div style="font-size:12px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.1); margin-top:3px; padding-top:3px; width:100%; text-align:center;">Idx: <span style="color:${color}; font-weight:bold;">${index}</span></div>
            </div>
        `;
    }).join('');
    
    let resultHTML = '';
    if (state.phase === 'done') {
        if (state.res === true) {
            resultHTML = `<div style="font-size:32px; font-weight:bold; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.5);">TRUE</div>`;
        } else {
            resultHTML = `<div style="font-size:32px; font-weight:bold; color:#f43f5e; text-shadow: 0 0 10px rgba(244,63,94,0.5);">FALSE</div>`;
        }
    } else {
        resultHTML = `<div style="font-size:24px; color:var(--text-dim);">-</div>`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Array (Divisor K = <span style="color:#a855f7;">${state.k}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                First Seen Remainder Map <br/>
                <span style="font-size:10px; color:#38bdf8; text-transform:none; font-weight:normal;">Current Sum (${state.curSum}) % ${state.k} = <b>${state.phase !== 'init' ? state.rem : '?'}</b></span>
              </div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
                ${seenHTML}
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Result</div>
              ${resultHTML}
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 05 · Binary Search (DOM) ================= */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Binary Search', short: 'Binary Search',
  idea: 'Maintain two pointers <code>L</code> and <code>R</code>. Check the middle element. If it\'s the target, return. If it\'s smaller, search the right half <code>L = M + 1</code>. If larger, search the left half <code>R = M - 1</code>.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '-1, 0, 3, 5, 9, 12 ; 9', hint: 'sorted array ; target',
  code: [
    'def search(nums, target):',
    '    l, r = 0, len(nums) - 1',
    '    while l <= r:',
    '        m = l + ((r - l) // 2)',
    '        if nums[m] > target:',
    '            r = m - 1',
    '        elif nums[m] < target:',
    '            l = m + 1',
    '        else:',
    '            return m',
    '    return -1'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), target: parseInt(p[1] || '9', 10) };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let L = 0, R = nums.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, phase: 'init', L, R, M: -1, found: -1,
      explTitle: 'Initialization',
      explText: `Set L = ${L}, R = ${R}.`
    }, ctx);

    while (L <= R) {
        let M = L + Math.floor((R - L) / 2);
        
        domPushState(seq, {
          kind: 'compute_mid', line: 4, color: 'blue',
          nums, target, phase: 'mid', L, R, M, found: -1,
          explTitle: `Compute Mid`,
          explText: `Mid = ${L} + floor((${R} - ${L}) / 2) = ${M}. nums[${M}] is ${nums[M]}.`
        }, ctx);
        
        if (nums[M] === target) {
            domPushState(seq, {
              kind: 'found', line: 10, color: 'emerald',
              nums, target, phase: 'found', L, R, M, found: M,
              explTitle: `Target Found!`,
              explText: `nums[${M}] is ${target}. Return ${M}.`
            }, ctx);
            return seq;
        } else if (nums[M] > target) {
            R = M - 1;
            domPushState(seq, {
              kind: 'go_left', line: 6, color: 'amber',
              nums, target, phase: 'left', L, R, M, found: -1,
              explTitle: `Search Left`,
              explText: `${nums[M]} > ${target}, so target must be in the left half. R = ${M} - 1 = ${R}.`
            }, ctx);
        } else {
            L = M + 1;
            domPushState(seq, {
              kind: 'go_right', line: 8, color: 'amber',
              nums, target, phase: 'right', L, R, M, found: -1,
              explTitle: `Search Right`,
              explText: `${nums[M]} < ${target}, so target must be in the right half. L = ${M} + 1 = ${L}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'red',
      nums, target, phase: 'done', L, R, M: -1, found: -1,
      explTitle: `Done`,
      explText: `L > R. Target not found. Return -1.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isL = idx === state.L;
      let isR = idx === state.R;
      let isM = idx === state.M && state.phase !== 'init' && state.phase !== 'done';
      let isFound = state.phase === 'found' && idx === state.found;
      
      let outOfBounds = idx < state.L || idx > state.R;
      if (state.phase === 'left' && idx > state.R) outOfBounds = true;
      if (state.phase === 'right' && idx < state.L) outOfBounds = true;
      
      let bg = outOfBounds ? 'rgba(0,0,0,0.1)' : 'var(--surface)';
      let border = 'var(--border)';
      let color = outOfBounds ? 'var(--text-dim)' : 'var(--text)';
      let boxsh = '';
      let opacity = outOfBounds ? 0.3 : 1;
      
      if (!outOfBounds) {
          if (isM && !isFound) {
              bg = 'rgba(56, 189, 248, 0.2)'; border = '#38bdf8'; color = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
          }
          if (isL || isR) {
              border = '#a855f7';
          }
      }
      
      if (isFound) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399'; opacity = 1;
      }

      let bottomHTML = '';
      let ptrs = [];
      if (isL && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">L</span>`);
      if (isM && state.phase !== 'done') ptrs.push(`<span style="color:#38bdf8;">M</span>`);
      if (isR && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">R</span>`);
      
      if (ptrs.length > 0) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; font-size:14px; font-weight:bold; white-space:nowrap; display:flex; gap:3px;">
              ${ptrs.length === 3 ? `<span style="color:#a855f7;">L</span><span style="color:var(--text-dim);">/</span><span style="color:#38bdf8;">M</span><span style="color:var(--text-dim);">/</span><span style="color:#a855f7;">R</span>` : ptrs.join('<span style="color:var(--text-dim);">/</span>')}
          </div>`;
      }
      
      if (isFound) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">Target!</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative; opacity:${opacity}; transition: opacity 0.5s;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isM || isFound ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let resultHTML = '';
    if (state.phase === 'found') {
        resultHTML = `<div style="font-size:32px; font-weight:bold; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.5);">Index ${state.found}</div>`;
    } else if (state.phase === 'done') {
        resultHTML = `<div style="font-size:32px; font-weight:bold; color:#f43f5e; text-shadow: 0 0 10px rgba(244,63,94,0.5);">-1</div>`;
    } else {
        resultHTML = `<div style="font-size:24px; color:var(--text-dim);">Searching...</div>`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted Array (Target = <span style="color:#38bdf8;">${state.target}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Pointers
              </div>
              <div style="display:flex; gap:20px; font-family:monospace; font-size:20px; font-weight:bold;">
                <div style="color:#a855f7;">L = ${state.L}</div>
                <div style="color:#38bdf8;">M = ${state.phase !== 'init' && state.phase !== 'done' ? state.M : '?'}</div>
                <div style="color:#a855f7;">R = ${state.R}</div>
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Result</div>
              ${resultHTML}
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 05 · Search Insert Position (DOM) ======== */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Search Insert Position', short: 'Search Insert',
  idea: 'Use binary search. If target is found, return index. If not, the correct insertion position will naturally be at pointer <code>L</code> when the loop terminates (because <code>L</code> represents the first element greater than target).',
  complexity: 'Time O(log N) · Space O(1)',
  input: '1, 3, 5, 6 ; 2', hint: 'sorted array ; target',
  code: [
    'def searchInsert(nums, target):',
    '    l, r = 0, len(nums) - 1',
    '    while l <= r:',
    '        m = l + ((r - l) // 2)',
    '        if nums[m] > target:',
    '            r = m - 1',
    '        elif nums[m] < target:',
    '            l = m + 1',
    '        else:',
    '            return m',
    '    return l'
  ],
  parse(str) {
    const p = str.split(';');
    return { nums: avArr(p[0]), target: parseInt(p[1] || '2', 10) };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (nums.length === 0) return seq;

    let L = 0, R = nums.length - 1;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, target, phase: 'init', L, R, M: -1, found: -1,
      explTitle: 'Initialization',
      explText: `Set L = ${L}, R = ${R}.`
    }, ctx);

    while (L <= R) {
        let M = L + Math.floor((R - L) / 2);
        
        domPushState(seq, {
          kind: 'compute_mid', line: 4, color: 'blue',
          nums, target, phase: 'mid', L, R, M, found: -1,
          explTitle: `Compute Mid`,
          explText: `Mid = ${L} + floor((${R} - ${L}) / 2) = ${M}. nums[${M}] is ${nums[M]}.`
        }, ctx);
        
        if (nums[M] === target) {
            domPushState(seq, {
              kind: 'found', line: 10, color: 'emerald',
              nums, target, phase: 'found', L, R, M, found: M,
              explTitle: `Target Found!`,
              explText: `nums[${M}] is ${target}. Return ${M}.`
            }, ctx);
            return seq;
        } else if (nums[M] > target) {
            R = M - 1;
            domPushState(seq, {
              kind: 'go_left', line: 6, color: 'amber',
              nums, target, phase: 'left', L, R, M, found: -1,
              explTitle: `Search Left`,
              explText: `${nums[M]} > ${target}, so search left half. R = ${M} - 1 = ${R}.`
            }, ctx);
        } else {
            L = M + 1;
            domPushState(seq, {
              kind: 'go_right', line: 8, color: 'amber',
              nums, target, phase: 'right', L, R, M, found: -1,
              explTitle: `Search Right`,
              explText: `${nums[M]} < ${target}, so search right half. L = ${M} + 1 = ${L}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 11, color: 'emerald',
      nums, target, phase: 'done', L, R, M: -1, found: L,
      explTitle: `Done`,
      explText: `L > R. Target not found. Correct insertion point is L = ${L}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    // Create spaces for potential insertion points (before each element and after the last)
    const renderElements = [];
    
    for (let i = 0; i <= state.nums.length; i++) {
        let isInsertPos = state.phase === 'done' && state.L === i;
        
        // Render insertion slot
        if (isInsertPos) {
             renderElements.push(`
                <div style="display:flex; flex-direction:column; align-items:center; position:relative; width:45px; height:60px;">
                  <div style="font-size:10px; color:#34d399; margin-bottom:4px; font-weight:bold;">insert</div>
                  <div style="
                    width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
                    background: rgba(52,211,153,0.2); border: 2px dashed #34d399; border-radius: 6px; font-weight: bold; font-size:18px; color:#34d399; font-family:monospace;
                    transform: scale(1.1); z-index:2; box-shadow: 0 0 15px #34d399;
                    animation: pulse 2s infinite;
                  ">${state.target}</div>
                  <div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">L = ${state.L}</div>
                </div>
             `);
        } else if (state.phase === 'done' && i === state.nums.length) {
            // invisible spacer for the end if not inserting there
            renderElements.push(`<div style="width:10px;"></div>`);
        }
        
        // Render actual array element
        if (i < state.nums.length) {
            let idx = i;
            let v = state.nums[i];
            
            let isL = idx === state.L;
            let isR = idx === state.R;
            let isM = idx === state.M && state.phase !== 'init' && state.phase !== 'done';
            let isFound = state.phase === 'found' && idx === state.found;
            
            let outOfBounds = idx < state.L || idx > state.R;
            if (state.phase === 'left' && idx > state.R) outOfBounds = true;
            if (state.phase === 'right' && idx < state.L) outOfBounds = true;
            if (state.phase === 'done') outOfBounds = true;
            
            let bg = outOfBounds ? 'rgba(0,0,0,0.1)' : 'var(--surface)';
            let border = 'var(--border)';
            let color = outOfBounds ? 'var(--text-dim)' : 'var(--text)';
            let boxsh = '';
            let opacity = outOfBounds ? 0.3 : 1;
            
            if (!outOfBounds) {
                if (isM && !isFound) {
                    bg = 'rgba(56, 189, 248, 0.2)'; border = '#38bdf8'; color = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
                }
                if (isL || isR) {
                    border = '#a855f7';
                }
            }
            
            if (isFound) {
                bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399'; opacity = 1;
            }

            let bottomHTML = '';
            let ptrs = [];
            if (isL && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">L</span>`);
            if (isM && state.phase !== 'done') ptrs.push(`<span style="color:#38bdf8;">M</span>`);
            if (isR && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">R</span>`);
            
            if (ptrs.length > 0) {
                bottomHTML = `<div style="position:absolute; bottom:-25px; font-size:14px; font-weight:bold; white-space:nowrap; display:flex; gap:3px;">
                    ${ptrs.length === 3 ? `<span style="color:#a855f7;">L</span><span style="color:var(--text-dim);">/</span><span style="color:#38bdf8;">M</span><span style="color:var(--text-dim);">/</span><span style="color:#a855f7;">R</span>` : ptrs.join('<span style="color:var(--text-dim);">/</span>')}
                </div>`;
            }
            
            if (isFound) {
                bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">Target!</div>`;
            }

            renderElements.push(`
                <div style="display:flex; flex-direction:column; align-items:center; position:relative; opacity:${opacity}; transition: opacity 0.5s;">
                  <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">${idx}</div>
                  <div style="
                    width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
                    background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
                    ${isM || isFound ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
                    transition: all 0.3s;
                  ">${v}</div>
                  ${bottomHTML}
                </div>
            `);
        }
    }
    
    let resultHTML = '';
    if (state.phase === 'found') {
        resultHTML = `<div style="font-size:32px; font-weight:bold; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.5);">Index ${state.found}</div>`;
    } else if (state.phase === 'done') {
        resultHTML = `<div style="font-size:32px; font-weight:bold; color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.5);">Index ${state.found}</div>`;
    } else {
        resultHTML = `<div style="font-size:24px; color:var(--text-dim);">Searching...</div>`;
    }

    container.innerHTML = `
      <style>
        @keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; transform: scale(1.15); box-shadow: 0 0 20px #34d399; } 100% { opacity: 0.8; } }
      </style>
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Sorted Array (Target = <span style="color:#38bdf8;">${state.target}</span>)</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; min-height:80px; align-items:flex-end;">
            ${renderElements.join('')}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:2; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Pointers
              </div>
              <div style="display:flex; gap:20px; font-family:monospace; font-size:20px; font-weight:bold;">
                <div style="color:#a855f7;">L = ${state.L}</div>
                <div style="color:#38bdf8;">M = ${state.phase !== 'init' && state.phase !== 'done' ? state.M : '?'}</div>
                <div style="color:#a855f7;">R = ${state.R}</div>
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">Result</div>
              ${resultHTML}
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 05 · First Bad Version (DOM) ============= */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'First Bad Version', short: 'First Bad Version',
  idea: 'We are searching for the FIRST <code>true</code> in an array of <code>[false, false, ..., true, true]</code>. When <code>isBadVersion(M)</code> is true, the first bad version is either M or to the left, so <code>R = M</code>. If false, it\'s strictly to the right, so <code>L = M + 1</code>.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '5 ; 4', hint: 'total versions (n) ; first bad version (hidden)',
  code: [
    'def firstBadVersion(n):',
    '    l, r = 1, n',
    '    while l < r:',
    '        m = l + ((r - l) // 2)',
    '        if isBadVersion(m):',
    '            r = m',
    '        else:',
    '            l = m + 1',
    '    return l'
  ],
  parse(str) {
    const p = str.split(';');
    return { n: parseInt(p[0] || '5', 10), bad: parseInt(p[1] || '4', 10) };
  },
  buildStates({ n, bad }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (n <= 0) return seq;
    
    // Create versions array just for visualization [1, 2, 3, 4, 5]
    let nums = [];
    for(let i=1; i<=n; i++) nums.push(i);

    let L = 1, R = n;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, bad, phase: 'init', L, R, M: -1,
      explTitle: 'Initialization',
      explText: `Versions 1 to ${n}. Set L = ${L}, R = ${R}. (Bad = ${bad} but hidden)`
    }, ctx);

    while (L < R) {
        let M = L + Math.floor((R - L) / 2);
        let isBad = M >= bad;
        
        domPushState(seq, {
          kind: 'compute_mid', line: 4, color: 'blue',
          nums, bad, phase: 'mid', L, R, M, isBad: null,
          explTitle: `Check Version ${M}`,
          explText: `Mid = ${L} + floor((${R} - ${L}) / 2) = ${M}. Calling API isBadVersion(${M})...`
        }, ctx);
        
        domPushState(seq, {
          kind: 'api_result', line: 5, color: isBad ? 'red' : 'emerald',
          nums, bad, phase: 'api', L, R, M, isBad,
          explTitle: `API Result`,
          explText: `isBadVersion(${M}) returned ${isBad ? 'TRUE' : 'FALSE'}.`
        }, ctx);
        
        if (isBad) {
            R = M;
            domPushState(seq, {
              kind: 'go_left', line: 6, color: 'amber',
              nums, bad, phase: 'left', L, R, M, isBad,
              explTitle: `Search Left (including M)`,
              explText: `Version ${M} is bad. The first bad version could be ${M} or earlier. R = ${M}.`
            }, ctx);
        } else {
            L = M + 1;
            domPushState(seq, {
              kind: 'go_right', line: 8, color: 'amber',
              nums, bad, phase: 'right', L, R, M, isBad,
              explTitle: `Search Right`,
              explText: `Version ${M} is good. The first bad version MUST be after ${M}. L = ${M} + 1 = ${L}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 9, color: 'emerald',
      nums, bad, phase: 'done', L, R, M: -1,
      explTitle: `Done`,
      explText: `L == R (${L}). The first bad version is ${L}.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isL = v === state.L;
      let isR = v === state.R;
      let isM = v === state.M && state.phase !== 'init' && state.phase !== 'done';
      let isFound = state.phase === 'done' && v === state.L;
      
      let outOfBounds = v < state.L || v > state.R;
      
      let bg = outOfBounds ? 'rgba(0,0,0,0.1)' : 'var(--surface)';
      let border = 'var(--border)';
      let color = outOfBounds ? 'var(--text-dim)' : 'var(--text)';
      let boxsh = '';
      let opacity = outOfBounds ? 0.3 : 1;
      
      if (!outOfBounds) {
          if (isM && !isFound) {
              if (state.phase === 'api' || state.phase === 'left' || state.phase === 'right') {
                   if (state.isBad) {
                       bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;';
                   } else {
                       bg = 'rgba(52,211,153,0.2)'; border = '#34d399'; color = '#34d399'; boxsh = 'box-shadow: 0 0 10px #34d399;';
                   }
              } else {
                  bg = 'rgba(56, 189, 248, 0.2)'; border = '#38bdf8'; color = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
              }
          }
          if (isL || isR) {
              if(!isM || state.phase === 'api' || state.phase === 'left' || state.phase === 'right') {
                border = '#a855f7';
              }
          }
      }
      
      if (isFound) {
          bg = 'rgba(244,63,94,0.3)'; border = '#f43f5e'; boxsh = 'box-shadow: 0 0 15px #f43f5e;'; color = '#f43f5e'; opacity = 1;
      }

      let bottomHTML = '';
      let ptrs = [];
      if (isL && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">L</span>`);
      if (isM && state.phase !== 'done') ptrs.push(`<span style="color:#38bdf8;">M</span>`);
      if (isR && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">R</span>`);
      
      if (ptrs.length > 0) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; font-size:14px; font-weight:bold; white-space:nowrap; display:flex; gap:3px;">
              ${ptrs.length === 3 ? `<span style="color:#a855f7;">L</span><span style="color:var(--text-dim);">/</span><span style="color:#38bdf8;">M</span><span style="color:var(--text-dim);">/</span><span style="color:#a855f7;">R</span>` : ptrs.join('<span style="color:var(--text-dim);">/</span>')}
          </div>`;
      }
      
      if (isFound) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#f43f5e; font-size:12px; font-weight:bold; white-space:nowrap;">1st Bad</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative; opacity:${opacity}; transition: opacity 0.5s;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:4px;">v${v}</div>
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isM || isFound ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let apiHTML = '';
    if (state.phase === 'api' || state.phase === 'left' || state.phase === 'right') {
        if (state.isBad) {
            apiHTML = `<div style="color:#f43f5e; font-weight:bold; font-size:16px;">isBadVersion(${state.M}) == TRUE</div>`;
        } else {
            apiHTML = `<div style="color:#34d399; font-weight:bold; font-size:16px;">isBadVersion(${state.M}) == FALSE</div>`;
        }
    } else if (state.phase === 'mid') {
        apiHTML = `<div style="color:#38bdf8; font-weight:bold; font-size:16px; font-style:italic;">Calling API for v${state.M}...</div>`;
    } else {
        apiHTML = `<div style="color:var(--text-dim); font-size:16px;">-</div>`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px; overflow-x:auto;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Versions</div>
          <div style="display:flex; gap:10px; justify-content:center; min-width:max-content; padding:0 20px;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Pointers
              </div>
              <div style="display:flex; gap:20px; font-family:monospace; font-size:20px; font-weight:bold;">
                <div style="color:#a855f7;">L = ${state.L}</div>
                <div style="color:#38bdf8;">M = ${state.phase !== 'init' && state.phase !== 'done' ? state.M : '?'}</div>
                <div style="color:#a855f7;">R = ${state.R}</div>
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; border:1px solid ${state.isBad === true ? '#f43f5e' : (state.isBad === false ? '#34d399' : 'var(--border)')};">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">API Result</div>
              ${apiHTML}
            </div>
        </div>
      </div>
    `;
  }
});

/* ================================ 05 · Guess Number Higher or Lower (DOM) = */
defineAlgoDom('05_binary_search', {
  type: 'dom',
  title: 'Guess Number Higher or Lower', short: 'Guess Number',
  idea: 'We use the <code>guess(num)</code> API. If it returns 0, we found it. If -1, the picked number is lower (search left). If 1, the picked number is higher (search right). Standard binary search.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '10 ; 6', hint: 'total max (n) ; picked number (hidden)',
  code: [
    'def guessNumber(n):',
    '    l, r = 1, n',
    '    while l <= r:',
    '        m = l + ((r - l) // 2)',
    '        res = guess(m)',
    '        if res == 0:',
    '            return m',
    '        elif res < 0:',
    '            r = m - 1',
    '        else:',
    '            l = m + 1',
    '    return -1'
  ],
  parse(str) {
    const p = str.split(';');
    return { n: parseInt(p[0] || '10', 10), picked: parseInt(p[1] || '6', 10) };
  },
  buildStates({ n, picked }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    if (n <= 0) return seq;
    
    let nums = [];
    for(let i=1; i<=n; i++) nums.push(i);

    let L = 1, R = n;

    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nums, picked, phase: 'init', L, R, M: -1,
      explTitle: 'Initialization',
      explText: `Numbers 1 to ${n}. Set L = ${L}, R = ${R}. (Picked = ${picked} but hidden)`
    }, ctx);

    while (L <= R) {
        let M = L + Math.floor((R - L) / 2);
        
        let res = 0;
        if (M > picked) res = -1;
        else if (M < picked) res = 1;
        
        domPushState(seq, {
          kind: 'compute_mid', line: 4, color: 'blue',
          nums, picked, phase: 'mid', L, R, M, res: null,
          explTitle: `Guess Number ${M}`,
          explText: `Mid = ${L} + floor((${R} - ${L}) / 2) = ${M}. Calling API guess(${M})...`
        }, ctx);
        
        domPushState(seq, {
          kind: 'api_result', line: 5, color: res === 0 ? 'emerald' : 'amber',
          nums, picked, phase: 'api', L, R, M, res,
          explTitle: `API Result`,
          explText: `guess(${M}) returned ${res}.`
        }, ctx);
        
        if (res === 0) {
            domPushState(seq, {
              kind: 'found', line: 7, color: 'emerald',
              nums, picked, phase: 'found', L, R, M, res,
              explTitle: `Target Found!`,
              explText: `guess returned 0. The picked number is ${M}.`
            }, ctx);
            return seq;
        } else if (res < 0) {
            R = M - 1;
            domPushState(seq, {
              kind: 'go_left', line: 9, color: 'amber',
              nums, picked, phase: 'left', L, R, M, res,
              explTitle: `Search Left`,
              explText: `guess returned -1 (picked number is lower). R = ${M} - 1 = ${R}.`
            }, ctx);
        } else {
            L = M + 1;
            domPushState(seq, {
              kind: 'go_right', line: 11, color: 'amber',
              nums, picked, phase: 'right', L, R, M, res,
              explTitle: `Search Right`,
              explText: `guess returned 1 (picked number is higher). L = ${M} + 1 = ${L}.`
            }, ctx);
        }
    }

    domPushState(seq, {
      kind: 'done', line: 12, color: 'red',
      nums, picked, phase: 'done', L, R, M: -1,
      explTitle: `Done`,
      explText: `Not found.`
    }, ctx);

    return seq;
  },
  renderDOM(container, state) {
    if (!state.nums) return;
      
    const numsHTML = state.nums.map((v, idx) => {
      let isL = v === state.L;
      let isR = v === state.R;
      let isM = v === state.M && state.phase !== 'init' && state.phase !== 'done';
      let isFound = state.phase === 'found' && v === state.M;
      
      let outOfBounds = v < state.L || v > state.R;
      
      let bg = outOfBounds ? 'rgba(0,0,0,0.1)' : 'var(--surface)';
      let border = 'var(--border)';
      let color = outOfBounds ? 'var(--text-dim)' : 'var(--text)';
      let boxsh = '';
      let opacity = outOfBounds ? 0.3 : 1;
      
      if (!outOfBounds) {
          if (isM && !isFound) {
              if (state.phase === 'api' || state.phase === 'left' || state.phase === 'right') {
                   if (state.res < 0) {
                       bg = 'rgba(244,63,94,0.2)'; border = '#f43f5e'; color = '#f43f5e'; boxsh = 'box-shadow: 0 0 10px #f43f5e;'; // red for lower
                   } else if (state.res > 0) {
                       bg = 'rgba(245,158,11,0.2)'; border = '#f59e0b'; color = '#f59e0b'; boxsh = 'box-shadow: 0 0 10px #f59e0b;'; // orange for higher
                   }
              } else {
                  bg = 'rgba(56, 189, 248, 0.2)'; border = '#38bdf8'; color = '#38bdf8'; boxsh = 'box-shadow: 0 0 10px #38bdf8;';
              }
          }
          if (isL || isR) {
              if(!isM || state.phase === 'api' || state.phase === 'left' || state.phase === 'right') {
                border = '#a855f7';
              }
          }
      }
      
      if (isFound) {
          bg = 'rgba(52,211,153,0.3)'; border = '#34d399'; boxsh = 'box-shadow: 0 0 15px #34d399;'; color = '#34d399'; opacity = 1;
      }

      let bottomHTML = '';
      let ptrs = [];
      if (isL && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">L</span>`);
      if (isM && state.phase !== 'done') ptrs.push(`<span style="color:#38bdf8;">M</span>`);
      if (isR && state.phase !== 'done') ptrs.push(`<span style="color:#a855f7;">R</span>`);
      
      if (ptrs.length > 0) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; font-size:14px; font-weight:bold; white-space:nowrap; display:flex; gap:3px;">
              ${ptrs.length === 3 ? `<span style="color:#a855f7;">L</span><span style="color:var(--text-dim);">/</span><span style="color:#38bdf8;">M</span><span style="color:var(--text-dim);">/</span><span style="color:#a855f7;">R</span>` : ptrs.join('<span style="color:var(--text-dim);">/</span>')}
          </div>`;
      }
      
      if (isFound) {
          bottomHTML = `<div style="position:absolute; bottom:-25px; color:#34d399; font-size:12px; font-weight:bold; white-space:nowrap;">Target!</div>`;
      }

      return `
        <div style="display:flex; flex-direction:column; align-items:center; position:relative; opacity:${opacity}; transition: opacity 0.5s;">
          <div style="
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            background: ${bg}; border: 2px solid ${border}; border-radius: 6px; font-weight: bold; font-size:18px; color:${color}; font-family:monospace;
            ${isM || isFound ? `transform: scale(1.1); z-index:2; ${boxsh}` : ''}
            transition: all 0.3s;
          ">${v}</div>
          ${bottomHTML}
        </div>
      `;
    }).join('');
    
    let apiHTML = '';
    let apiColor = 'var(--text-dim)';
    if (state.phase === 'api' || state.phase === 'left' || state.phase === 'right' || state.phase === 'found') {
        if (state.res === 0) {
            apiHTML = `guess(${state.M}) == 0<br/><span style="font-size:12px; font-weight:normal;">(Correct!)</span>`;
            apiColor = '#34d399';
        } else if (state.res < 0) {
            apiHTML = `guess(${state.M}) == -1<br/><span style="font-size:12px; font-weight:normal;">(Target is lower)</span>`;
            apiColor = '#f43f5e';
        } else {
            apiHTML = `guess(${state.M}) == 1<br/><span style="font-size:12px; font-weight:normal;">(Target is higher)</span>`;
            apiColor = '#f59e0b';
        }
    } else if (state.phase === 'mid') {
        apiHTML = `guess(${state.M}) == ?<br/><span style="font-size:12px; font-weight:normal;">Calling API...</span>`;
        apiColor = '#38bdf8';
    } else {
        apiHTML = `-`;
    }

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:20px; align-items:center; width:100%;">
        <div class="glass-panel" style="padding: 20px 20px 40px 20px; width: 100%; display: flex; flex-direction: column; align-items: center; max-width:800px; overflow-x:auto;">
          <div class="panel-heading" style="margin-bottom: 25px; color: var(--accent);">Numbers 1 to n</div>
          <div style="display:flex; gap:10px; justify-content:center; min-width:max-content; padding:0 20px;">
            ${numsHTML}
          </div>
        </div>
        
        <div style="display:flex; gap:20px; width:100%; max-width:800px;">
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center;">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold; margin-bottom:10px; text-align:center;">
                Pointers
              </div>
              <div style="display:flex; gap:20px; font-family:monospace; font-size:20px; font-weight:bold;">
                <div style="color:#a855f7;">L = ${state.L}</div>
                <div style="color:#38bdf8;">M = ${state.phase !== 'init' && state.phase !== 'done' ? state.M : '?'}</div>
                <div style="color:#a855f7;">R = ${state.R}</div>
              </div>
            </div>
            
            <div class="glass-panel" style="padding: 15px; flex:1; display: flex; flex-direction: column; align-items: center; justify-content:center; border:1px solid ${apiColor !== 'var(--text-dim)' && apiColor !== '#38bdf8' ? apiColor : 'var(--border)'};">
              <div style="color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:1px; font-weight:bold;">API Result</div>
              <div style="color:${apiColor}; font-weight:bold; font-size:16px; text-align:center; margin-top:5px;">
                ${apiHTML}
              </div>
            </div>
        </div>
      </div>
    `;
  }
});

defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Baseball Game", short: "Baseball",
  idea: "Use a stack to keep track of scores. Numbers are added, '+' adds the sum of top two, 'D' doubles the top, and 'C' removes the top.",
  complexity: "Time O(n) \u00b7 Space O(n)",
  input: "5, 2, C, D, +", hint: "comma-separated operations",
  code: ["def calPoints(operations):", "    stack = []", "    for op in operations:", "        if op == '+':", "            stack.append(stack[-1] + stack[-2])", "        elif op == 'D':", "            stack.append(stack[-1] * 2)", "        elif op == 'C':", "            stack.pop()", "        else:", "            stack.append(int(op))", "    return sum(stack)"],
  parse(s) {
    return { ops: s.split(',').map(x => x.trim()).filter(x => x) };
  },
  buildStates({ops}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, ops, i: -1, stack: [...stack], explTitle: 'Start', explText: 'Empty stack.' }, ctx);
    for (let i = 0; i < ops.length; i++) {
        const op = ops[i];
        domPushState(seq, { kind: 'scan', line: 3, ops, i, stack: [...stack], explTitle: 'Process ' + op, explText: `Read operation: ${op}` }, ctx);
        if (op === '+') {
            const a = stack[stack.length - 1], b = stack[stack.length - 2];
            stack.push(a + b);
            domPushState(seq, { kind: 'add', line: 5, ops, i, stack: [...stack], explTitle: 'Sum top two', explText: `Add ${a} and ${b} to get ${a+b}. Push ${a+b}.` }, ctx);
        } else if (op === 'D') {
            const a = stack[stack.length - 1];
            stack.push(a * 2);
            domPushState(seq, { kind: 'double', line: 7, ops, i, stack: [...stack], explTitle: 'Double top', explText: `Double ${a} to get ${a*2}. Push ${a*2}.` }, ctx);
        } else if (op === 'C') {
            const popped = stack.pop();
            domPushState(seq, { kind: 'cancel', line: 9, ops, i, stack: [...stack], explTitle: 'Cancel', explText: `Remove top score ${popped}.` }, ctx);
        } else {
            stack.push(parseInt(op, 10));
            domPushState(seq, { kind: 'number', line: 11, ops, i, stack: [...stack], explTitle: 'Number', explText: `Push ${op} to stack.` }, ctx);
        }
    }
    const total = stack.reduce((a, b) => a + b, 0);
    domPushState(seq, { kind: 'done', line: 12, ops, i: ops.length, stack: [...stack], explTitle: 'Done', explText: `Total score is ${total}.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const opsHTML = s.ops.map((op, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${op}</span><div class="node-index">${idx}</div></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((v, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Operations</div>
          <div class="array-track">${opsHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Next Greater Element I", short: "Next Greater",
  idea: "Use a decreasing monotonic stack on nums2 to find the next greater element for each number. Store the results in a hash map for O(1) lookups when processing nums1.",
  complexity: "Time O(N + M) \u00b7 Space O(N)",
  input: "4, 1, 2 ; 1, 3, 4, 2", hint: "nums1 ; nums2",
  code: ["def nextGreaterElement(nums1, nums2):", "    stack = []", "    mapping = {}", "    for num in nums2:", "        while stack and num > stack[-1]:", "            mapping[stack.pop()] = num", "        stack.append(num)", "    for num in stack:", "        mapping[num] = -1", "    return [mapping[num] for num in nums1]"],
  parse(s) {
    const [n1, n2] = s.split(';'); return { nums1: avNums(n1), nums2: avNums(n2) };
  },
  buildStates({nums1, nums2}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    const mapping = {};
    domPushState(seq, { kind: 'init', line: 2, nums2, nums1, i: -1, stack: [...stack], mapping: {...mapping}, explTitle: 'Start', explText: 'Empty stack and mapping.' }, ctx);
    for (let i = 0; i < nums2.length; i++) {
        const num = nums2[i];
        domPushState(seq, { kind: 'scan', line: 4, nums2, nums1, i, stack: [...stack], mapping: {...mapping}, explTitle: `Process ${num}`, explText: `Read ${num} from nums2.` }, ctx);
        while (stack.length > 0 && num > stack[stack.length - 1]) {
            const popped = stack.pop();
            mapping[popped] = num;
            domPushState(seq, { kind: 'pop', line: 6, nums2, nums1, i, stack: [...stack], mapping: {...mapping}, explTitle: 'Found Next Greater', explText: `${num} > ${popped}. Next greater for ${popped} is ${num}. Pop ${popped}.` }, ctx);
        }
        stack.push(num);
        domPushState(seq, { kind: 'push', line: 7, nums2, nums1, i, stack: [...stack], mapping: {...mapping}, explTitle: 'Push', explText: `Push ${num} onto stack.` }, ctx);
    }
    for(let i=0; i<stack.length; i++) mapping[stack[i]] = -1;
    domPushState(seq, { kind: 'done', line: 10, nums2, nums1, i: nums2.length, stack: [], mapping: {...mapping}, explTitle: 'Result', explText: `Remaining stack elements mapped to -1. Mapping complete.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const nums2HTML = s.nums2.map((num, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${num}</span><div class="node-index">${idx}</div></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((v, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    const mappingEntries = Object.keys(s.mapping).map(k => `<div>${k} &rarr; ${s.mapping[k]}</div>`).join('');
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">nums2</div>
          <div class="array-track">${nums2HTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
          <div>
            <div class="panel-heading" style="color:#34d399;">Mapping</div>
            <div style="font-size:1.1rem;color:var(--text);font-family:monospace;">${mappingEntries || '(empty)'}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Min Stack", short: "Min Stack",
  idea: "Store pairs of (value, current_minimum) on the stack so that pushing and popping both value and the minimum are O(1).",
  complexity: "Time O(1) \u00b7 Space O(N)",
  input: "push 5, push 2, push 7, pop, getMin", hint: "comma-separated ops: push X, pop, top, getMin",
  code: ["class MinStack:", "    def __init__(self):", "        self.stack = []", "    def push(self, val):", "        curr_min = min(val, self.stack[-1][1]) if self.stack else val", "        self.stack.append((val, curr_min))", "    def pop(self):", "        self.stack.pop()", "    def top(self):", "        return self.stack[-1][0]", "    def getMin(self):", "        return self.stack[-1][1]"],
  parse(s) {
    return { ops: s.split(',').map(x => x.trim()).filter(x => x) };
  },
  buildStates({ops}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, ops, i: -1, stack: [...stack], explTitle: 'Start', explText: 'Empty stack.' }, ctx);
    for (let i = 0; i < ops.length; i++) {
        const opStr = ops[i];
        const parts = opStr.split(' ');
        const cmd = parts[0];
        const val = parts.length > 1 ? parseInt(parts[1], 10) : null;
        
        domPushState(seq, { kind: 'cmd', line: 4, ops, i, stack: [...stack], explTitle: `Command: ${cmd}`, explText: `Execute ${opStr}` }, ctx);
        
        if (cmd === 'push') {
            const curr_min = stack.length > 0 ? Math.min(val, stack[stack.length - 1].min) : val;
            stack.push({val, min: curr_min});
            domPushState(seq, { kind: 'push', line: 6, ops, i, stack: [...stack], explTitle: 'Push', explText: `Pushed (${val}, min: ${curr_min})` }, ctx);
        } else if (cmd === 'pop') {
            stack.pop();
            domPushState(seq, { kind: 'pop', line: 8, ops, i, stack: [...stack], explTitle: 'Pop', explText: `Popped top element.` }, ctx);
        } else if (cmd === 'getMin') {
            const m = stack[stack.length - 1].min;
            domPushState(seq, { kind: 'getMin', line: 12, ops, i, stack: [...stack], explTitle: 'getMin', explText: `Current min is ${m}.` }, ctx);
        }
    }
    domPushState(seq, { kind: 'done', line: 1, ops, i: ops.length, stack: [...stack], explTitle: 'Done', explText: `Finished all operations.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const opsHTML = s.ops.map((op, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span style="font-size:0.9rem">${op}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((item, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="width:120px; flex-direction:column; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24; right:-40px; top:10px;">← top</div>' : ''}<span style="font-weight:bold">val: ${item.val}</span><span style="font-size:0.8rem;color:#34d399">min: ${item.min}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Operations</div>
          <div class="array-track" style="flex-wrap:wrap">${opsHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack (Val, Min)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center; position:relative;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Evaluate Reverse Polish Notation", short: "RPN",
  idea: "Push numbers onto the stack. When an operator is encountered, pop the last two numbers, apply the operator, and push the result back.",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "2, 1, +, 3, *", hint: "comma-separated tokens",
  code: ["def evalRPN(tokens):", "    stack = []", "    for t in tokens:", "        if t not in '+-*/':", "            stack.append(int(t))", "        else:", "            b, a = stack.pop(), stack.pop()", "            if t == '+': stack.append(a + b)", "            elif t == '-': stack.append(a - b)", "            elif t == '*': stack.append(a * b)", "            else: stack.append(int(a / b))", "    return stack[0]"],
  parse(s) {
    return { tokens: s.split(',').map(x => x.trim()).filter(x => x) };
  },
  buildStates({tokens}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, tokens, i: -1, stack: [...stack], explTitle: 'Start', explText: 'Empty stack.' }, ctx);
    for (let i = 0; i < tokens.length; i++) {
        const t = tokens[i];
        domPushState(seq, { kind: 'scan', line: 3, tokens, i, stack: [...stack], explTitle: `Token: ${t}`, explText: `Process ${t}` }, ctx);
        if (!['+', '-', '*', '/'].includes(t)) {
            stack.push(parseInt(t, 10));
            domPushState(seq, { kind: 'push', line: 5, tokens, i, stack: [...stack], explTitle: 'Push Number', explText: `Push ${t} onto stack.` }, ctx);
        } else {
            const b = stack.pop();
            const a = stack.pop();
            let res;
            if (t === '+') res = a + b;
            else if (t === '-') res = a - b;
            else if (t === '*') res = a * b;
            else res = Math.trunc(a / b);
            stack.push(res);
            domPushState(seq, { kind: 'eval', line: 7, tokens, i, stack: [...stack], explTitle: 'Evaluate', explText: `Pop ${b} and ${a}, calculate ${a} ${t} ${b} = ${res}. Push ${res}.` }, ctx);
        }
    }
    domPushState(seq, { kind: 'done', line: 12, tokens, i: tokens.length, stack: [...stack], explTitle: 'Done', explText: `Final result is ${stack[0]}.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const opsHTML = s.tokens.map((op, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${op}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((v, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Tokens</div>
          <div class="array-track" style="flex-wrap:wrap">${opsHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Generate Parentheses", short: "Gen Parens",
  idea: "Backtracking: build strings by adding '(' if we have some left, and ')' if there are more '(' used than ')'.",
  complexity: "Time O(4^N / sqrt(N)) \u00b7 Space O(N)",
  input: "3", hint: "number of pairs N",
  code: ["def generateParenthesis(n):", "    res = []", "    def backtrack(openN, closedN, path):", "        if openN == closedN == n:", "            res.append(path)", "            return", "        if openN < n:", "            backtrack(openN + 1, closedN, path + '(')", "        if closedN < openN:", "            backtrack(openN, closedN + 1, path + ')')", "    backtrack(0, 0, '')", "    return res"],
  parse(s) {
    return { n: parseInt(s.trim()) || 2 };
  },
  buildStates({n}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const res = [];
    domPushState(seq, { kind: 'init', line: 2, n, path: '', openN: 0, closedN: 0, res: [...res], explTitle: 'Start', explText: `Generating parentheses for n=${n}.` }, ctx);
    function backtrack(openN, closedN, path) {
        domPushState(seq, { kind: 'visit', line: 3, n, path, openN, closedN, res: [...res], explTitle: 'Backtrack', explText: `Path: "${path}" (open: ${openN}, closed: ${closedN})` }, ctx);
        if (openN === n && closedN === n) {
            res.push(path);
            domPushState(seq, { kind: 'found', line: 5, n, path, openN, closedN, res: [...res], explTitle: 'Valid Combo!', explText: `Added "${path}" to results.` }, ctx);
            return;
        }
        if (openN < n) {
            domPushState(seq, { kind: 'go-open', line: 8, n, path, openN, closedN, res: [...res], explTitle: 'Add (', explText: `Can add '(' since ${openN} < ${n}.` }, ctx);
            backtrack(openN + 1, closedN, path + '(');
            domPushState(seq, { kind: 'back-open', line: 8, n, path, openN, closedN, res: [...res], explTitle: 'Backtrack', explText: `Returned from adding '(' path.` }, ctx);
        }
        if (closedN < openN) {
            domPushState(seq, { kind: 'go-close', line: 10, n, path, openN, closedN, res: [...res], explTitle: 'Add )', explText: `Can add ')' since ${closedN} < ${openN}.` }, ctx);
            backtrack(openN, closedN + 1, path + ')');
            domPushState(seq, { kind: 'back-close', line: 10, n, path, openN, closedN, res: [...res], explTitle: 'Backtrack', explText: `Returned from adding ')' path.` }, ctx);
        }
    }
    backtrack(0, 0, '');
    domPushState(seq, { kind: 'done', line: 12, n, path: '', openN: 0, closedN: 0, res: [...res], explTitle: 'Done', explText: `Generated ${res.length} combinations.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const resHTML = s.res.map(r => `<div style="padding:4px 8px; background:#34d39920; border:1px solid #34d399; border-radius:4px;">${r}</div>`).join('');
    container.innerHTML = `
      <div class="glass-panel">
        <div style="font-size:1.2rem; margin-bottom:10px;">Current Path: <strong style="color:var(--accent); font-family:monospace; letter-spacing:2px;">${s.path || '(empty)'}</strong></div>
        <div style="display:flex; gap:20px; color:var(--text-dim);">
            <div>Open: ${s.openN} / ${s.n}</div>
            <div>Closed: ${s.closedN} / ${s.n}</div>
        </div>
        <div style="margin-top:20px; border-top:1px solid var(--border); padding-top:10px;">
            <div class="panel-heading" style="color:#34d399;">Results</div>
            <div style="display:flex; flex-wrap:wrap; gap:10px; font-family:monospace;">${resHTML}</div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Car Fleet", short: "Car Fleet",
  idea: "Sort cars by position. Calculate time to reach target. If a car behind takes less or equal time than the car ahead, it joins the fleet (stack).",
  complexity: "Time O(N log N) \u00b7 Space O(N)",
  input: "12 ; 10, 8, 0, 5, 3 ; 2, 4, 1, 1, 3", hint: "target ; positions ; speeds",
  code: ["def carFleet(target, position, speed):", "    pair = [[p, s] for p, s in zip(position, speed)]", "    stack = []", "    for p, s in sorted(pair)[::-1]:", "        stack.append((target - p) / s)", "        if len(stack) >= 2 and stack[-1] <= stack[-2]:", "            stack.pop()", "    return len(stack)"],
  parse(s) {
    const parts = s.split(';'); return { target: parseInt(parts[0].trim()), pos: avNums(parts[1]), spd: avNums(parts[2]) };
  },
  buildStates({target, pos, spd}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const pairs = pos.map((p, i) => ({p, s: spd[i], initIdx: i}));
    pairs.sort((a, b) => b.p - a.p);
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, target, pairs, i: -1, stack: [...stack], explTitle: 'Start', explText: 'Sort cars by descending position.' }, ctx);
    
    for (let i = 0; i < pairs.length; i++) {
        const {p, s} = pairs[i];
        const time = (target - p) / s;
        domPushState(seq, { kind: 'calc', line: 4, target, pairs, i, stack: [...stack], time, explTitle: 'Calculate Time', explText: `Car at ${p} with speed ${s}. Time to target: (${target} - ${p}) / ${s} = ${time.toFixed(2)}` }, ctx);
        
        stack.push(time);
        domPushState(seq, { kind: 'push', line: 5, target, pairs, i, stack: [...stack], time, explTitle: 'Push Time', explText: `Push time ${time.toFixed(2)} to stack.` }, ctx);
        
        if (stack.length >= 2 && stack[stack.length - 1] <= stack[stack.length - 2]) {
            stack.pop();
            domPushState(seq, { kind: 'pop', line: 7, target, pairs, i, stack: [...stack], time, explTitle: 'Join Fleet', explText: `Time ${time.toFixed(2)} <= previous fleet time ${stack[stack.length - 1].toFixed(2)}. It catches up and joins the fleet. Pop it.` }, ctx);
        }
    }
    domPushState(seq, { kind: 'done', line: 8, target, pairs, i: pairs.length, stack: [...stack], time: 0, explTitle: 'Done', explText: `Total fleets: ${stack.length}` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const carsHTML = s.pairs.map((car, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="width:100px; flex-direction:column; ${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span style="font-weight:bold">Pos: ${car.p}</span><span style="font-size:0.8rem">Spd: ${car.s}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((t, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="width:90px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>T: ${t.toFixed(2)}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Cars (Sorted DESC) | Target: ${s.target}</div>
          <div class="array-track" style="flex-wrap:wrap">${carsHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Fleet Stack (Time)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Online Stock Span", short: "Stock Span",
  idea: "Monotonic decreasing stack storing pairs of (price, span). If today's price >= top price, pop and add its span to today's span.",
  complexity: "Time O(N) amortized \u00b7 Space O(N)",
  input: "100, 80, 60, 70, 60, 75, 85", hint: "comma-separated prices",
  code: ["class StockSpanner:", "    def __init__(self):", "        self.stack = []  # pair (price, span)", "    def next(self, price):", "        span = 1", "        while self.stack and self.stack[-1][0] <= price:", "            span += self.stack.pop()[1]", "        self.stack.append((price, span))", "        return span"],
  parse(s) {
    return { prices: avNums(s) };
  },
  buildStates({prices}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, prices, i: -1, stack: [...stack], span: 0, explTitle: 'Start', explText: 'Empty stack.' }, ctx);
    for (let i = 0; i < prices.length; i++) {
        const price = prices[i];
        let span = 1;
        domPushState(seq, { kind: 'next', line: 4, prices, i, stack: [...stack], span, explTitle: `Next Price: ${price}`, explText: `Initialize span = 1 for price ${price}.` }, ctx);
        
        while (stack.length > 0 && stack[stack.length - 1].price <= price) {
            const popped = stack.pop();
            span += popped.span;
            domPushState(seq, { kind: 'pop', line: 6, prices, i, stack: [...stack], span, explTitle: 'Pop & Add', explText: `Top price ${popped.price} <= ${price}. Pop it and add its span ${popped.span}. New span = ${span}.` }, ctx);
        }
        
        stack.push({price, span});
        domPushState(seq, { kind: 'push', line: 8, prices, i, stack: [...stack], span, explTitle: 'Push', explText: `Push (${price}, span: ${span}) to stack.` }, ctx);
    }
    domPushState(seq, { kind: 'done', line: 9, prices, i: prices.length, stack: [...stack], span: 0, explTitle: 'Done', explText: `Processed all prices.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const pricesHTML = s.prices.map((p, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${p}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((item, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="width:110px; flex-direction:column; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24; right:-40px; top:10px;">← top</div>' : ''}<span style="font-weight:bold">P: ${item.price}</span><span style="font-size:0.8rem;color:#34d399">Span: ${item.span}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Prices</div>
          <div class="array-track" style="flex-wrap:wrap">${pricesHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack (Price, Span)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;position:relative;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Largest Rectangle in Histogram", short: "Histogram",
  idea: "Monotonic increasing stack of (index, height). When finding a shorter bar, pop taller bars from stack, calculating their area with width extending back to their popped index.",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "2, 1, 5, 6, 2, 3", hint: "comma-separated heights",
  code: ["def largestRectangleArea(heights):", "    maxArea = 0", "    stack = []  # pair: (index, height)", "    for i, h in enumerate(heights):", "        start = i", "        while stack and stack[-1][1] > h:", "            index, height = stack.pop()", "            maxArea = max(maxArea, height * (i - index))", "            start = index", "        stack.append((start, h))", "    for i, h in stack:", "        maxArea = max(maxArea, h * (len(heights) - i))", "    return maxArea"],
  parse(s) {
    return { heights: avNums(s) };
  },
  buildStates({heights}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    let maxArea = 0;
    domPushState(seq, { kind: 'init', line: 2, heights, i: -1, stack: [...stack], maxArea, explTitle: 'Start', explText: 'Initialize maxArea = 0 and empty stack.' }, ctx);
    
    for (let i = 0; i < heights.length; i++) {
        const h = heights[i];
        let start = i;
        domPushState(seq, { kind: 'scan', line: 4, heights, i, stack: [...stack], maxArea, explTitle: `Index ${i}`, explText: `Read height ${h}. Start = ${i}.` }, ctx);
        
        while (stack.length > 0 && stack[stack.length - 1].h > h) {
            const popped = stack.pop();
            const area = popped.h * (i - popped.idx);
            if (area > maxArea) maxArea = area;
            start = popped.idx;
            domPushState(seq, { kind: 'pop', line: 6, heights, i, stack: [...stack], maxArea, explTitle: 'Pop & Calculate', explText: `Top height ${popped.h} > ${h}. Pop it. Area = ${popped.h} * (${i} - ${popped.idx}) = ${area}. Max area = ${maxArea}. Extend start back to ${start}.` }, ctx);
        }
        stack.push({idx: start, h});
        domPushState(seq, { kind: 'push', line: 10, heights, i, stack: [...stack], maxArea, explTitle: 'Push', explText: `Push (index: ${start}, height: ${h}) to stack.` }, ctx);
    }
    
    domPushState(seq, { kind: 'end-scan', line: 11, heights, i: heights.length, stack: [...stack], maxArea, explTitle: 'End Scan', explText: 'Finished scanning. Now process remaining stack elements.' }, ctx);
    while (stack.length > 0) {
        const popped = stack.pop();
        const area = popped.h * (heights.length - popped.idx);
        if (area > maxArea) maxArea = area;
        domPushState(seq, { kind: 'drain', line: 12, heights, i: heights.length, stack: [...stack], maxArea, explTitle: 'Drain Stack', explText: `Pop (idx:${popped.idx}, h:${popped.h}). Area = ${popped.h} * (${heights.length} - ${popped.idx}) = ${area}. Max = ${maxArea}.` }, ctx);
    }
    domPushState(seq, { kind: 'done', line: 14, heights, i: heights.length, stack: [], maxArea, explTitle: 'Done', explText: `Final max area is ${maxArea}.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const heightsHTML = s.heights.map((h, idx) => {
        const isActive = s.i === idx;
        const ht = Math.max(10, h * 15);
        return `<div style="display:flex;flex-direction:column;align-items:center;margin-right:2px;">
            <div style="height:100px;display:flex;align-items:flex-end;">
                <div style="width:30px;height:${ht}px;background:${isActive ? 'var(--accent)' : 'var(--text-dim)'};"></div>
            </div>
            <div style="font-size:0.8rem;margin-top:2px;color:${isActive ? 'var(--accent)' : 'var(--text-dim)'}">${h}</div>
        </div>`;
    }).join('');
    
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((item, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="width:110px; flex-direction:column; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24; right:-40px; top:10px;">← top</div>' : ''}<span style="font-weight:bold">Idx: ${item.idx}</span><span style="font-size:0.8rem;color:#34d399">H: ${item.h}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div style="display:flex;justify-content:space-between;">
          <div>
            <div class="panel-heading" style="color:var(--accent);">Heights Histogram</div>
            <div style="display:flex; align-items:flex-end; border-bottom:1px solid var(--border); padding-bottom:2px;">${heightsHTML}</div>
          </div>
          <div style="font-size:1.5rem;font-weight:bold;color:#34d399;margin-top:20px;">Max Area: ${s.maxArea}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack (Start Idx, Height)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;position:relative;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Basic Calculator II", short: "Calculator",
  idea: "Use a stack to store numbers to be added later. When encountering *, /, perform the operation with the stack's top immediately.",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "3+2*2", hint: "string expression",
  code: ["def calculate(s: str) -> int:", "    if not s: return 0", "    stack, curr_num, op = [], 0, '+'", "    s += '+'", "    for char in s:", "        if char.isdigit():", "            curr_num = curr_num * 10 + int(char)", "        elif char in '+-*/':", "            if op == '+': stack.append(curr_num)", "            elif op == '-': stack.append(-curr_num)", "            elif op == '*': stack[-1] = stack[-1] * curr_num", "            elif op == '/': stack[-1] = int(stack[-1] / curr_num)", "            curr_num = 0", "            op = char", "    return sum(stack)"],
  parse(s) {
    return { str: s.replace(/\s+/g, '') + '+' };
  },
  buildStates({str}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    let curr_num = 0, op = '+';
    domPushState(seq, { kind: 'init', line: 3, str, i: -1, stack: [...stack], curr_num, op, explTitle: 'Start', explText: 'Init curr_num=0, op="+", empty stack. Appended + to end to trigger last eval.' }, ctx);
    
    for (let i = 0; i < str.length; i++) {
        const char = str[i];
        domPushState(seq, { kind: 'scan', line: 5, str, i, stack: [...stack], curr_num, op, explTitle: `Char: ${char}`, explText: `Read char '${char}'.` }, ctx);
        
        if (char >= '0' && char <= '9') {
            curr_num = curr_num * 10 + parseInt(char, 10);
            domPushState(seq, { kind: 'digit', line: 7, str, i, stack: [...stack], curr_num, op, explTitle: 'Digit', explText: `Update curr_num = ${curr_num}.` }, ctx);
        } else if (['+', '-', '*', '/'].includes(char)) {
            if (op === '+') {
                stack.push(curr_num);
            } else if (op === '-') {
                stack.push(-curr_num);
            } else if (op === '*') {
                stack[stack.length - 1] = stack[stack.length - 1] * curr_num;
            } else if (op === '/') {
                stack[stack.length - 1] = Math.trunc(stack[stack.length - 1] / curr_num);
            }
            domPushState(seq, { kind: 'op', line: 9, str, i, stack: [...stack], curr_num, op: char, explTitle: `Eval ${op}`, explText: `Previous operator was '${op}'. Applied it with ${curr_num} to stack. Reset curr_num=0, new op='${char}'.` }, ctx);
            curr_num = 0;
            op = char;
        }
    }
    const res = stack.reduce((a,b)=>a+b, 0);
    domPushState(seq, { kind: 'done', line: 15, str, i: str.length, stack: [...stack], curr_num, op, explTitle: 'Done', explText: `Sum of stack elements: ${res}` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const strHTML = s.str.split('').map((char, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${char}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((v, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div style="display:flex;justify-content:space-between">
            <div>
              <div class="panel-heading" style="color:var(--accent);">Expression (padded with +)</div>
              <div class="array-track">${strHTML}</div>
            </div>
            <div style="font-size:1.2rem; margin-top:20px; border-left:1px solid var(--border); padding-left:20px;">
                <div>Op: <span style="color:#f87171;font-weight:bold">${s.op}</span></div>
                <div>Num: <span style="color:#38bdf8;font-weight:bold">${s.curr_num}</span></div>
            </div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Asteroid Collision", short: "Asteroids",
  idea: "Use a stack. For each asteroid, if it's moving right (>0) or the stack is empty, push it. If it's moving left (<0), resolve collisions with right-moving asteroids on the stack.",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "5, 10, -5", hint: "comma-separated asteroid sizes",
  code: ["def asteroidCollision(asteroids):", "    stack = []", "    for a in asteroids:", "        while stack and a < 0 < stack[-1]:", "            if stack[-1] < -a:", "                stack.pop()", "                continue", "            elif stack[-1] == -a:", "                stack.pop()", "            break", "        else:", "            stack.append(a)", "    return stack"],
  parse(s) {
    return { ast: avNums(s) };
  },
  buildStates({ast}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    domPushState(seq, { kind: 'init', line: 2, ast, i: -1, stack: [...stack], explTitle: 'Start', explText: 'Empty stack.' }, ctx);
    
    for (let i = 0; i < ast.length; i++) {
        const a = ast[i];
        domPushState(seq, { kind: 'scan', line: 3, ast, i, stack: [...stack], explTitle: `Asteroid ${a}`, explText: `Read asteroid ${a}.` }, ctx);
        
        let survived = true;
        while (stack.length > 0 && a < 0 && stack[stack.length - 1] > 0) {
            const top = stack[stack.length - 1];
            if (top < -a) {
                stack.pop();
                domPushState(seq, { kind: 'explode-top', line: 6, ast, i, stack: [...stack], explTitle: 'Collision', explText: `Right asteroid ${top} is smaller than left asteroid ${a}. ${top} explodes.` }, ctx);
                continue;
            } else if (top === -a) {
                stack.pop();
                survived = false;
                domPushState(seq, { kind: 'explode-both', line: 9, ast, i, stack: [...stack], explTitle: 'Collision', explText: `Asteroids ${top} and ${a} are same size. Both explode.` }, ctx);
                break;
            } else {
                survived = false;
                domPushState(seq, { kind: 'explode-new', line: 10, ast, i, stack: [...stack], explTitle: 'Collision', explText: `Right asteroid ${top} is larger than left asteroid ${a}. ${a} explodes.` }, ctx);
                break;
            }
        }
        
        if (survived) {
            stack.push(a);
            domPushState(seq, { kind: 'push', line: 12, ast, i, stack: [...stack], explTitle: 'Push', explText: `Asteroid ${a} survives and is pushed to stack.` }, ctx);
        }
    }
    domPushState(seq, { kind: 'done', line: 13, ast, i: ast.length, stack: [...stack], explTitle: 'Done', explText: `Remaining asteroids: ${stack.join(', ')}` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const astHTML = s.ast.map((a, idx) => {
        const isActive = s.i === idx;
        const col = a > 0 ? '#38bdf8' : '#f87171'; // Blue right, Red left
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? `border-color:${col};` : ''} color:${col};">${isActive ? `<div class="pointer" style="color:${col};">↓</div>` : ''}<span>${a}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((a, idx) => {
        const isTop = idx === 0;
        const col = a > 0 ? '#38bdf8' : '#f87171';
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''} color:${col};">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${a}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div>
          <div class="panel-heading" style="color:var(--accent);">Asteroids</div>
          <div class="array-track" style="flex-wrap:wrap">${astHTML}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Remove K Digits", short: "Remove K",
  idea: "Monotonic increasing stack. If the current digit is smaller than the top of the stack, pop the stack to make the number smaller, up to k times.",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "1432219 ; 3", hint: "num ; k",
  code: ["def removeKdigits(num, k):", "    stack = []", "    for d in num:", "        while k > 0 and stack and stack[-1] > d:", "            stack.pop()", "            k -= 1", "        stack.append(d)", "    while k > 0:", "        stack.pop()", "        k -= 1", "    res = ''.join(stack).lstrip('0')", "    return res if res else '0'"],
  parse(s) {
    const parts = s.split(';'); return { numStr: parts[0].trim(), k: parseInt(parts[1].trim()) };
  },
  buildStates({numStr, k}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    let remK = k;
    domPushState(seq, { kind: 'init', line: 2, numStr, i: -1, stack: [...stack], remK, explTitle: 'Start', explText: `Remove ${remK} digits.` }, ctx);
    
    for (let i = 0; i < numStr.length; i++) {
        const d = numStr[i];
        domPushState(seq, { kind: 'scan', line: 3, numStr, i, stack: [...stack], remK, explTitle: `Digit ${d}`, explText: `Read digit ${d}.` }, ctx);
        
        while (remK > 0 && stack.length > 0 && stack[stack.length - 1] > d) {
            const popped = stack.pop();
            remK -= 1;
            domPushState(seq, { kind: 'pop', line: 5, numStr, i, stack: [...stack], remK, explTitle: 'Pop larger', explText: `Top digit ${popped} > ${d}. Pop it to minimize the number. K is now ${remK}.` }, ctx);
        }
        stack.push(d);
        domPushState(seq, { kind: 'push', line: 7, numStr, i, stack: [...stack], remK, explTitle: 'Push', explText: `Push digit ${d}.` }, ctx);
    }
    
    domPushState(seq, { kind: 'post', line: 8, numStr, i: numStr.length, stack: [...stack], remK, explTitle: 'End Scan', explText: `Finished scanning. K remaining: ${remK}.` }, ctx);
    while (remK > 0) {
        stack.pop();
        remK -= 1;
        domPushState(seq, { kind: 'pop-end', line: 9, numStr, i: numStr.length, stack: [...stack], remK, explTitle: 'Pop from end', explText: `Pop from end because number is already monotonic increasing. K is now ${remK}.` }, ctx);
    }
    
    let res = stack.join('').replace(/^0+/, '');
    if (!res) res = '0';
    domPushState(seq, { kind: 'done', line: 12, numStr, i: numStr.length, stack: [...stack], remK, explTitle: 'Done', explText: `Final result: ${res}` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const strHTML = s.numStr.split('').map((char, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${char}</span></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((v, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="min-width:40px; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24;">← top</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div style="display:flex;justify-content:space-between;">
          <div>
            <div class="panel-heading" style="color:var(--accent);">Number</div>
            <div class="array-track">${strHTML}</div>
          </div>
          <div style="font-size:1.5rem;font-weight:bold;color:#f87171;margin-top:20px;">k left: ${s.remK}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack (Number built so far)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('06_stack', {
  type: 'dom',
  title: "Sum of Subarray Minimums", short: "Subarray Mins",
  idea: "Use a monotonic stack to find the left and right bounds where each element is the minimum. The number of subarrays where arr[i] is the minimum is (i - left) * (right - i).",
  complexity: "Time O(N) \u00b7 Space O(N)",
  input: "3, 1, 2, 4", hint: "comma-separated numbers",
  code: ["def sumSubarrayMins(arr):", "    MOD = 10**9 + 7", "    res = 0", "    stack = []  # pairs: (index, value)", "    for i in range(len(arr) + 1):", "        val = arr[i] if i < len(arr) else 0", "        while stack and stack[-1][1] > val:", "            j, m = stack.pop()", "            left = j - stack[-1][0] if stack else j + 1", "            right = i - j", "            res = (res + m * left * right) % MOD", "        stack.append((i, val))", "    return res"],
  parse(s) {
    return { arr: avNums(s) };
  },
  buildStates({arr}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const stack = [];
    let res = 0;
    domPushState(seq, { kind: 'init', line: 4, arr, i: -1, stack: [...stack], res, explTitle: 'Start', explText: 'Empty stack. Result = 0.' }, ctx);
    
    for (let i = 0; i <= arr.length; i++) {
        const val = i < arr.length ? arr[i] : 0;
        domPushState(seq, { kind: 'scan', line: 6, arr, i, stack: [...stack], res, explTitle: `Index ${i}`, explText: `Read value ${val} (using 0 at end to flush stack).` }, ctx);
        
        while (stack.length > 0 && stack[stack.length - 1].val > val) {
            const popped = stack.pop();
            const left = stack.length > 0 ? (popped.idx - stack[stack.length - 1].idx) : (popped.idx + 1);
            const right = i - popped.idx;
            const contrib = popped.val * left * right;
            res = (res + contrib) % 1000000007;
            domPushState(seq, { kind: 'pop', line: 8, arr, i, stack: [...stack], res, explTitle: 'Calculate Contribution', explText: `Top value ${popped.val} > ${val}. Popped element was minimum for ${left} left elements and ${right} right elements. Contribution = ${popped.val} * ${left} * ${right} = ${contrib}. New res = ${res}.` }, ctx);
        }
        stack.push({idx: i, val});
        domPushState(seq, { kind: 'push', line: 12, arr, i, stack: [...stack], res, explTitle: 'Push', explText: `Push (idx: ${i}, val: ${val}).` }, ctx);
    }
    
    domPushState(seq, { kind: 'done', line: 13, arr, i: arr.length, stack: [...stack], res, explTitle: 'Done', explText: `Final sum is ${res}.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const arrHTML = s.arr.map((val, idx) => {
        const isActive = s.i === idx;
        return `<div class="array-node ${isActive ? 'active-1' : ''}" style="${isActive ? 'border-color:var(--accent);' : ''}">${isActive ? '<div class="pointer" style="color:var(--accent);">↓</div>' : ''}<span>${val}</span><div class="node-index">${idx}</div></div>`;
    }).join('');
    const stackHTML = s.stack.length ? s.stack.slice().reverse().map((item, idx) => {
        const isTop = idx === 0;
        return `<div class="array-node ${isTop ? 'active-2' : ''}" style="width:110px; flex-direction:column; ${isTop ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isTop ? '<div class="pointer" style="color:#fbbf24; right:-40px; top:10px;">← top</div>' : ''}<span style="font-weight:bold">Idx: ${item.idx}</span><span style="font-size:0.8rem;color:#34d399">Val: ${item.val}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty)</div>';
    
    container.innerHTML = `
      <div class="glass-panel arrays-container">
        <div style="display:flex;justify-content:space-between;">
          <div>
            <div class="panel-heading" style="color:var(--accent);">Array (padded with 0 at the end)</div>
            <div class="array-track">${arrHTML}</div>
          </div>
          <div style="font-size:1.5rem;font-weight:bold;color:#34d399;margin-top:20px;">Res: ${s.res}</div>
        </div>
        <div style="display:flex;gap:40px;margin-top:20px;">
          <div>
            <div class="panel-heading" style="color:#fbbf24;">Stack (Idx, Val)</div>
            <div style="display:flex;flex-direction:column;gap:5px;align-items:center;position:relative;">${stackHTML}</div>
          </div>
        </div>
      </div>`;

  }
});



defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: "Implement Stack using Queues", short: "Stack via Queues",
  idea: "We need LIFO behavior but only have FIFO queues. We can use a single queue. When pushing an element, we add it to the back, then pop all previous elements and push them to the back again. This makes the new element sit at the front!",
  complexity: "Time O(n) for push, O(1) for pop \u00b7 Space O(n)",
  input: "push 1, push 2, top, pop, empty", hint: "comma-separated operations (push X, pop, top, empty)",
  code: ["class MyStack:", "    def __init__(self):", "        self.q = deque()", "", "    def push(self, x: int) -> None:", "        self.q.append(x)", "        for _ in range(len(self.q) - 1):", "            self.q.append(self.q.popleft())", "", "    def pop(self) -> int:", "        return self.q.popleft()", "", "    def top(self) -> int:", "        return self.q[0]", "", "    def empty(self) -> bool:", "        return len(self.q) == 0"],
  parse(s) {
    return { ops: s.split(',').map(x => x.trim().toLowerCase()).filter(Boolean) };
  },
  buildStates({ops}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const q = [];
    domPushState(seq, { kind: 'init', line: 2, ops, opIdx: -1, q: [...q], result: null, explTitle: 'Start', explText: 'Initialize an empty queue.' }, ctx);
    
    for (let i = 0; i < ops.length; i++) {
        const opStr = ops[i];
        const parts = opStr.split(' ');
        const cmd = parts[0];
        const val = parts.length > 1 ? parseInt(parts[1], 10) : null;
        
        domPushState(seq, { kind: 'cmd', line: 4, ops, opIdx: i, q: [...q], result: null, explTitle: `Operation: ${opStr}`, explText: `Processing ${opStr}.` }, ctx);
        
        if (cmd === 'push') {
            q.push(val);
            domPushState(seq, { kind: 'push', line: 6, ops, opIdx: i, q: [...q], result: null, explTitle: `Push ${val}`, explText: `Append ${val} to the back of the queue.` }, ctx);
            
            const n = q.length;
            for (let k = 0; k < n - 1; k++) {
                const popped = q.shift();
                q.push(popped);
                domPushState(seq, { kind: 'rotate', line: 8, ops, opIdx: i, q: [...q], result: null, explTitle: `Rotate Queue`, explText: `Pop front element ${popped} and push it back. This moves the newly pushed element closer to the front.` }, ctx);
            }
        } else if (cmd === 'pop') {
            const result = q.shift();
            domPushState(seq, { kind: 'pop', line: 11, ops, opIdx: i, q: [...q], result, explTitle: 'Pop', explText: `Remove and return the front of the queue: ${result}.` }, ctx);
        } else if (cmd === 'top') {
            const result = q[0];
            domPushState(seq, { kind: 'top', line: 14, ops, opIdx: i, q: [...q], result, explTitle: 'Top', explText: `Front of the queue is ${result}.` }, ctx);
        } else if (cmd === 'empty') {
            const result = q.length === 0;
            domPushState(seq, { kind: 'empty', line: 17, ops, opIdx: i, q: [...q], result, explTitle: 'Empty', explText: `Is queue empty? ${result}.` }, ctx);
        }
    }
    domPushState(seq, { kind: 'done', line: -1, ops, opIdx: ops.length, q: [...q], result: null, explTitle: 'Done', explText: `All operations completed.` }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const opsList = s.ops.map((op, i) => {
        const isCur = s.opIdx === i;
        const isPast = s.opIdx > i;
        return `<div style="padding:4px 8px;border-radius:4px;font-family:var(--mono);font-size:12px;${isCur ? 'background:var(--accent);color:var(--accent-ink);font-weight:bold;' : isPast ? 'color:var(--text-dim);text-decoration:line-through;' : 'color:var(--text);'}">${op}</div>`;
    }).join('');
    
    const qHTML = s.q.length ? s.q.map((v, idx) => {
        const isFront = idx === 0;
        return `<div class="array-node ${isFront ? 'active-2' : ''}" style="min-width:40px; ${isFront ? 'border-color:#fbbf24; background:#fbbf2420;' : ''}">${isFront ? '<div class="pointer" style="color:#fbbf24; top:-30px;">↓ Front</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty queue)</div>';
    
    const resultBox = s.result !== null
      ? `<div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:color-mix(in srgb, #34d399 15%, transparent);border:1px solid #34d399;color:#34d399;font-weight:bold;text-align:center;">Returned: ${s.result}</div>`
      : '';
      
    container.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:8px;">
        ${opsList}
      </div>
      <div class="glass-panel" style="display:flex;flex-direction:column;align-items:center;padding:40px 20px;">
        <div class="panel-heading" style="color:var(--accent);">Queue State</div>
        <div style="display:flex;gap:10px;margin-top:20px;min-height:60px;">${qHTML}</div>
        ${resultBox}
      </div>`;

  }
});



defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: "Number of Recent Calls", short: "Recent Calls",
  idea: "We need to count how many requests happened in the last 3000 milliseconds. Store request times in a queue. When a new ping(t) arrives, append t, then pop from the front all times strictly less than t - 3000. Return queue length.",
  complexity: "Time O(1) amortized \u00b7 Space O(N)",
  input: "1, 100, 3001, 3002", hint: "comma-separated ping timestamps",
  code: ["class RecentCounter:", "    def __init__(self):", "        self.q = deque()", "", "    def ping(self, t: int) -> int:", "        self.q.append(t)", "        while self.q and self.q[0] < t - 3000:", "            self.q.popleft()", "        return len(self.q)"],
  parse(s) {
    return { pings: avNums(s) };
  },
  buildStates({pings}) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    
    const q = [];
    domPushState(seq, { kind: 'init', line: 2, pings, i: -1, q: [...q], result: null, explTitle: 'Start', explText: 'Initialize an empty queue to hold request timestamps.' }, ctx);
    
    for (let i = 0; i < pings.length; i++) {
        const t = pings[i];
        domPushState(seq, { kind: 'ping', line: 5, pings, i, q: [...q], result: null, explTitle: `ping(${t})`, explText: `New request arrives at time ${t}.` }, ctx);
        
        q.push(t);
        domPushState(seq, { kind: 'push', line: 6, pings, i, q: [...q], result: null, explTitle: `Append ${t}`, explText: `Add ${t} to the queue.` }, ctx);
        
        const limit = t - 3000;
        domPushState(seq, { kind: 'check', line: 7, pings, i, q: [...q], result: null, explTitle: 'Check Old Pings', explText: `We only keep requests >= ${t} - 3000 = ${limit}.` }, ctx);
        
        while (q.length > 0 && q[0] < limit) {
            const popped = q.shift();
            domPushState(seq, { kind: 'pop', line: 8, pings, i, q: [...q], result: null, explTitle: 'Remove Old Ping', explText: `${popped} is older than ${limit}. Remove it.` }, ctx);
        }
        
        const result = q.length;
        domPushState(seq, { kind: 'return', line: 9, pings, i, q: [...q], result, explTitle: 'Return Count', explText: `Queue size is ${result}. Return ${result}.` }, ctx);
    }
    domPushState(seq, { kind: 'done', line: -1, pings, i: pings.length, q: [...q], result: null, explTitle: 'Done', explText: 'Finished processing all pings.' }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    
    const pingsList = s.pings.map((p, idx) => {
        const isActive = s.i === idx;
        const isPast = s.i > idx;
        return `<div style="padding:4px 8px;border-radius:4px;font-family:var(--mono);font-size:12px;${isActive ? 'background:var(--accent);color:var(--accent-ink);font-weight:bold;' : isPast ? 'color:var(--text-dim);' : 'color:var(--text);'}">${p}</div>`;
    }).join('');
    
    const qHTML = s.q.length ? s.q.map((v, idx) => {
        const isFront = idx === 0;
        return `<div class="array-node" style="min-width:50px; border-color:#38bdf8; background:#38bdf820; color:#38bdf8">${isFront ? '<div class="pointer" style="color:#38bdf8; top:-30px;">↓ Front</div>' : ''}<span>${v}</span></div>`;
    }).join('') : '<div style="padding:10px;color:var(--text-dim);">(empty queue)</div>';
    
    const resultBox = s.result !== null
      ? `<div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:color-mix(in srgb, #34d399 15%, transparent);border:1px solid #34d399;color:#34d399;font-weight:bold;text-align:center;">Returned: ${s.result}</div>`
      : '';
      
    container.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:8px;">
        ${pingsList}
      </div>
      <div class="glass-panel" style="display:flex;flex-direction:column;align-items:center;padding:40px 20px;">
        <div class="panel-heading" style="color:var(--accent);">Queue State (Valid Pings)</div>
        <div style="display:flex;gap:10px;margin-top:20px;min-height:60px;">${qHTML}</div>
        ${resultBox}
      </div>`;

  }
});


defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: 'Design Circular Queue', short: 'Circular Queue',
  idea: 'Use a fixed-size array along with a <code>head</code> index and a <code>size</code> counter. The insertion index (tail) is computed dynamically as <code>(head + size) % capacity</code>. No need to compare head and tail, because size unambiguously tells us if it is full or empty.',
  complexity: 'Time O(1) · Space O(k)',
  input: 'init 3, enQueue 1, enQueue 2, deQueue, enQueue 3, enQueue 4, Rear, isFull', 
  hint: 'comma-separated operations (init k, enQueue v, deQueue, Front, Rear, isEmpty, isFull)',
  code: [
    'class MyCircularQueue:',
    '    def __init__(self, k: int):',
    '        self.buf = [0] * k',
    '        self.cap = k',
    '        self.head = 0',
    '        self.size = 0',
    '',
    '    def enQueue(self, value: int) -> bool:',
    '        if self.size == self.cap: return False',
    '        tail = (self.head + self.size) % self.cap',
    '        self.buf[tail] = value',
    '        self.size += 1',
    '        return True',
    '',
    '    def deQueue(self) -> bool:',
    '        if self.size == 0: return False',
    '        self.head = (self.head + 1) % self.cap',
    '        self.size -= 1',
    '        return True',
    '',
    '    def Front(self) -> int:',
    '        if self.size == 0: return -1',
    '        return self.buf[self.head]',
    '',
    '    def Rear(self) -> int:',
    '        if self.size == 0: return -1',
    '        return self.buf[(self.head + self.size - 1) % self.cap]',
    '',
    '    def isEmpty(self) -> bool:',
    '        return self.size == 0',
    '',
    '    def isFull(self) -> bool:',
    '        return self.size == self.cap'
  ],
  parse(s) {
    const ops = s.split(',').map(x => x.trim()).filter(Boolean);
    if (!ops.length) throw new Error('Enter operations');
    if (!ops[0].toLowerCase().startsWith('init')) {
        throw new Error('First operation must be "init k"');
    }
    return { ops };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let cap = 0, head = 0, size = 0, buf = [];

    const initMatch = ops[0].match(/init\s+(\d+)/i);
    if (initMatch) {
      cap = parseInt(initMatch[1]);
      buf = Array(cap).fill(null);
    } else {
      cap = 3; 
      buf = Array(cap).fill(null);
    }

    domPushState(seq, {
      kind: 'init', line: 2,
      ops, opIdx: 0, buf: [...buf], cap, head, size, result: null, targetIdx: -1,
      explTitle: 'Initialization',
      explText: `Created circular queue with capacity ${cap}.`,
      pause: true
    }, ctx);

    for (let i = 1; i < ops.length; i++) {
      const parts = ops[i].split(/\s+/);
      const cmd = parts[0].toLowerCase();
      let result = null;

      if (cmd.startsWith('enq')) {
        const val = parseInt(parts[1]);
        if (size === cap) {
          result = false;
          domPushState(seq, {
            kind: 'enQueue', line: 8, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `enQueue(${val})`, explText: `Queue is full (size == cap). Cannot enqueue.`, pause: true
          }, ctx);
        } else {
          const tail = (head + size) % cap;
          domPushState(seq, {
            kind: 'enQueue-step', line: 9, ops, opIdx: i, buf: [...buf], cap, head, size, result: null, targetIdx: tail,
            explTitle: `enQueue(${val})`, explText: `Queue not full. Calculate tail = (head + size) % cap = (${head} + ${size}) % ${cap} = ${tail}.`, pause: false
          }, ctx);
          
          buf[tail] = val;
          size += 1;
          result = true;
          domPushState(seq, {
            kind: 'enQueue-done', line: 12, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: tail,
            explTitle: `enQueue(${val})`, explText: `Inserted ${val} at index ${tail}. Incremented size to ${size}.`, pause: true
          }, ctx);
        }
      } else if (cmd.startsWith('deq')) {
        if (size === 0) {
          result = false;
          domPushState(seq, {
            kind: 'deQueue', line: 15, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deQueue()`, explText: `Queue is empty (size == 0). Cannot dequeue.`, pause: true
          }, ctx);
        } else {
          head = (head + 1) % cap;
          size -= 1;
          result = true;
          domPushState(seq, {
            kind: 'deQueue-done', line: 18, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deQueue()`, explText: `Dequeued element. Updated head to ${head} and decremented size to ${size}. Note: The old value is still in the buffer but is outside the logical size.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'front') {
        if (size === 0) {
          result = -1;
          domPushState(seq, {
            kind: 'front', line: 21, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `Front()`, explText: `Queue is empty, return -1.`, pause: true
          }, ctx);
        } else {
          result = buf[head];
          domPushState(seq, {
            kind: 'front', line: 22, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: head,
            explTitle: `Front()`, explText: `Return element at head (${head}), which is ${result}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'rear') {
        if (size === 0) {
          result = -1;
          domPushState(seq, {
            kind: 'rear', line: 25, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `Rear()`, explText: `Queue is empty, return -1.`, pause: true
          }, ctx);
        } else {
          const tail = (head + size - 1) % cap;
          result = buf[tail];
          domPushState(seq, {
            kind: 'rear', line: 26, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: tail,
            explTitle: `Rear()`, explText: `Tail is at (head + size - 1) % cap = (${head} + ${size} - 1) % ${cap} = ${tail}. Returning ${result}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'isempty') {
        result = size === 0;
        domPushState(seq, {
          kind: 'isempty', line: 29, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
          explTitle: `isEmpty()`, explText: `Is size == 0? ${result}.`, pause: true
        }, ctx);
      } else if (cmd === 'isfull') {
        result = size === cap;
        domPushState(seq, {
          kind: 'isfull', line: 32, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
          explTitle: `isFull()`, explText: `Is size == cap (${cap})? ${result}.`, pause: true
        }, ctx);
      }
    }
    
    domPushState(seq, {
      kind: 'done', line: -1, ops, opIdx: ops.length, buf: [...buf], cap, head, size, result: null, targetIdx: -1,
      explTitle: 'Finished', explText: 'All operations complete.', pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s) {
    const opsList = s.ops.map((op, i) => {
      const isCur = s.opIdx === i;
      const isPast = s.opIdx > i;
      return `<div style="padding:4px 8px;border-radius:4px;font-family:var(--mono);font-size:12px;${isCur ? 'background:var(--accent);color:var(--accent-ink);font-weight:bold;' : isPast ? 'color:var(--text-dim);text-decoration:line-through;' : 'color:var(--text);'}">${op}</div>`;
    }).join('');

    const validIndices = new Set();
    for(let k = 0; k < s.size; k++) {
        validIndices.add((s.head + k) % s.cap);
    }

    const arrHTML = s.buf.map((val, idx) => {
        const isHead = idx === s.head && s.size > 0;
        const isTarget = idx === s.targetIdx;
        const isValid = validIndices.has(idx);
        
        let labelHTML = '';
        if (isTarget) {
            labelHTML = `<div style="position:absolute;top:-25px;font-size:10px;font-weight:bold;color:#38bdf8;">Target</div><div class="pointer" style="opacity:1;color:#38bdf8;">↓</div>`;
        } else if (isHead) {
            labelHTML = `<div style="position:absolute;top:-25px;font-size:10px;font-weight:bold;color:#fbbf24;">Head</div><div class="pointer" style="opacity:1;color:#fbbf24;">↓</div>`;
        }
        
        const displayVal = val === null ? '' : val;
        
        return `
        <div style="position:relative;display:flex;flex-direction:column;align-items:center;margin:0 4px;">
            ${labelHTML}
            <div class="array-node" style="margin-top:10px; ${!isValid ? 'opacity:0.4; border-style:dashed; color:var(--text-dim);' : 'border-color:var(--accent); color:var(--text);'} ${isTarget ? 'border-color:#38bdf8;box-shadow:0 0 10px #38bdf880;' : ''}">
              <span>${displayVal}</span>
            </div>
            <div class="node-index" style="bottom:-20px;">${idx}</div>
        </div>`;
    }).join('');

    const resultBox = s.result !== null
      ? `<div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:color-mix(in srgb, #34d399 15%, transparent);border:1px solid #34d399;color:#34d399;font-weight:bold;text-align:center;">Returned: ${s.result}</div>`
      : '';

    container.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:8px;">
        ${opsList}
      </div>
      <div class="glass-panel" style="display:flex;flex-direction:column;align-items:center;padding:40px 20px;">
        <div style="display:flex;justify-content:center;align-items:center;margin-bottom:30px;min-height:80px;">
            ${arrHTML}
        </div>
        <div style="display:flex;gap:20px;font-family:var(--mono);font-size:14px;color:var(--text);background:var(--bg);padding:10px 20px;border-radius:8px;border:1px solid var(--border);">
            <div><span style="color:var(--text-dim)">Capacity:</span> ${s.cap}</div>
            <div><span style="color:var(--text-dim)">Size:</span> <span style="color:#fbbf24;font-weight:bold">${s.size}</span></div>
            <div><span style="color:var(--text-dim)">Head Index:</span> ${s.head}</div>
        </div>
        ${resultBox}
      </div>
    `;
  }
});

defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: 'Design Circular Deque', short: 'Circular Deque',
  idea: 'Extends Circular Queue. <code>head</code> can move backward via <code>(head - 1) % cap</code>. In Python this correctly wraps around to <code>cap - 1</code> if head was 0, since Python modulo retains the divisor\'s sign. <code>deleteLast</code> simply decrements <code>size</code> without moving any index, causing the rear element to instantly fall out of the valid logical window.',
  complexity: 'Time O(1) · Space O(k)',
  input: 'init 3, insertLast 1, insertLast 2, insertFront 3, insertFront 4, getRear, isFull, deleteLast, insertFront 4, getFront', 
  hint: 'comma-separated ops (init k, insertFront v, insertLast v, deleteFront, deleteLast, getFront, getRear, isEmpty, isFull)',
  code: [
    'class MyCircularDeque:',
    '    def __init__(self, k: int):',
    '        self.buf = [0] * k',
    '        self.cap = k',
    '        self.head = 0',
    '        self.size = 0',
    '',
    '    def insertFront(self, value: int) -> bool:',
    '        if self.size == self.cap: return False',
    '        self.head = (self.head - 1) % self.cap',
    '        self.buf[self.head] = value',
    '        self.size += 1',
    '        return True',
    '',
    '    def insertLast(self, value: int) -> bool:',
    '        if self.size == self.cap: return False',
    '        tail = (self.head + self.size) % self.cap',
    '        self.buf[tail] = value',
    '        self.size += 1',
    '        return True',
    '',
    '    def deleteFront(self) -> bool:',
    '        if self.size == 0: return False',
    '        self.head = (self.head + 1) % self.cap',
    '        self.size -= 1',
    '        return True',
    '',
    '    def deleteLast(self) -> bool:',
    '        if self.size == 0: return False',
    '        self.size -= 1',
    '        return True',
    '',
    '    def getFront(self) -> int:',
    '        if self.size == 0: return -1',
    '        return self.buf[self.head]',
    '',
    '    def getRear(self) -> int:',
    '        if self.size == 0: return -1',
    '        return self.buf[(self.head + self.size - 1) % self.cap]',
    '',
    '    def isEmpty(self) -> bool:',
    '        return self.size == 0',
    '',
    '    def isFull(self) -> bool:',
    '        return self.size == self.cap'
  ],
  parse(s) {
    const ops = s.split(',').map(x => x.trim()).filter(Boolean);
    if (!ops.length) throw new Error('Enter operations');
    if (!ops[0].toLowerCase().startsWith('init')) {
        throw new Error('First operation must be "init k"');
    }
    return { ops };
  },
  buildStates({ ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    let cap = 0, head = 0, size = 0, buf = [];

    const initMatch = ops[0].match(/init\s+(\d+)/i);
    if (initMatch) {
      cap = parseInt(initMatch[1]);
      buf = Array(cap).fill(null);
    } else {
      cap = 3; 
      buf = Array(cap).fill(null);
    }

    domPushState(seq, {
      kind: 'init', line: 2,
      ops, opIdx: 0, buf: [...buf], cap, head, size, result: null, targetIdx: -1,
      explTitle: 'Initialization',
      explText: `Created circular deque with capacity ${cap}.`,
      pause: true
    }, ctx);

    for (let i = 1; i < ops.length; i++) {
      const parts = ops[i].split(/\s+/);
      const cmd = parts[0].toLowerCase();
      let result = null;

      if (cmd === 'insertfront') {
        const val = parseInt(parts[1]);
        if (size === cap) {
          result = false;
          domPushState(seq, {
            kind: 'insertFront', line: 8, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `insertFront(${val})`, explText: `Deque is full (size == cap). Cannot insert.`, pause: true
          }, ctx);
        } else {
          head = (head - 1 + cap) % cap;
          domPushState(seq, {
            kind: 'insertFront-step', line: 9, ops, opIdx: i, buf: [...buf], cap, head, size, result: null, targetIdx: head,
            explTitle: `insertFront(${val})`, explText: `Decremented head to (head - 1) % cap = ${head}. Note how we wrap around backward if needed.`, pause: false
          }, ctx);
          
          buf[head] = val;
          size += 1;
          result = true;
          domPushState(seq, {
            kind: 'insertFront-done', line: 12, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: head,
            explTitle: `insertFront(${val})`, explText: `Inserted ${val} at new head (${head}). Incremented size to ${size}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'insertlast') {
        const val = parseInt(parts[1]);
        if (size === cap) {
          result = false;
          domPushState(seq, {
            kind: 'insertLast', line: 15, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `insertLast(${val})`, explText: `Deque is full (size == cap). Cannot insert.`, pause: true
          }, ctx);
        } else {
          const tail = (head + size) % cap;
          domPushState(seq, {
            kind: 'insertLast-step', line: 16, ops, opIdx: i, buf: [...buf], cap, head, size, result: null, targetIdx: tail,
            explTitle: `insertLast(${val})`, explText: `Calculate tail = (head + size) % cap = (${head} + ${size}) % ${cap} = ${tail}.`, pause: false
          }, ctx);
          
          buf[tail] = val;
          size += 1;
          result = true;
          domPushState(seq, {
            kind: 'insertLast-done', line: 19, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: tail,
            explTitle: `insertLast(${val})`, explText: `Inserted ${val} at index ${tail}. Incremented size to ${size}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'deletefront') {
        if (size === 0) {
          result = false;
          domPushState(seq, {
            kind: 'deleteFront', line: 22, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deleteFront()`, explText: `Deque is empty (size == 0). Cannot delete.`, pause: true
          }, ctx);
        } else {
          head = (head + 1) % cap;
          size -= 1;
          result = true;
          domPushState(seq, {
            kind: 'deleteFront-done', line: 25, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deleteFront()`, explText: `Moved head forward to ${head} and decremented size to ${size}. Old value is now logically deleted.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'deletelast') {
        if (size === 0) {
          result = false;
          domPushState(seq, {
            kind: 'deleteLast', line: 28, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deleteLast()`, explText: `Deque is empty (size == 0). Cannot delete.`, pause: true
          }, ctx);
        } else {
          size -= 1;
          result = true;
          domPushState(seq, {
            kind: 'deleteLast-done', line: 31, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `deleteLast()`, explText: `Just decremented size to ${size}. The rear element instantly falls out of the valid logical window.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'getfront') {
        if (size === 0) {
          result = -1;
          domPushState(seq, {
            kind: 'getFront', line: 34, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `getFront()`, explText: `Deque is empty, return -1.`, pause: true
          }, ctx);
        } else {
          result = buf[head];
          domPushState(seq, {
            kind: 'getFront', line: 35, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: head,
            explTitle: `getFront()`, explText: `Return element at head (${head}), which is ${result}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'getrear') {
        if (size === 0) {
          result = -1;
          domPushState(seq, {
            kind: 'getRear', line: 38, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
            explTitle: `getRear()`, explText: `Deque is empty, return -1.`, pause: true
          }, ctx);
        } else {
          const tail = (head + size - 1) % cap;
          result = buf[tail];
          domPushState(seq, {
            kind: 'getRear', line: 39, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: tail,
            explTitle: `getRear()`, explText: `Rear is at (head + size - 1) % cap = (${head} + ${size} - 1) % ${cap} = ${tail}. Returning ${result}.`, pause: true
          }, ctx);
        }
      } else if (cmd === 'isempty') {
        result = size === 0;
        domPushState(seq, {
          kind: 'isempty', line: 42, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
          explTitle: `isEmpty()`, explText: `Is size == 0? ${result}.`, pause: true
        }, ctx);
      } else if (cmd === 'isfull') {
        result = size === cap;
        domPushState(seq, {
          kind: 'isfull', line: 45, ops, opIdx: i, buf: [...buf], cap, head, size, result, targetIdx: -1,
          explTitle: `isFull()`, explText: `Is size == cap (${cap})? ${result}.`, pause: true
        }, ctx);
      }
    }
    
    domPushState(seq, {
      kind: 'done', line: -1, ops, opIdx: ops.length, buf: [...buf], cap, head, size, result: null, targetIdx: -1,
      explTitle: 'Finished', explText: 'All operations complete.', pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s) {
    const opsList = s.ops.map((op, i) => {
      const isCur = s.opIdx === i;
      const isPast = s.opIdx > i;
      return `<div style="padding:4px 8px;border-radius:4px;font-family:var(--mono);font-size:12px;${isCur ? 'background:var(--accent);color:var(--accent-ink);font-weight:bold;' : isPast ? 'color:var(--text-dim);text-decoration:line-through;' : 'color:var(--text);'}">${op}</div>`;
    }).join('');

    const validIndices = new Set();
    for(let k = 0; k < s.size; k++) {
        validIndices.add((s.head + k) % s.cap);
    }

    const arrHTML = s.buf.map((val, idx) => {
        const isHead = idx === s.head && s.size > 0;
        const isTarget = idx === s.targetIdx;
        const isValid = validIndices.has(idx);
        
        let labelHTML = '';
        if (isTarget) {
            labelHTML = `<div style="position:absolute;top:-25px;font-size:10px;font-weight:bold;color:#38bdf8;">Target</div><div class="pointer" style="opacity:1;color:#38bdf8;">↓</div>`;
        } else if (isHead) {
            labelHTML = `<div style="position:absolute;top:-25px;font-size:10px;font-weight:bold;color:#fbbf24;">Head</div><div class="pointer" style="opacity:1;color:#fbbf24;">↓</div>`;
        }
        
        const displayVal = val === null ? '' : val;
        
        return `
        <div style="position:relative;display:flex;flex-direction:column;align-items:center;margin:0 4px;">
            ${labelHTML}
            <div class="array-node" style="margin-top:10px; ${!isValid ? 'opacity:0.4; border-style:dashed; color:var(--text-dim);' : 'border-color:var(--accent); color:var(--text);'} ${isTarget ? 'border-color:#38bdf8;box-shadow:0 0 10px #38bdf880;' : ''}">
              <span>${displayVal}</span>
            </div>
            <div class="node-index" style="bottom:-20px;">${idx}</div>
        </div>`;
    }).join('');

    const resultBox = s.result !== null
      ? `<div style="margin-top:16px;padding:8px 16px;border-radius:8px;background:color-mix(in srgb, #34d399 15%, transparent);border:1px solid #34d399;color:#34d399;font-weight:bold;text-align:center;">Returned: ${s.result}</div>`
      : '';

    container.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:8px;">
        ${opsList}
      </div>
      <div class="glass-panel" style="display:flex;flex-direction:column;align-items:center;padding:40px 20px;">
        <div style="display:flex;justify-content:center;align-items:center;margin-bottom:30px;min-height:80px;">
            ${arrHTML}
        </div>
        <div style="display:flex;gap:20px;font-family:var(--mono);font-size:14px;color:var(--text);background:var(--bg);padding:10px 20px;border-radius:8px;border:1px solid var(--border);">
            <div><span style="color:var(--text-dim)">Capacity:</span> ${s.cap}</div>
            <div><span style="color:var(--text-dim)">Size:</span> <span style="color:#fbbf24;font-weight:bold">${s.size}</span></div>
            <div><span style="color:var(--text-dim)">Head Index:</span> ${s.head}</div>
        </div>
        ${resultBox}
      </div>
    `;
  }
});
/* ============================================================================
   07 · Shortest Subarray with Sum at Least K (DOM)
   ========================================================================= */

defineAlgoDom('07_queue_deque', {
  type: 'dom',
  title: 'Shortest Subarray with Sum at Least K', short: 'Shortest Subarray ≥ K',
  idea: 'Use a prefix sum array and a <b>monotonic deque</b>. For each prefix <code>p</code> at index <code>i</code>, we want the largest previous index <code>l</code> where <code>p - prefix[l] ≥ k</code>. The deque stores potential left bounds. We pop from the front if they satisfy the sum condition (they can never form a shorter valid subarray later), and pop from the back if they are dominated (larger prefix but earlier index).',
  complexity: 'Time O(n) · Space O(n)',
  input: '84, -37, 32, 40, 95 ; 167', hint: 'comma-separated array ; k',
  code: [
    'def shortestSubarray(nums, k):',
    '    n = len(nums)',
    '    prefix = [0] * (n + 1)',
    '    for i in range(n):',
    '        prefix[i + 1] = prefix[i] + nums[i]',
    '',
    '    dq = collections.deque()',
    '    best = n + 1',
    '    for i, p in enumerate(prefix):',
    '        while dq and p - prefix[dq[0]] >= k:',
    '            best = min(best, i - dq.popleft())',
    '        while dq and prefix[dq[-1]] >= p:',
    '            dq.pop()',
    '        dq.append(i)',
    '    return best if best <= n else -1'
  ],
  parse(s) {
    const [arrStr, kStr] = avParts(s);
    if (!arrStr || kStr === undefined) throw new Error('Provide array and k separated by semicolon (e.g., "84, -37, 32, 40, 95 ; 167")');
    const nums = avNums(arrStr, 15, 'array');
    const k = avNum(kStr, 'k');
    return { nums, k };
  },
  buildStates({ nums, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = nums.length;
    const prefix = [0];
    for (let i = 0; i < n; i++) {
      prefix.push(prefix[i] + nums[i]);
    }
    const dq = [];
    let best = n + 1;

    domPushState(seq, {
      kind: 'init', line: 7, color: 'default',
      nums, k, prefix, dq: [...dq], best, i: -1, p: null, frontPop: -1, backPop: -1,
      explTitle: 'Initialization',
      explText: `Computed prefix sums. Length is ${n+1}. Initialize empty deque. best = ∞.`,
      pause: true
    }, ctx);

    for (let i = 0; i <= n; i++) {
      const p = prefix[i];
      domPushState(seq, {
        kind: 'visit', line: 9, color: 'default',
        nums, k, prefix, dq: [...dq], best, i, p, frontPop: -1, backPop: -1,
        explTitle: `Visit Prefix Index ${i}`,
        explText: `prefix[${i}] = ${p}.`
      }, ctx);

      // FRONT pop
      while (dq.length > 0 && p - prefix[dq[0]] >= k) {
        const popped = dq.shift(); // popleft
        const curLen = i - popped;
        const oldBest = best;
        if (curLen < best) best = curLen;
        domPushState(seq, {
          kind: 'front-pop', line: 11, color: 'emerald',
          nums, k, prefix, dq: [...dq], best, i, p, frontPop: popped, backPop: -1,
          explTitle: 'Valid Subarray Found!',
          explText: `${p} - prefix[${popped}] = ${p - prefix[popped]} ≥ ${k}. ` +
                    `Subarray length is ${i} - ${popped} = ${curLen}. ` +
                    (curLen < oldBest ? `New shortest length is ${best}!` : `Length ${curLen} is not shorter than ${oldBest}.`) +
                    ` Index ${popped} is permanently discarded from the deque front.`
        }, ctx);
      }

      // BACK pop
      while (dq.length > 0 && prefix[dq[dq.length - 1]] >= p) {
        const popped = dq.pop();
        domPushState(seq, {
          kind: 'back-pop', line: 13, color: 'amber',
          nums, k, prefix, dq: [...dq], best, i, p, frontPop: -1, backPop: popped,
          explTitle: 'Maintain Monotonicity',
          explText: `prefix[${popped}] = ${prefix[popped]} ≥ current prefix ${p}. ` +
                    `Index ${popped} is dominated by index ${i} (it's older AND has a larger/equal prefix). Pop it from the back.`
        }, ctx);
      }

      dq.push(i);
      domPushState(seq, {
        kind: 'push', line: 14, color: 'blue',
        nums, k, prefix, dq: [...dq], best, i, p, frontPop: -1, backPop: -1,
        explTitle: 'Push Index',
        explText: `Push index ${i} to deque.`
      }, ctx);
    }

    const ans = best <= n ? best : -1;
    domPushState(seq, {
      kind: 'done', line: 15, color: ans !== -1 ? 'emerald' : 'amber',
      nums, k, prefix, dq: [...dq], best: ans, i: n, p: prefix[n], frontPop: -1, backPop: -1,
      explTitle: 'Complete',
      explText: ans !== -1 ? `Shortest subarray length is ${ans}.` : `No valid subarray found. Return -1.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s) {
    const numsHTML = s.nums.map((val, idx) => {
        const inSubarray = s.frontPop >= 0 && idx >= s.frontPop && idx < s.i;
        return `
            <div class="array-node ${inSubarray ? 'active-k merged' : ''}" style="min-width:32px;">
                ${val}
                <div class="node-index">${idx}</div>
            </div>`;
    }).join('');

    const prefixHTML = s.prefix.map((p, idx) => {
        const isCur = idx === s.i;
        const inDq = s.dq.includes(idx);
        const isPoppedFront = s.frontPop === idx;
        const isPoppedBack = s.backPop === idx;

        let borderColor = 'var(--border)';
        let bgColor = 'transparent';
        let color = 'var(--text)';

        if (isCur) {
            borderColor = 'var(--accent)';
            bgColor = 'color-mix(in srgb, var(--accent) 15%, transparent)';
        } else if (isPoppedFront) {
            borderColor = '#34d399';
            bgColor = 'color-mix(in srgb, #34d399 15%, transparent)';
            color = '#34d399';
        } else if (isPoppedBack) {
            borderColor = '#fbbf24';
            bgColor = 'color-mix(in srgb, #fbbf24 15%, transparent)';
            color = '#fbbf24';
        } else if (inDq) {
            borderColor = '#38bdf8';
            bgColor = 'color-mix(in srgb, #38bdf8 15%, transparent)';
            color = '#38bdf8';
        }

        let ptr = '';
        if (isCur) ptr = `<div class="pointer" style="opacity:1;color:var(--accent);">↓ i</div>`;
        else if (isPoppedFront) ptr = `<div class="pointer" style="opacity:1;color:#34d399;font-size:10px;bottom:-18px;top:auto;">front pop</div>`;
        else if (isPoppedBack) ptr = `<div class="pointer" style="opacity:1;color:#fbbf24;font-size:10px;bottom:-18px;top:auto;">back pop</div>`;
        
        return `
            <div class="array-node" style="min-width:32px; border-color:${borderColor}; background:${bgColor}; color:${color}; position:relative; margin-bottom:12px;">
                ${ptr}
                ${p}
                <div class="node-index">${idx}</div>
            </div>`;
    }).join('');

    const dqHTML = s.dq.map(idx => {
        return `
            <div class="array-node" style="min-width:32px; border-color:#38bdf8; background:color-mix(in srgb, #38bdf8 15%, transparent); color:#38bdf8;">
                ${idx}
                <div style="font-size:10px; color:var(--text-dim); margin-top:2px;">(p=${s.prefix[idx]})</div>
            </div>`;
    }).join('');

    const statsHTML = `
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;align-items:center;">
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">k =</span> <b style="color:var(--accent);">${s.k}</b>
        </div>
        <div style="display:inline-flex;align-items:baseline;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--border);font-size:12px;font-family:var(--mono);">
          <span style="color:var(--text-dim);">best =</span> <b style="color:#34d399;">${s.best > s.nums.length ? '∞' : s.best}</b>
        </div>
      </div>`;

    container.innerHTML = `
      <div class="glass-panel arrays-container" style="margin-bottom:8px;">
        <div class="panel-heading" style="color:var(--text);">nums</div>
        <div class="array-track">${numsHTML}</div>
      </div>
      <div class="glass-panel arrays-container" style="margin-bottom:8px;">
        <div class="panel-heading" style="color:var(--accent);">prefix sums</div>
        <div class="array-track" style="padding-bottom:16px;">${prefixHTML}</div>
      </div>
      <div class="glass-panel arrays-container">
        <div class="panel-heading" style="color:#38bdf8;">deque (indices into prefix array)</div>
        <div class="array-track" style="min-height:48px; align-items:center;">
            ${s.dq.length === 0 ? '<div style="color:var(--text-dim);font-size:12px;padding:8px;">(empty)</div>' : '<div style="color:var(--text-dim);font-size:12px;padding:8px;font-family:var(--mono);">front →</div>' + dqHTML + '<div style="color:var(--text-dim);font-size:12px;padding:8px;font-family:var(--mono);">← back</div>'}
        </div>
        ${statsHTML}
      </div>`;
  }
});
