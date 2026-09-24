/* ============================================================================
   Visualizations for 08_linked_list (Part 3 - Advanced Pointers & Maths)
   ========================================================================= */
"use strict";

/* ================================ 08 · Palindrome Linked List ============ */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Palindrome Linked List', short: 'Palindrome',
  idea: 'Use fast and slow pointers to find the middle. Reverse the second half of the list, then compare the first and second halves.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 2, 1', hint: 'list elements',
  code: [
    'def isPalindrome(head):',
    '    slow = fast = head',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '    prev = None',
    '    while slow:',
    '        nxt = slow.next',
    '        slow.next = prev',
    '        prev = slow',
    '        slow = nxt',
    '    left, right = head, prev',
    '    while right:',
    '        if left.val != right.val: return False',
    '        left = left.next',
    '        right = right.next',
    '    return True'
  ],
  parse(s) {
    return { list: avNums(s, 15, 'list') };
  },
  buildStates({ list }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let nodes = list.map((val, i) => ({ id: `node_${i}`, val, next: i + 1 < list.length ? i + 1 : null }));
    
    let slow = 0, fast = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, left: null, right: null,
      explTitle: 'Find Middle',
      explText: `Initialize slow and fast pointers to the head to find the middle.`,
      pause: true
    }, ctx);
    
    while (fast < nodes.length && nodes[fast].next !== null) {
      slow = nodes[slow].next;
      fast = nodes[nodes[fast].next].next;
      if (fast === null) fast = nodes.length; // logical end
      
      domPushState(seq, {
        kind: 'mid', line: 4, color: 'blue',
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, left: null, right: null,
        explTitle: 'Advance Pointers',
        explText: `Advance slow by 1 step, fast by 2 steps.`
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'reverse-init', line: 6, color: 'default',
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, left: null, right: null, prev: null, curr: slow,
      explTitle: 'Reverse Second Half',
      explText: `Slow is at the middle. Now reverse the second half of the list starting from slow.`,
      pause: true
    }, ctx);
    
    let prev = null;
    let curr = slow;
    
    while (curr !== null) {
      let nxt = nodes[curr].next;
      nodes[curr].next = prev;
      prev = curr;
      curr = nxt;
      
      domPushState(seq, {
        kind: 'reverse-step', line: 9, color: 'amber',
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, left: null, right: null, prev, curr,
        explTitle: 'Reverse Pointers',
        explText: `Reverse the next pointer for node with value ${nodes[prev].val}.`
      }, ctx);
    }
    
    let left = 0;
    let right = prev;
    
    domPushState(seq, {
      kind: 'compare-init', line: 12, color: 'default',
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, left, right,
      explTitle: 'Compare Halves',
      explText: `Set left to head and right to the head of the reversed second half.`,
      pause: true
    }, ctx);
    
    let isPal = true;
    while (right !== null) {
      domPushState(seq, {
        kind: 'compare-step', line: 14, color: 'blue',
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, left, right,
        explTitle: 'Compare Values',
        explText: `Compare left.val (${nodes[left].val}) with right.val (${nodes[right].val}).`
      }, ctx);
      
      if (nodes[left].val !== nodes[right].val) {
        isPal = false;
        domPushState(seq, {
          kind: 'false', line: 14, color: 'red',
          nodes: JSON.parse(JSON.stringify(nodes)),
          slow, fast, left, right,
          explTitle: 'Mismatch Found',
          explText: `Values do not match. It is not a palindrome.`,
          pause: true
        }, ctx);
        break;
      }
      
      left = nodes[left].next;
      right = nodes[right].next;
    }
    
    if (isPal) {
      domPushState(seq, {
        kind: 'true', line: 17, color: 'emerald',
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, left, right,
        explTitle: 'Palindrome Validated',
        explText: `All values matched. The list is a palindrome!`,
        pause: true
      }, ctx);
    }
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (nodes) => {
        let html = '';
        
        let visualArray = [];
        for(let i = 0; i < nodes.length; i++) {
           visualArray.push({idx: i, node: nodes[i]});
        }
        
        visualArray.forEach((item) => {
            let cls = '';
            let ptrs = [];
            
            if (s.kind === 'mid' || s.kind === 'init') {
                if (item.idx === s.slow) ptrs.push(`<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>`);
                if (item.idx === s.fast) ptrs.push(`<div class="pointer" style="color:#f59e0b; top:-40px;">↓ fast</div>`);
                if (item.idx === s.slow || item.idx === s.fast) cls = 'active-1';
            }
            
            if (s.kind.startsWith('reverse')) {
                if (item.idx === s.prev) ptrs.push(`<div class="pointer" style="color:#3b82f6; top:-25px;">↓ prev</div>`);
                if (item.idx === s.curr) ptrs.push(`<div class="pointer" style="color:#f59e0b; top:-40px;">↓ curr</div>`);
                if (item.idx === s.prev || item.idx === s.curr) cls = 'active-k';
            }
            
            if (s.kind.startsWith('compare') || s.kind === 'true' || s.kind === 'false') {
                if (item.idx === s.left) ptrs.push(`<div class="pointer" style="color:#10b981; top:-25px;">↓ left</div>`);
                if (item.idx === s.right) ptrs.push(`<div class="pointer" style="color:#8b5cf6; top:-40px;">↓ right</div>`);
                if (item.idx === s.left || item.idx === s.right) cls = 'active-1';
            }
            
            let nextArrow = '→';
            if (s.kind.startsWith('reverse') || s.kind.startsWith('compare') || s.kind === 'true' || s.kind === 'false') {
                if (item.idx >= s.slow) {
                    if (item.node.next === null) nextArrow = '∅';
                    else if (item.node.next < item.idx) nextArrow = '←';
                }
            }
            if (item.idx === nodes.length - 1 && nextArrow === '→') nextArrow = '∅';
            
            html += `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px;">
                ${ptrs.join('')}
                ${item.node.val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">${nextArrow}</div>
    </div>`;
        });
        
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Linked List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.nodes)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Add Two Numbers =================== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Add Two Numbers', short: 'Add Two Numbers',
  idea: 'Iterate through both lists, keeping track of a <code>carry</code>. Sum digits at each step and append <code>sum % 10</code> to a new dummy list.',
  complexity: 'Time O(max(n,m)) · Space O(max(n,m))',
  input: '2, 4, 3 ; 5, 6, 4', hint: 'list1 ; list2',
  code: [
    'def addTwoNumbers(l1, l2):',
    '    dummy = ListNode()',
    '    curr = dummy',
    '    carry = 0',
    '    while l1 or l2 or carry:',
    '        v1 = l1.val if l1 else 0',
    '        v2 = l2.val if l2 else 0',
    '        total = v1 + v2 + carry',
    '        carry, digit = divmod(total, 10)',
    '        curr.next = ListNode(digit)',
    '        curr = curr.next',
    '        if l1: l1 = l1.next',
    '        if l2: l2 = l2.next',
    '    return dummy.next'
  ],
  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Enter list1 and list2 separated by ;');
    const l1 = avNums(parts[0], 10, 'list1');
    const l2 = avNums(parts[1], 10, 'list2');
    return { l1, l2 };
  },
  buildStates({ l1, l2 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let p1 = 0, p2 = 0;
    let carry = 0;
    let merged = [];
    
    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      l1, l2, p1, p2, carry, merged: [...merged],
      explTitle: 'Initialization',
      explText: 'Create a dummy head and set carry to 0.',
      pause: true
    }, ctx);
    
    while (p1 < l1.length || p2 < l2.length || carry > 0) {
      let v1 = p1 < l1.length ? l1[p1] : 0;
      let v2 = p2 < l2.length ? l2[p2] : 0;
      
      domPushState(seq, {
        kind: 'extract', line: 6, color: 'blue',
        l1, l2, p1, p2, carry, merged: [...merged], v1, v2,
        explTitle: 'Extract Digits',
        explText: `Extract v1 = ${v1} and v2 = ${v2}.`
      }, ctx);
      
      let total = v1 + v2 + carry;
      let digit = total % 10;
      carry = Math.floor(total / 10);
      
      domPushState(seq, {
        kind: 'sum', line: 9, color: 'amber',
        l1, l2, p1, p2, carry, merged: [...merged], v1, v2, total, digit,
        explTitle: 'Compute Sum & Carry',
        explText: `total = ${v1} + ${v2} + ${total - v1 - v2} = ${total}. Digit = ${digit}, Carry = ${carry}.`
      }, ctx);
      
      merged.push(digit);
      
      domPushState(seq, {
        kind: 'append', line: 10, color: 'emerald',
        l1, l2, p1, p2, carry, merged: [...merged],
        explTitle: 'Append Digit',
        explText: `Append ${digit} to the merged list.`
      }, ctx);
      
      if (p1 < l1.length) p1++;
      if (p2 < l2.length) p2++;
      
      domPushState(seq, {
        kind: 'advance', line: 12, color: 'default',
        l1, l2, p1, p2, carry, merged: [...merged],
        explTitle: 'Advance Pointers',
        explText: `Advance l1 and l2 pointers.`,
        pause: true
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'done', line: 14, color: 'emerald',
      l1, l2, p1, p2, carry, merged: [...merged],
      explTitle: 'Complete',
      explText: `Return dummy.next as the head of the new list!`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (list, p, label) => {
        if(list.length === 0) return `<div class="array-node merged">∅</div>`;
        return list.map((val, idx) => {
            let cls = '';
            let ptrHTML = '';
            if (idx === p) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:var(--text-bright)">↓ ${label}</div>`;
            } else if (idx < p) {
                cls = 'merged';
            }
            return `
            <div class="array-node ${cls}" style="border-radius:50%; width:45px; height:45px; margin-right:15px; ${idx < p ? 'opacity: 0.5' : ''}">
                ${ptrHTML}
                ${val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        }).join('') + `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
    };
    
    const getMergedHTML = (merged) => {
        if(merged.length === 0) return `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent;">→ ∅</div>`;
        let html = `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent; margin-right:15px;">→</div>`;
        html += merged.map((val, idx) => {
            let isTail = idx === merged.length - 1;
            let ptrHTML = isTail && s.kind !== 'done' ? `<div class="pointer" style="color:#3b82f6">↓ curr</div>` : '';
            return `
            <div class="array-node active-1" style="border-radius:50%; width:45px; height:45px; margin-right:15px; border-color:var(--emerald); color:var(--emerald);">
                ${ptrHTML}
                ${val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        }).join('');
        html += `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>l1</span>
                      <span style="color:var(--amber);">Carry: ${s.carry || 0}</span>
                  </div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.l1, s.p1, 'l1')}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">l2</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.l2, s.p2, 'l2')}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Merged Result</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px; justify-content:center; flex-wrap:wrap;">${getMergedHTML(s.merged)}</div>
              </div>
    </div>`;
  }
});
/* ================================ 08 · Reorder List ======================= */
defineAlgoDom("08_linked_list", {
  type: "dom",
  title: "Reorder List", short: "Reorder List",
  idea: "Find middle, reverse the second half, then merge the two halves alternately.",
  complexity: "Time O(n) · Space O(1)",
  input: "1, 2, 3, 4, 5", hint: "list elements",
  code: [
    "def reorderList(head):",
    "    slow = fast = head",
    "    while fast and fast.next:",
    "        slow = slow.next",
    "        fast = fast.next.next",
    "    second = slow.next",
    "    slow.next = None",
    "    prev = None",
    "    while second:",
    "        nxt = second.next",
    "        second.next = prev",
    "        prev = second",
    "        second = nxt",
    "    first, second = head, prev",
    "    while second:",
    "        tmp1, tmp2 = first.next, second.next",
    "        first.next = second",
    "        second.next = tmp1",
    "        first, second = tmp1, tmp2"
  ],
  parse(s) {
    return { list: avNums(s, 15, "list") };
  },
  buildStates({ list }) {
    const seq = [], ctx = { t: "Concept", x: "Ready to begin." };
    
    let nodes = list.map((val, i) => ({ id: "node_" + i, val, next: i + 1 < list.length ? i + 1 : null }));
    
    let slow = 0, fast = 0;
    
    domPushState(seq, {
      kind: "init", line: 2, color: "default",
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, first: null, second: null, prev: null,
      explTitle: "Find Middle",
      explText: "Initialize slow and fast pointers to the head."
    }, ctx);
    
    while (fast < nodes.length && nodes[fast].next !== null) {
      slow = nodes[slow].next;
      fast = nodes[nodes[fast].next].next;
      if (fast === null) fast = nodes.length;
      
      domPushState(seq, {
        kind: "mid", line: 4, color: "blue",
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, first: null, second: null, prev: null,
        explTitle: "Advance Pointers",
        explText: "Advance slow by 1 step, fast by 2 steps."
      }, ctx);
    }
    
    let second = nodes[slow].next;
    nodes[slow].next = null;
    
    domPushState(seq, {
      kind: "cut", line: 7, color: "default",
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, first: null, second, prev: null,
      explTitle: "Cut List",
      explText: "Cut the list into two halves.",
      pause: true
    }, ctx);
    
    let prev = null;
    while (second !== null) {
      let nxt = nodes[second].next;
      nodes[second].next = prev;
      prev = second;
      second = nxt;
      
      domPushState(seq, {
        kind: "reverse-step", line: 11, color: "amber",
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, first: null, second, prev,
        explTitle: "Reverse Second Half",
        explText: "Reverse pointers in the second half."
      }, ctx);
    }
    
    let first = 0;
    second = prev;
    
    domPushState(seq, {
      kind: "merge-init", line: 14, color: "default",
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, first, second, prev: null,
      explTitle: "Merge Halves",
      explText: "Set first to head, second to reversed half head.",
      pause: true
    }, ctx);
    
    while (second !== null) {
      let tmp1 = nodes[first].next;
      let tmp2 = nodes[second].next;
      
      nodes[first].next = second;
      nodes[second].next = tmp1;
      
      domPushState(seq, {
        kind: "merge-step", line: 17, color: "emerald",
        nodes: JSON.parse(JSON.stringify(nodes)),
        slow, fast, first, second, prev: null,
        explTitle: "Interleave Nodes",
        explText: "Link first to second, and second to first.next."
      }, ctx);
      
      first = tmp1;
      second = tmp2;
    }
    
    domPushState(seq, {
      kind: "done", line: 19, color: "emerald",
      nodes: JSON.parse(JSON.stringify(nodes)),
      slow, fast, first, second, prev: null,
      explTitle: "Complete",
      explText: "The list has been successfully reordered in-place!",
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (nodes) => {
        let html = "";
        
        let visualArray = [];
        for(let i = 0; i < nodes.length; i++) {
           visualArray.push({idx: i, node: nodes[i]});
        }
        
        visualArray.forEach((item) => {
            let cls = "";
            let ptrs = [];
            
            if (s.kind === "mid" || s.kind === "init") {
                if (item.idx === s.slow) ptrs.push('<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>');
                if (item.idx === s.fast) ptrs.push('<div class="pointer" style="color:#f59e0b; top:-40px;">↓ fast</div>');
                if (item.idx === s.slow || item.idx === s.fast) cls = "active-1";
            }
            
            if (s.kind.startsWith("reverse") || s.kind === "cut") {
                if (item.idx === s.prev) ptrs.push('<div class="pointer" style="color:#3b82f6; top:-25px;">↓ prev</div>');
                if (item.idx === s.second) ptrs.push('<div class="pointer" style="color:#f59e0b; top:-40px;">↓ second</div>');
                if (item.idx === s.prev || item.idx === s.second) cls = "active-k";
            }
            
            if (s.kind.startsWith("merge") || s.kind === "done") {
                if (item.idx === s.first) ptrs.push('<div class="pointer" style="color:#10b981; top:-25px;">↓ first</div>');
                if (item.idx === s.second) ptrs.push('<div class="pointer" style="color:#8b5cf6; top:-40px;">↓ second</div>');
                if (item.idx === s.first || item.idx === s.second) cls = "active-1";
            }
            
            let nextArrow = "→";
            if (s.kind.startsWith("reverse") || s.kind === "cut") {
                if (item.node.next === null) nextArrow = "∅";
                else if (item.node.next < item.idx) nextArrow = "←";
            } else if (s.kind.startsWith("merge") || s.kind === "done") {
                if (item.node.next === null) nextArrow = "∅";
                else if (Math.abs(item.node.next - item.idx) > 1) {
                     nextArrow = "→ <span style=\"font-size:12px\">(" + nodes[item.node.next].val + ")</span>";
                }
            }
            
            html += '<div class="array-node ' + cls + '" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px;">' +
                ptrs.join("") +
                item.node.val +
                '<div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">' + nextArrow + '</div>' +
            '</div>';
        });
        
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Linked List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.nodes)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Find the Duplicate Number ========== */
defineAlgoDom("08_linked_list", {
  type: "dom",
  title: "Find the Duplicate Number", short: "Find Duplicate",
  idea: "Use Floyd's Cycle Detection on an implicit linked list where each value points to the next index. <code>slow = nums[slow]</code> and <code>fast = nums[nums[fast]]</code>.",
  complexity: "Time O(n) · Space O(1)",
  input: "1, 3, 4, 2, 2", hint: "array elements",
  code: [
    "def findDuplicate(nums):",
    "    slow = fast = 0",
    "    while True:",
    "        slow = nums[slow]",
    "        fast = nums[nums[fast]]",
    "        if slow == fast:",
    "            break",
    "    slow2 = 0",
    "    while slow2 != slow:",
    "        slow2 = nums[slow2]",
    "        slow = nums[slow]",
    "    return slow2"
  ],
  parse(s) {
    return { nums: avNums(s, 15, "nums") };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: "Concept", x: "Ready to begin." };
    
    let slow = 0, fast = 0;
    
    domPushState(seq, {
      kind: "init", line: 2, color: "default",
      nums, slow, fast, slow2: null, phase: 1,
      explTitle: "Initialization",
      explText: "Initialize slow and fast pointers to index 0.",
      pause: true
    }, ctx);
    
    while (true) {
      slow = nums[slow];
      fast = nums[nums[fast]];
      
      domPushState(seq, {
        kind: "phase1", line: 4, color: "amber",
        nums, slow, fast, slow2: null, phase: 1,
        explTitle: "Phase 1: Find Cycle",
        explText: "Advance slow by 1 step (nums[slow]) and fast by 2 steps (nums[nums[fast]])."
      }, ctx);
      
      if (slow === fast) {
        domPushState(seq, {
          kind: "intersect", line: 6, color: "red",
          nums, slow, fast, slow2: null, phase: 1,
          explTitle: "Intersection Found",
          explText: "slow and fast met at index " + slow + "!",
          pause: true
        }, ctx);
        break;
      }
    }
    
    let slow2 = 0;
    domPushState(seq, {
      kind: "init2", line: 8, color: "default",
      nums, slow, fast, slow2, phase: 2,
      explTitle: "Phase 2: Find Entrance",
      explText: "Initialize slow2 to index 0. Advance both slow and slow2 by 1 step until they meet.",
      pause: true
    }, ctx);
    
    while (slow2 !== slow) {
      slow2 = nums[slow2];
      slow = nums[slow];
      
      domPushState(seq, {
        kind: "phase2", line: 10, color: "blue",
        nums, slow, fast, slow2, phase: 2,
        explTitle: "Advance Pointers",
        explText: "Advance slow and slow2 by 1 step each."
      }, ctx);
    }
    
    domPushState(seq, {
      kind: "done", line: 12, color: "emerald",
      nums, slow, fast, slow2, phase: 2,
      explTitle: "Complete",
      explText: "The entrance of the cycle is " + slow2 + ". This is the duplicate number!",
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (nums) => {
        let html = "";
        
        nums.forEach((val, idx) => {
            let cls = "";
            let ptrs = [];
            
            if (s.phase === 1) {
                if (idx === s.slow) ptrs.push('<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>');
                if (idx === s.fast) ptrs.push('<div class="pointer" style="color:#f59e0b; top:-40px;">↓ fast</div>');
                if (idx === s.slow || idx === s.fast) cls = "active-1";
            } else if (s.phase === 2) {
                if (idx === s.slow) ptrs.push('<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>');
                if (idx === s.slow2) ptrs.push('<div class="pointer" style="color:#3b82f6; top:-40px;">↓ slow2</div>');
                if (idx === s.slow || idx === s.slow2) cls = "active-k";
            }
            
            html += '<div class="array-node ' + cls + '" style="position:relative; margin-right:5px; width:45px; height:45px; flex-shrink:0;">' +
                '<div style="position:absolute; top:-60px; font-size:12px; color:var(--text-dim);">idx ' + idx + '</div>' +
                ptrs.join("") +
                val +
            '</div>';
        });
        
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Implicit Linked List (Array)</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:60px; justify-content:center;">${getListHTML(s.nums)}</div>
              </div>
    </div>`;
  }
});
