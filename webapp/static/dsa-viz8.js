/* ============================================================================
   Visualizations for 08_linked_list (Part 2 - Removals & Traversals)
   ========================================================================= */
"use strict";

/* ================================ 08 · Remove Linked List Elements ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Remove Linked List Elements', short: 'Remove Elements',
  idea: 'Use a dummy head. Keep a <code>curr</code> pointer and check <code>curr.next.val</code>. If it matches the target, rewire <code>curr.next = curr.next.next</code>, otherwise advance <code>curr</code>.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 6, 3, 4, 5, 6 ; 6', hint: 'list ; target',
  code: [
    'def removeElements(head, val):',
    '    dummy = ListNode(next=head)',
    '    curr = dummy',
    '    while curr.next:',
    '        if curr.next.val == val:',
    '            curr.next = curr.next.next',
    '        else:',
    '            curr = curr.next',
    '    return dummy.next'
  ],
  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Enter list and target separated by ;');
    const list = avNums(parts[0], 15, 'list');
    const target = avNum(parts[1], 'target');
    return { list, target };
  },
  buildStates({ list, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    // Convert array to a list of node objects
    let nodes = list.map((val, i) => ({ id: `node_${i}`, val, deleted: false }));
    let dummy = { id: 'dummy', val: 'dummy', deleted: false };
    
    let logicalList = [dummy, ...nodes];
    let currIdx = 0; // index in logicalList pointing to dummy
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx, target,
      explTitle: 'Initialization',
      explText: `Create a dummy head node. Set curr pointer to dummy. Target value is ${target}.`,
      pause: true
    }, ctx);
    
    domPushState(seq, {
      kind: 'init2', line: 3, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx, target,
      explTitle: 'Initialization',
      explText: `Set curr pointer to dummy.`
    }, ctx);
    
    while (currIdx + 1 < logicalList.length) {
      domPushState(seq, {
        kind: 'loop', line: 4, color: 'blue',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        currIdx, target,
        explTitle: 'Loop Check',
        explText: `Check if curr.next exists. It points to value ${logicalList[currIdx + 1].val}.`
      }, ctx);
      
      domPushState(seq, {
        kind: 'compare', line: 5, color: 'default',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        currIdx, target,
        explTitle: 'Compare Node',
        explText: `Is curr.next.val (${logicalList[currIdx + 1].val}) == target (${target})?`
      }, ctx);
      
      if (logicalList[currIdx + 1].val === target) {
        logicalList[currIdx + 1].deleted = true;
        let removedNode = logicalList.splice(currIdx + 1, 1)[0];
        
        domPushState(seq, {
          kind: 'remove', line: 6, color: 'red',
          logicalList: JSON.parse(JSON.stringify(logicalList)),
          currIdx, target,
          removedNode,
          explTitle: 'Remove Node',
          explText: `Yes. Rewire curr.next to curr.next.next, dropping the matching node.`
        }, ctx);
      } else {
        currIdx++;
        domPushState(seq, {
          kind: 'advance', line: 8, color: 'emerald',
          logicalList: JSON.parse(JSON.stringify(logicalList)),
          currIdx, target,
          explTitle: 'Advance Pointer',
          explText: `No. Advance curr to the next node.`
        }, ctx);
      }
    }
    
    domPushState(seq, {
      kind: 'loop-end', line: 4, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx, target,
      explTitle: 'Loop Terminates',
      explText: `curr.next is null. Reached the end of the list.`
    }, ctx);
    
    domPushState(seq, {
      kind: 'done', line: 9, color: 'emerald',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx, target,
      explTitle: 'Complete',
      explText: `Return dummy.next as the new head of the list.`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (logicalList, currIdx) => {
        let html = '';
        logicalList.forEach((node, idx) => {
            let cls = node.id === 'dummy' ? 'merged' : '';
            let style = node.id === 'dummy' ? 'background:var(--bg-elevated);' : '';
            let ptrHTML = '';
            
            if (idx === currIdx) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:var(--text-bright); top:-30px;">↓ curr</div>`;
            } else if (s.kind === 'done' && idx > 0) {
                cls = 'active-k';
            }
            
            if (s.kind === 'remove' && s.removedNode && idx === currIdx) {
               html += `
               <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; ${style}">
                   ${ptrHTML}
                   ${node.val}
                   <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
               
               html += `
               <div class="array-node deleted" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; opacity:0.3; border-color:var(--red); color:var(--red);">
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(45deg); width:100%; height:2px; background:var(--red);"></div>
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-45deg); width:100%; height:2px; background:var(--red);"></div>
                   ${s.removedNode.val}
               </div>`;
               return;
            }
            
            html += `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; ${style}">
                ${ptrHTML}
                ${node.val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        });
        
        html += `<div class="array-node merged" style="position:relative; border:none;background:transparent;">∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Target: <span style="color:var(--red); font-weight:bold;">${s.target}</span></div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.logicalList, s.currIdx)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Remove Duplicates from Sorted List ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Remove Duplicates from Sorted List', short: 'Remove Duplicates',
  idea: 'Since the list is sorted, duplicates are adjacent. Keep a <code>curr</code> pointer. If <code>curr.val == curr.next.val</code>, rewire <code>curr.next = curr.next.next</code>. Otherwise, move <code>curr</code> forward.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 1, 2, 3, 3', hint: 'sorted list elements',
  code: [
    'def deleteDuplicates(head):',
    '    curr = head',
    '    while curr and curr.next:',
    '        if curr.val == curr.next.val:',
    '            curr.next = curr.next.next',
    '        else:',
    '            curr = curr.next',
    '    return head'
  ],
  parse(s) {
    return { list: avNums(s, 15, 'list') };
  },
  buildStates({ list }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let logicalList = list.map((val, i) => ({ id: `node_${i}`, val }));
    let currIdx = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx,
      explTitle: 'Initialization',
      explText: `Set curr pointer to the head of the list.`,
      pause: true
    }, ctx);
    
    while (currIdx < logicalList.length && currIdx + 1 < logicalList.length) {
      domPushState(seq, {
        kind: 'loop', line: 3, color: 'blue',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        currIdx,
        explTitle: 'Loop Check',
        explText: `Check if curr and curr.next exist.`
      }, ctx);
      
      domPushState(seq, {
        kind: 'compare', line: 4, color: 'default',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        currIdx,
        explTitle: 'Compare Adjacent Nodes',
        explText: `Is curr.val (${logicalList[currIdx].val}) == curr.next.val (${logicalList[currIdx + 1].val})?`
      }, ctx);
      
      if (logicalList[currIdx].val === logicalList[currIdx + 1].val) {
        let removedNode = logicalList.splice(currIdx + 1, 1)[0];
        
        domPushState(seq, {
          kind: 'remove', line: 5, color: 'red',
          logicalList: JSON.parse(JSON.stringify(logicalList)),
          currIdx, removedNode,
          explTitle: 'Remove Duplicate',
          explText: `Yes. Rewire curr.next to curr.next.next, dropping the duplicate.`
        }, ctx);
      } else {
        currIdx++;
        domPushState(seq, {
          kind: 'advance', line: 7, color: 'emerald',
          logicalList: JSON.parse(JSON.stringify(logicalList)),
          currIdx,
          explTitle: 'Advance Pointer',
          explText: `No. Advance curr to the next node.`
        }, ctx);
      }
    }
    
    domPushState(seq, {
      kind: 'loop-end', line: 3, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx,
      explTitle: 'Loop Terminates',
      explText: `Reached the end of the list.`
    }, ctx);
    
    domPushState(seq, {
      kind: 'done', line: 8, color: 'emerald',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      currIdx,
      explTitle: 'Complete',
      explText: `Return head. All adjacent duplicates removed.`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (logicalList, currIdx) => {
        if (logicalList.length === 0) return `<div class="array-node merged">∅</div>`;
        let html = '';
        logicalList.forEach((node, idx) => {
            let cls = '';
            let ptrHTML = '';
            
            if (idx === currIdx) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:var(--text-bright); top:-30px;">↓ curr</div>`;
            } else if (s.kind === 'done') {
                cls = 'active-k';
            }
            
            if (s.kind === 'remove' && s.removedNode && idx === currIdx) {
               html += `
               <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px;">
                   ${ptrHTML}
                   ${node.val}
                   <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
               
               html += `
               <div class="array-node deleted" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; opacity:0.3; border-color:var(--red); color:var(--red);">
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(45deg); width:100%; height:2px; background:var(--red);"></div>
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-45deg); width:100%; height:2px; background:var(--red);"></div>
                   ${s.removedNode.val}
               </div>`;
               return;
            }
            
            html += `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px;">
                ${ptrHTML}
                ${node.val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        });
        
        html += `<div class="array-node merged" style="position:relative; border:none;background:transparent;">∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Sorted Linked List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.logicalList, s.currIdx)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Remove Nth Node From End of List ========== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Remove Nth Node From End of List', short: 'Remove Nth Node From End of List',
  idea: 'Use a dummy head and two pointers separated by an <code>n</code> step gap. When <code>fast</code> hits the end, <code>slow</code> will be right before the target node.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 4, 5 ; 2', hint: 'list elements ; n',
  code: [
    'def removeNthFromEnd(head, n):',
    '    dummy = ListNode(next=head)',
    '    fast = slow = dummy',
    '    for _ in range(n):',
    '        fast = fast.next',
    '    while fast.next:',
    '        fast = fast.next',
    '        slow = slow.next',
    '    slow.next = slow.next.next',
    '    return dummy.next'
  ],
  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Enter list and n separated by ;');
    const list = avNums(parts[0], 15, 'list');
    const n = avNum(parts[1], 'n');
    return { list, n };
  },
  buildStates({ list, n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let nodes = list.map((val, i) => ({ id: `node_${i}`, val }));
    let dummy = { id: 'dummy', val: 'dummy' };
    let logicalList = [dummy, ...nodes];
    
    let fast = 0;
    let slow = 0;
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      fast, slow, n,
      explTitle: 'Initialization',
      explText: `Create dummy head. Initialize slow and fast pointers to point at dummy. Target n = ${n}.`,
      pause: true
    }, ctx);
    
    domPushState(seq, {
      kind: 'init2', line: 3, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      fast, slow, n,
      explTitle: 'Initialization',
      explText: `Create dummy head. Initialize slow and fast pointers to point at dummy.`
    }, ctx);
    
    for (let i = 0; i < n; i++) {
      if (fast + 1 >= logicalList.length) break;
      fast++;
      domPushState(seq, {
        kind: 'gap', line: 5, color: 'amber',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        fast, slow, n,
        explTitle: 'Create Gap',
        explText: `Advance fast pointer to create an n-step gap (${i+1}/${n}).`
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'gap-done', line: 5, color: 'amber',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      fast, slow, n,
      explTitle: 'Gap Complete',
      explText: `Fast pointer is now ${n} steps ahead of slow.`,
      pause: true
    }, ctx);
    
    while (fast + 1 < logicalList.length) {
      domPushState(seq, {
        kind: 'loop', line: 6, color: 'blue',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        fast, slow, n,
        explTitle: 'Loop Check',
        explText: `Check if fast.next exists.`
      }, ctx);
      
      fast++;
      domPushState(seq, {
        kind: 'slide-fast', line: 7, color: 'amber',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        fast, slow, n,
        explTitle: 'Slide Window',
        explText: `Advance fast pointer.`
      }, ctx);
      
      slow++;
      domPushState(seq, {
        kind: 'slide-slow', line: 8, color: 'emerald',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        fast, slow, n,
        explTitle: 'Slide Window',
        explText: `Advance slow pointer to maintain the gap.`
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'loop-end', line: 6, color: 'default',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      fast, slow, n,
      explTitle: 'Loop Terminates',
      explText: `fast.next is null. The slow pointer is now perfectly positioned right before the target node.`
    }, ctx);
    
    if (slow + 1 < logicalList.length) {
      let removedNode = logicalList.splice(slow + 1, 1)[0];
      // Fast index shifts because we removed a node before it
      if (fast > slow) fast--;
      
      domPushState(seq, {
        kind: 'remove', line: 9, color: 'red',
        logicalList: JSON.parse(JSON.stringify(logicalList)),
        fast, slow, n, removedNode,
        explTitle: 'Remove Node',
        explText: `Rewire slow.next = slow.next.next to drop the nth node from the end.`,
        pause: true
      }, ctx);
    }
    
    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      logicalList: JSON.parse(JSON.stringify(logicalList)),
      fast, slow, n,
      explTitle: 'Complete',
      explText: `Return dummy.next as the new head.`,
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (logicalList, slow, fast) => {
        let html = '';
        logicalList.forEach((node, idx) => {
            let cls = node.id === 'dummy' ? 'merged' : '';
            let style = node.id === 'dummy' ? 'background:var(--bg-elevated);' : '';
            let ptrHTML = '';
            
            if (idx === slow && idx === fast) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:var(--text-bright); top:-35px;">↓ slow, fast</div>`;
            } else if (idx === slow) {
                cls = 'active-k';
                ptrHTML = `<div class="pointer" style="color:#10b981; top:-25px;">↓ slow</div>`;
            } else if (idx === fast) {
                cls = 'active-1';
                ptrHTML = `<div class="pointer" style="color:#f59e0b; top:-25px;">↓ fast</div>`;
            } else if (s.kind === 'done' && idx > 0) {
                cls = 'active-k';
            }
            
            if (s.kind === 'remove' && s.removedNode && idx === slow) {
               html += `
               <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; ${style}">
                   ${ptrHTML}
                   ${node.val}
                   <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
               
               html += `
               <div class="array-node deleted" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; opacity:0.3; border-color:var(--red); color:var(--red);">
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(45deg); width:100%; height:2px; background:var(--red);"></div>
                   <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-45deg); width:100%; height:2px; background:var(--red);"></div>
                   ${s.removedNode.val}
               </div>`;
               return;
            }
            
            html += `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:50%; width:45px; height:45px; ${style}">
                ${ptrHTML}
                ${node.val}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        });
        
        html += `<div class="array-node merged" style="position:relative; border:none;background:transparent;">∅</div>`;
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">n = <span style="color:var(--amber); font-weight:bold;">${s.n}</span></div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:center; flex-wrap:wrap;">${getListHTML(s.logicalList, s.slow, s.fast)}</div>
              </div>
    </div>`;
  }
});
