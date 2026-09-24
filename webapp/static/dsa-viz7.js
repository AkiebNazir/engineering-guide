/* ============================================================================
   Visualizations for 08_linked_list
   ========================================================================= */
"use strict";

/* ================================ 08 · Merge Two Sorted Lists (DOM) ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Merge Two Sorted Lists', short: 'Merge 2 Lists',
  idea: 'Use a dummy head and a tail pointer. Compare nodes from both lists and append the smaller one to the merged list.',
  complexity: 'Time O(n+m) · Space O(1)',
  input: '1, 2, 4 ; 1, 3, 4', hint: 'list1 ; list2',
  code: [
    'def mergeTwoLists(list1, list2):',
    '    dummy = ListNode()',
    '    tail = dummy',
    '    while list1 and list2:',
    '        if list1.val <= list2.val:',
    '            tail.next = list1',
    '            list1 = list1.next',
    '        else:',
    '            tail.next = list2',
    '            list2 = list2.next',
    '        tail = tail.next',
    '    tail.next = list1 if list1 else list2',
    '    return dummy.next'
  ],
  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Enter two comma-separated lists separated by ;');
    const l1 = avNums(parts[0], 10, 'list1');
    const l2 = avNums(parts[1], 10, 'list2');
    return { l1, l2 };
  },
  buildStates({ l1, l2 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    // We will simulate the pointers
    let p1 = 0, p2 = 0;
    let merged = [];
    
    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      l1, l2, p1, p2, merged: [...merged],
      explTitle: 'Initialization',
      explText: 'Create a dummy head and a tail pointer to track the merged list.',
      pause: true
    }, ctx);
    
    while (p1 < l1.length && p2 < l2.length) {
      domPushState(seq, {
        kind: 'loop', line: 4, color: 'blue',
        l1, l2, p1, p2, merged: [...merged],
        explTitle: 'Loop Check',
        explText: `Check if both list1 (val=${l1[p1]}) and list2 (val=${l2[p2]}) have nodes left.`
      }, ctx);
      
      domPushState(seq, {
        kind: 'compare', line: 5, color: 'default',
        l1, l2, p1, p2, merged: [...merged],
        explTitle: 'Compare Nodes',
        explText: `Is list1.val (${l1[p1]}) <= list2.val (${l2[p2]})?`
      }, ctx);
      
      if (l1[p1] <= l2[p2]) {
        merged.push({ val: l1[p1], src: 1 });
        domPushState(seq, {
          kind: 'append1', line: 6, color: 'emerald',
          l1, l2, p1, p2, merged: [...merged],
          explTitle: 'Append list1 node',
          explText: `Yes. Append list1's node to tail.`
        }, ctx);
        
        p1++;
        domPushState(seq, {
          kind: 'adv1', line: 7, color: 'emerald',
          l1, l2, p1, p2, merged: [...merged],
          explTitle: 'Advance list1',
          explText: `Advance list1 pointer.`
        }, ctx);
      } else {
        merged.push({ val: l2[p2], src: 2 });
        domPushState(seq, {
          kind: 'append2', line: 9, color: 'amber',
          l1, l2, p1, p2, merged: [...merged],
          explTitle: 'Append list2 node',
          explText: `No. Append list2's node to tail.`
        }, ctx);
        
        p2++;
        domPushState(seq, {
          kind: 'adv2', line: 10, color: 'amber',
          l1, l2, p1, p2, merged: [...merged],
          explTitle: 'Advance list2',
          explText: `Advance list2 pointer.`
        }, ctx);
      }
      
      domPushState(seq, {
        kind: 'advtail', line: 11, color: 'default',
        l1, l2, p1, p2, merged: [...merged],
        explTitle: 'Advance Tail',
        explText: `Advance tail pointer to the newly appended node.`,
        pause: true
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'remainder', line: 12, color: 'emerald',
      l1, l2, p1, p2, merged: [...merged],
      explTitle: 'Append Remainder',
      explText: `One of the lists is empty. Append the remainder of the other list directly.`
    }, ctx);
    
    while(p1 < l1.length) { merged.push({ val: l1[p1++], src: 1 }); }
    while(p2 < l2.length) { merged.push({ val: l2[p2++], src: 2 }); }
    
    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      l1, l2, p1, p2, merged: [...merged],
      explTitle: 'Complete',
      explText: `Return dummy.next as the head of the newly merged sorted list!`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (list, p, label, colorCls) => {
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
            <div class="array-node ${cls}" style="${idx < p ? 'opacity: 0.5' : ''}">
                ${ptrHTML}
                ${val}
                <div class="node-index" style="bottom:-20px; font-size:16px;">→</div>
    </div>`;
        }).join('') + `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
    };
    
    const getMergedHTML = (merged) => {
        if(merged.length === 0) return `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent;">→ ∅</div>`;
        let html = `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent;">→</div>`;
        html += merged.map((node, idx) => {
            let isTail = idx === merged.length - 1;
            let srcColor = node.src === 1 ? 'emerald' : 'amber';
            let ptrHTML = isTail && s.kind !== 'done' ? `<div class="pointer" style="color:#3b82f6">↓ tail</div>` : '';
            return `
            <div class="array-node" style="border-color:var(--${srcColor}); color:var(--${srcColor});">
                ${ptrHTML}
                ${node.val}
                <div class="node-index" style="bottom:-20px; font-size:16px; color:var(--text-dim);">→</div>
    </div>`;
        }).join('');
        html += `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">list1</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px;">${getListHTML(s.l1, s.p1, 'list1', 'emerald')}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">list2</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px;">${getListHTML(s.l2, s.p2, 'list2', 'amber')}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Merged List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px;">${getMergedHTML(s.merged)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Middle of the Linked List (DOM) ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Middle of the Linked List', short: 'Middle Node',
  idea: 'Use two pointers: slow and fast. Move slow by 1 step and fast by 2 steps. When fast reaches the end, slow will be at the middle.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 2, 3, 4, 5', hint: 'list elements',
  code: [
    'def middleNode(head):',
    '    slow = fast = head',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '    return slow'
  ],
  parse(s) {
    return { list: avNums(s, 15, 'list') };
  },
  buildStates({ list }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let slow = 0, fast = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      list, slow, fast,
      explTitle: 'Initialization',
      explText: 'Initialize slow and fast pointers to the head of the list.',
      pause: true
    }, ctx);
    
    while (fast < list.length && fast + 1 < list.length) {
      domPushState(seq, {
        kind: 'loop', line: 3, color: 'blue',
        list, slow, fast,
        explTitle: 'Loop Check',
        explText: `Check if fast pointer is valid and has a next node.`
      }, ctx);
      
      slow += 1;
      domPushState(seq, {
        kind: 'move-slow', line: 4, color: 'emerald',
        list, slow, fast,
        explTitle: 'Move Slow Pointer',
        explText: `Move slow pointer 1 step forward to index ${slow}.`
      }, ctx);
      
      fast += 2;
      domPushState(seq, {
        kind: 'move-fast', line: 5, color: 'amber',
        list, slow, fast,
        explTitle: 'Move Fast Pointer',
        explText: `Move fast pointer 2 steps forward to index ${fast}.`,
        pause: true
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'loop-end', line: 3, color: 'default',
      list, slow, fast,
      explTitle: 'Loop Terminates',
      explText: `Fast pointer reached the end of the list.`
    }, ctx);
    
    domPushState(seq, {
      kind: 'done', line: 6, color: 'emerald',
      list, slow, fast,
      explTitle: 'Complete',
      explText: `Return slow pointer which is at the middle node (value ${list[slow]}).`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (list, slow, fast) => {
        if(list.length === 0) return `<div class="array-node merged">∅</div>`;
        let html = list.map((val, idx) => {
            let cls = '';
            let ptrHTML = '';
            
            if (idx === slow && idx === fast) {
                cls = 'active-1';
                ptrHTML = `<div class="pointer" style="color:var(--text-bright); top:-35px;">↓ slow, fast</div>`;
            } else if (idx === slow) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>`;
            } else if (idx === fast) {
                cls = 'active-1';
                ptrHTML = `<div class="pointer" style="color:#f59e0b; top:-25px;">↓ fast</div>`;
            } else if (s.kind === 'done' && idx >= slow) {
                cls = 'active-k';
            }
            
            return `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px;">
                ${ptrHTML}
                ${val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        }).join('');
        
        let fastEndPtr = '';
        if (fast >= list.length) {
             fastEndPtr = `<div class="pointer" style="position:absolute; color:#f59e0b; top:-25px;">↓ fast</div>`;
        }
        
        html += `<div class="array-node merged" style="position:relative; border:none;background:transparent;">${fastEndPtr}∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Linked List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.list, s.slow, s.fast)}</div>
              </div>
    </div>`;
  }
});
