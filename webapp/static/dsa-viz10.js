/* ============================================================================
   Visualizations for 08_linked_list (Part 4 - Deep Copy, LRU, & Hard Problems)
   ========================================================================= */
"use strict";

/* ================================ 08 · Copy List with Random Pointer ===== */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Copy List with Random Pointer', short: 'Copy List',
  idea: 'Use a hash map to map old nodes to new nodes. First pass: create all new nodes. Second pass: assign next and random pointers.',
  complexity: 'Time O(n) · Space O(n)',
  input: '7,null ; 13,0 ; 11,4 ; 10,2 ; 1,0', hint: 'val,randomIdx ; ...',
  code: [
    'def copyRandomList(head):',
    '    if not head:',
    '        return None',
    '    old_to_new = {}',
    '    curr = head',
    '    while curr:',
    '        old_to_new[curr] = Node(curr.val)',
    '        curr = curr.next',
    '    curr = head',
    '    while curr:',
    '        copy = old_to_new[curr]',
    '        copy.next = old_to_new.get(curr.next)',
    '        copy.random = old_to_new.get(curr.random)',
    '        curr = curr.next',
    '    return old_to_new[head]'
  ],
  parse(s) {
    const parts = avParts(s);
    const list = parts.map(p => {
        let [v, r] = p.split(',').map(x => x.trim());
        return { val: v, random: r === 'null' ? null : Number(r) };
    });
    return { list };
  },
  buildStates({ list }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    // Build initial node list
    let oldList = list.map((node, i) => ({
        id: `old_${i}`, val: node.val, 
        next: i + 1 < list.length ? i + 1 : null,
        random: node.random
    }));
    
    let newList = [];
    
    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      oldList, newList: [...newList], curr: 0,
      explTitle: 'Initialization',
      explText: 'Initialize a hash map `old_to_new` and set curr to head.',
      pause: true
    }, ctx);
    
    // First pass
    let curr = 0;
    while (curr < oldList.length) {
      newList.push({ id: `new_${curr}`, val: oldList[curr].val, next: null, random: null });
      
      domPushState(seq, {
        kind: 'pass1', line: 7, color: 'amber',
        oldList, newList: [...newList], curr,
        explTitle: 'First Pass: Create Copies',
        explText: `Create a copy of node with value ${oldList[curr].val} and store in hash map.`
      }, ctx);
      
      curr++;
    }
    
    curr = 0;
    domPushState(seq, {
      kind: 'pass2-init', line: 9, color: 'default',
      oldList, newList: [...newList], curr,
      explTitle: 'Second Pass',
      explText: 'Reset curr to head. Now we will assign next and random pointers using the hash map.',
      pause: true
    }, ctx);
    
    // Second pass
    while (curr < oldList.length) {
      if (oldList[curr].next !== null) newList[curr].next = oldList[curr].next;
      if (oldList[curr].random !== null) newList[curr].random = oldList[curr].random;
      
      domPushState(seq, {
        kind: 'pass2', line: 12, color: 'blue',
        oldList, newList: JSON.parse(JSON.stringify(newList)), curr,
        explTitle: 'Second Pass: Assign Pointers',
        explText: `For node ${oldList[curr].val}, assign copy.next and copy.random using old_to_new mapping.`
      }, ctx);
      
      curr++;
    }
    
    domPushState(seq, {
      kind: 'done', line: 15, color: 'emerald',
      oldList, newList: JSON.parse(JSON.stringify(newList)), curr: null,
      explTitle: 'Complete',
      explText: 'Return the head of the new copied list.',
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (nodes, isNewList) => {
        if(nodes.length === 0) return `<div style="color:var(--text-dim); padding:10px;">Empty</div>`;
        return nodes.map((node, idx) => {
            let cls = '';
            let ptrs = [];
            
            if (s.curr === idx && !isNewList) {
                cls = 'active-1';
                ptrs.push(`<div class="pointer" style="color:#10b981; top:-25px;">↓ curr</div>`);
            } else if (s.curr === idx && isNewList) {
                cls = 'active-k';
                ptrs.push(`<div class="pointer" style="color:#3b82f6; top:-40px;">↓ copy</div>`);
            }
            
            let nextStr = node.next !== null ? `next: idx ${node.next}` : `next: ∅`;
            let randStr = node.random !== null ? `rand: idx ${node.random}` : `rand: ∅`;
            
            return `
            <div class="array-node ${cls}" style="position:relative; margin-right:15px; border-radius:8px; padding:10px; min-width:80px; flex-shrink:0;">
                ${ptrs.join('')}
                <div style="font-weight:bold; text-align:center; margin-bottom:5px;">${node.val}</div>
                <div style="font-size:11px; color:var(--text-dim);">${nextStr}</div>
                <div style="font-size:11px; color:var(--text-dim);">${randStr}</div>
                <div class="node-index" style="position:absolute; right:-25px; top:15px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        }).join('') + `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Original List</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:30px; justify-content:flex-start; overflow-x:auto;">${getListHTML(s.oldList, false)}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Copied List (old_to_new values)</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:40px; justify-content:flex-start; overflow-x:auto;">${getListHTML(s.newList, true)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · LRU Cache ========================= */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'LRU Cache', short: 'LRU Cache',
  idea: 'Use a hash map for O(1) lookups and a doubly linked list for O(1) removals and insertions. The MRU is kept near the head, and LRU near the tail.',
  complexity: 'Time O(1) per operation · Space O(capacity)',
  input: 'cap:2 ; put:1,1 ; put:2,2 ; get:1 ; put:3,3 ; get:2 ; put:4,4 ; get:1 ; get:3 ; get:4', hint: 'cap:C ; op:args ; ...',
  code: [
    'class LRUCache:',
    '    def __init__(self, capacity):',
    '        self.cap = capacity',
    '        self.cache = {}',
    '        self.head, self.tail = Node(), Node()',
    '        self.head.next, self.tail.prev = self.tail, self.head',
    '    def _remove(self, node):',
    '        node.prev.next = node.next',
    '        node.next.prev = node.prev',
    '    def _insert_front(self, node):',
    '        node.prev, node.next = self.head, self.head.next',
    '        self.head.next.prev = node',
    '        self.head.next = node',
    '    def get(self, key):',
    '        if key in self.cache:',
    '            node = self.cache[key]',
    '            self._remove(node)',
    '            self._insert_front(node)',
    '            return node.val',
    '        return -1',
    '    def put(self, key, value):',
    '        if key in self.cache:',
    '            self._remove(self.cache[key])',
    '        node = Node(key, value)',
    '        self.cache[key] = node',
    '        self._insert_front(node)',
    '        if len(self.cache) > self.cap:',
    '            lru = self.tail.prev',
    '            self._remove(lru)',
    '            del self.cache[lru.key]'
  ],
  parse(s) {
    const ops = avParts(s);
    let cap = 2;
    let parsedOps = [];
    ops.forEach(op => {
        let [cmd, args] = op.split(':').map(x => x.trim());
        if (cmd === 'cap') { cap = Number(args); }
        else {
            let argParts = args.split(',').map(x => x.trim());
            parsedOps.push({ cmd, k: Number(argParts[0]), v: argParts[1] ? Number(argParts[1]) : null });
        }
    });
    return { cap, ops: parsedOps };
  },
  buildStates({ cap, ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    let cacheList = []; // Array representing Doubly Linked List from Head (MRU) to Tail (LRU)
    let mapSize = 0;
    
    domPushState(seq, {
      kind: 'init', line: 6, color: 'default',
      cap, cacheList: [...cacheList], mapSize,
      opTitle: 'LRUCache(capacity)', opCmd: `Init Cache with capacity ${cap}`,
      explTitle: 'Initialization',
      explText: 'Create a dummy head (MRU) and dummy tail (LRU).',
      pause: true
    }, ctx);
    
    for (let op of ops) {
        if (op.cmd === 'get') {
            let foundIdx = cacheList.findIndex(n => n.k === op.k);
            let found = foundIdx !== -1;
            
            domPushState(seq, {
              kind: 'get-init', line: 15, color: found ? 'blue' : 'red',
              cap, cacheList: [...cacheList], mapSize,
              opTitle: `get(${op.k})`, opCmd: `GET key ${op.k}`,
              explTitle: 'Lookup Cache',
              explText: found ? `Key ${op.k} found in hash map.` : `Key ${op.k} not found. Return -1.`,
              pause: true
            }, ctx);
            
            if (found) {
                let node = cacheList.splice(foundIdx, 1)[0];
                
                domPushState(seq, {
                  kind: 'get-remove', line: 17, color: 'amber',
                  cap, cacheList: [...cacheList], mapSize, highlight: node.k,
                  opTitle: `get(${op.k})`, opCmd: `GET key ${op.k}`,
                  explTitle: 'Remove Node',
                  explText: `Remove node (${node.k}, ${node.v}) from its current position.`
                }, ctx);
                
                cacheList.unshift(node);
                
                domPushState(seq, {
                  kind: 'get-insert', line: 18, color: 'emerald',
                  cap, cacheList: [...cacheList], mapSize, highlight: node.k,
                  opTitle: `get(${op.k})`, opCmd: `GET key ${op.k}`,
                  explTitle: 'Insert at Front (MRU)',
                  explText: `Insert node (${node.k}, ${node.v}) right after head, making it the MRU. Return ${node.v}.`
                }, ctx);
            }
        } else if (op.cmd === 'put') {
            let foundIdx = cacheList.findIndex(n => n.k === op.k);
            let found = foundIdx !== -1;
            
            domPushState(seq, {
              kind: 'put-init', line: 22, color: 'blue',
              cap, cacheList: [...cacheList], mapSize,
              opTitle: `put(${op.k}, ${op.v})`, opCmd: `PUT key ${op.k}, val ${op.v}`,
              explTitle: 'Put Value',
              explText: found ? `Key ${op.k} exists. We must remove it first.` : `Key ${op.k} is new. Create node.`,
              pause: true
            }, ctx);
            
            if (found) {
                cacheList.splice(foundIdx, 1);
                mapSize--;
                
                domPushState(seq, {
                  kind: 'put-remove', line: 23, color: 'amber',
                  cap, cacheList: [...cacheList], mapSize,
                  opTitle: `put(${op.k}, ${op.v})`, opCmd: `PUT key ${op.k}, val ${op.v}`,
                  explTitle: 'Remove Existing Node',
                  explText: `Removed old node for key ${op.k}.`
                }, ctx);
            }
            
            let newNode = { k: op.k, v: op.v };
            cacheList.unshift(newNode);
            mapSize++;
            
            domPushState(seq, {
              kind: 'put-insert', line: 26, color: 'emerald',
              cap, cacheList: [...cacheList], mapSize, highlight: newNode.k,
              opTitle: `put(${op.k}, ${op.v})`, opCmd: `PUT key ${op.k}, val ${op.v}`,
              explTitle: 'Insert at Front (MRU)',
              explText: `Insert node (${newNode.k}, ${newNode.v}) right after head.`
            }, ctx);
            
            if (mapSize > cap) {
                let lruNode = cacheList.pop();
                mapSize--;
                
                domPushState(seq, {
                  kind: 'put-evict', line: 29, color: 'red',
                  cap, cacheList: [...cacheList], mapSize, highlight: lruNode.k,
                  opTitle: `put(${op.k}, ${op.v})`, opCmd: `PUT key ${op.k}, val ${op.v}`,
                  explTitle: 'Evict LRU Node',
                  explText: `Capacity exceeded (${mapSize + 1} > ${cap}). Remove LRU node from tail: key ${lruNode.k}.`
                }, ctx);
            }
        }
    }
    
    domPushState(seq, {
      kind: 'done', line: 1, color: 'default',
      cap, cacheList: [...cacheList], mapSize,
      opTitle: 'Completed', opCmd: `All operations done.`,
      explTitle: 'Done',
      explText: 'Cache sequence completed.',
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (list) => {
        let html = `
        <div class="array-node merged" style="flex-direction:column; background:var(--bg-surface); padding:10px; border-radius:8px; margin-right:20px; position:relative;">
            <div style="font-size:12px; font-weight:bold; color:var(--text-bright); margin-bottom:5px;">HEAD</div>
            <div style="font-size:10px; color:var(--text-dim);">MRU</div>
            <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">⇄</div>
    </div>`;
        
        if (list.length === 0) {
            html += `<div style="color:var(--text-dim); padding:20px; margin-right:15px; font-style:italic;">(Empty)</div>`;
        } else {
            html += list.map((node, idx) => {
                let cls = node.k === s.highlight ? 'active-1' : 'merged';
                let borderColor = node.k === s.highlight ? 'border-color:var(--emerald);' : '';
                
                let nextArrow = idx === list.length - 1 ? '⇄' : '⇄';
                
                return `
                <div class="array-node ${cls}" style="flex-direction:column; margin-right:20px; border-radius:8px; padding:10px; min-width:60px; ${borderColor}">
                    <div style="font-size:11px; color:var(--text-dim); margin-bottom:2px;">k:${node.k}</div>
                    <div style="font-weight:bold; font-size:16px;">v:${node.v}</div>
                    <div class="node-index" style="position:absolute; right:-28px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">${nextArrow}</div>
    </div>`;
            }).join('');
        }
        
        html += `
        <div class="array-node merged" style="flex-direction:column; background:var(--bg-surface); padding:10px; border-radius:8px; position:relative; margin-left:5px;">
            <div style="font-size:12px; font-weight:bold; color:var(--text-bright); margin-bottom:5px;">TAIL</div>
            <div style="font-size:10px; color:var(--text-dim);">LRU</div>
    </div>`;
        
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              
              <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:15px; border-radius:8px; border-left:4px solid var(--blue);">
                  <div>
                      <div style="font-size:12px; color:var(--text-dim); text-transform:uppercase;">Current Operation</div>
                      <div style="font-size:18px; font-weight:bold; color:var(--text-bright);">${s.opTitle}</div>
                  </div>
                  <div style="text-align:right;">
                      <div style="font-size:12px; color:var(--text-dim); text-transform:uppercase;">Capacity</div>
                      <div style="font-size:18px; font-weight:bold; color:${s.mapSize > s.cap ? 'var(--red)' : 'var(--text-bright)'};">${s.mapSize} / ${s.cap}</div>
                  </div>
              </div>
              
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Doubly Linked List (MRU to LRU)</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px; justify-content:flex-start; overflow-x:auto;">${getListHTML(s.cacheList)}</div>
              </div>
    </div>`;
  }
});
/* ================================ 08 · Merge k Sorted Lists ================ */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Merge k Sorted Lists', short: 'Merge k Lists',
  idea: 'Use a min-heap to keep track of the smallest current element among all k lists. Extract minimum, append to result, and push its next element to heap.',
  complexity: 'Time O(N log k) · Space O(k)',
  input: '1,4,5 ; 1,3,4 ; 2,6', hint: 'list1 ; list2 ; list3...',
  code: [
    'def mergeKLists(lists):',
    '    heap = []',
    '    for i, node in enumerate(lists):',
    '        if node:',
    '            heapq.heappush(heap, (node.val, i, node))',
    '    dummy = tail = ListNode()',
    '    while heap:',
    '        val, i, node = heapq.heappop(heap)',
    '        tail.next = node',
    '        tail = tail.next',
    '        if node.next:',
    '            heapq.heappush(heap, (node.next.val, i, node.next))',
    '    return dummy.next'
  ],
  parse(s) {
    const parts = avParts(s);
    const lists = parts.map((p, i) => avNums(p, 10, `list${i+1}`));
    return { lists };
  },
  buildStates({ lists }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    // Model each list as array of objects
    let stateLists = lists.map((arr, listIdx) => {
        return arr.map((val, idx) => ({ val, listIdx, idx }));
    });
    
    let heap = []; // Will store {val, listIdx, idx}
    let merged = [];
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
      explTitle: 'Initialization',
      explText: 'Create an empty min-heap and a dummy head for the merged list.',
      pause: true
    }, ctx);
    
    for (let i = 0; i < stateLists.length; i++) {
        if (stateLists[i].length > 0) {
            heap.push(stateLists[i][0]);
            heap.sort((a, b) => a.val - b.val); // simulate min-heap
            
            domPushState(seq, {
              kind: 'heap-init', line: 5, color: 'amber',
              stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
              highlightList: i, highlightIdx: 0,
              explTitle: 'Push Heads to Heap',
              explText: `Push the head of list ${i} (value ${stateLists[i][0].val}) to the min-heap.`
            }, ctx);
        }
    }
    
    domPushState(seq, {
      kind: 'while-init', line: 7, color: 'default',
      stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
      explTitle: 'Begin Merging',
      explText: 'While the heap is not empty, extract the minimum node.',
      pause: true
    }, ctx);
    
    while (heap.length > 0) {
        let minNode = heap.shift(); // extract min
        
        domPushState(seq, {
          kind: 'pop', line: 8, color: 'red',
          stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
          popped: minNode,
          explTitle: 'Extract Minimum',
          explText: `Pop the smallest node (value ${minNode.val} from list ${minNode.listIdx}) from the heap.`
        }, ctx);
        
        merged.push(minNode);
        
        domPushState(seq, {
          kind: 'append', line: 9, color: 'emerald',
          stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
          explTitle: 'Append to Tail',
          explText: `Append value ${minNode.val} to the merged list tail.`
        }, ctx);
        
        if (minNode.idx + 1 < stateLists[minNode.listIdx].length) {
            let nextNode = stateLists[minNode.listIdx][minNode.idx + 1];
            heap.push(nextNode);
            heap.sort((a, b) => a.val - b.val); // simulate min-heap
            
            domPushState(seq, {
              kind: 'push', line: 12, color: 'blue',
              stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
              highlightList: nextNode.listIdx, highlightIdx: nextNode.idx,
              explTitle: 'Push Next Node',
              explText: `Node has a next element. Push value ${nextNode.val} from list ${nextNode.listIdx} to the heap.`
            }, ctx);
        }
    }
    
    domPushState(seq, {
      kind: 'done', line: 13, color: 'emerald',
      stateLists: JSON.parse(JSON.stringify(stateLists)), heap: [...heap], merged: [...merged],
      explTitle: 'Complete',
      explText: 'Heap is empty. Return dummy.next as the head of the fully merged list!',
      pause: true
    }, ctx);
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListsHTML = (stateLists, merged, heap) => {
        let html = '';
        stateLists.forEach((list, listIdx) => {
            html += `<div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="width:60px; font-weight:bold; color:var(--text-dim);">L${listIdx}</div>
                <div style="display:flex;">`;
            
            if (list.length === 0) {
                html += `<div class="array-node merged" style="background:transparent; border:none; opacity:0.5;">∅</div>`;
            } else {
                list.forEach((node, idx) => {
                    let isMerged = merged.some(m => m.listIdx === listIdx && m.idx === idx);
                    let isInHeap = heap.some(h => h.listIdx === listIdx && h.idx === idx);
                    
                    let cls = '';
                    let borderColor = '';
                    
                    if (isMerged) {
                        cls = 'merged';
                    } else if (isInHeap) {
                        cls = 'active-k';
                        borderColor = 'border-color:var(--amber); color:var(--amber);';
                    } else if (s.highlightList === listIdx && s.highlightIdx === idx) {
                        cls = 'active-1';
                        borderColor = 'border-color:var(--blue);';
                    }
                    
                    html += `
                    <div class="array-node ${cls}" style="margin-right:15px; border-radius:50%; width:40px; height:40px; ${borderColor}">
                        ${node.val}
                        <div class="node-index" style="position:absolute; right:-20px; font-size:20px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
                });
                html += `<div class="array-node merged" style="background:transparent; border:none; opacity:0.5;">∅</div>`;
            }
            html += `</div>
    </div>`;
        });
        return html;
    };
    
    const getMergedHTML = (merged) => {
        if(merged.length === 0) return `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent;">→ ∅</div>`;
        let html = `<div class="array-node merged">dummy</div><div class="array-node merged" style="border:none;background:transparent; margin-right:15px;">→</div>`;
        html += merged.map((node, idx) => {
            return `
            <div class="array-node active-1" style="border-radius:50%; width:40px; height:40px; margin-right:15px; border-color:var(--emerald); color:var(--emerald);">
                <div style="position:absolute; top:-15px; font-size:10px; color:var(--text-dim);">L${node.listIdx}</div>
                ${node.val}
                <div class="node-index" style="position:absolute; right:-20px; font-size:20px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>
    </div>`;
        }).join('');
        html += `<div class="array-node merged" style="border:none;background:transparent;">∅</div>`;
        return html;
    };
    
    const getHeapHTML = (heap) => {
        if (heap.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">(Empty Heap)</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:10px;">` + heap.map(node => {
            return `
            <div class="array-node active-k" style="border-radius:8px; padding:5px 10px; border-color:var(--amber); color:var(--amber);">
                <span style="font-size:12px; margin-right:5px; color:var(--text-dim);">val:</span>${node.val} 
                <span style="font-size:10px; margin-left:5px; color:var(--text-dim);">(L${node.listIdx})</span>
            </div>`;
        }).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Input Lists</div>
                  <div class="array-track" style="padding-bottom:10px; padding-top:20px; flex-direction:column; overflow-x:auto;">${getListsHTML(s.stateLists, s.merged, s.heap)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--amber);">
                  <div class="panel-heading">Min-Heap State</div>
                  <div class="array-track" style="padding:10px; justify-content:flex-start;">${getHeapHTML(s.heap)}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Merged Result</div>
                  <div class="array-track" style="padding-bottom:15px; padding-top:20px; justify-content:flex-start; flex-wrap:wrap;">${getMergedHTML(s.merged)}</div>
              </div>
    </div>`;
  }
});

/* ================================ 08 · Reverse Nodes in k-Group ============ */
defineAlgoDom('08_linked_list', {
  type: 'dom',
  title: 'Reverse Nodes in k-Group', short: 'Reverse k-Group',
  idea: 'Use a dummy head. Check if there are k nodes ahead. If yes, reverse those k nodes, rewire pointers, and move to the next group. Otherwise, stop.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 4, 5 ; 2', hint: 'list ; k',
  code: [
    'def reverseKGroup(head, k):',
    '    dummy = ListNode(next=head)',
    '    group_prev = dummy',
    '    while True:',
    '        kth = group_prev',
    '        for _ in range(k):',
    '            kth = kth.next',
    '            if not kth:',
    '                return dummy.next',
    '        group_next = kth.next',
    '        prev, curr = group_next, group_prev.next',
    '        for _ in range(k):',
    '            nxt = curr.next',
    '            curr.next = prev',
    '            prev = curr',
    '            curr = nxt',
    '        tmp = group_prev.next',
    '        group_prev.next = kth',
    '        group_prev = tmp'
  ],
  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Enter list and k separated by ;');
    const list = avNums(parts[0], 20, 'list');
    const k = avNum(parts[1], 'k');
    return { list, k };
  },
  buildStates({ list, k }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    
    // Internal node representation
    // idx 0 is dummy. list nodes are 1..list.length
    let nodes = [{ id: 'dummy', val: 'D', next: list.length > 0 ? 1 : null }];
    list.forEach((val, i) => {
        nodes.push({ id: `node_${i+1}`, val, next: i + 1 < list.length ? i + 2 : null });
    });
    
    let group_prev = 0; // dummy
    
    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth: null, group_next: null, prev: null, curr: null,
      explTitle: 'Initialization',
      explText: 'Create a dummy head. group_prev points to dummy.',
      pause: true
    }, ctx);
    
    while (true) {
        let kth = group_prev;
        let enoughNodes = true;
        
        domPushState(seq, {
          kind: 'check-k', line: 5, color: 'blue',
          nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next: null, prev: null, curr: null,
          explTitle: 'Check Next k Nodes',
          explText: `Check if there are at least k=${k} nodes remaining.`
        }, ctx);
        
        for (let count = 0; count < k; count++) {
            kth = nodes[kth].next;
            if (kth === null) {
                enoughNodes = false;
                break;
            }
        }
        
        if (!enoughNodes) {
            domPushState(seq, {
              kind: 'done', line: 9, color: 'emerald',
              nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next: null, prev: null, curr: null,
              explTitle: 'Not Enough Nodes',
              explText: `Fewer than k nodes remaining. Return dummy.next!`,
              pause: true
            }, ctx);
            break;
        }
        
        let group_next = nodes[kth].next;
        
        domPushState(seq, {
          kind: 'group-found', line: 10, color: 'default',
          nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next, prev: null, curr: null,
          explTitle: 'Group Found',
          explText: `Found ${k} nodes. The k-th node is ${nodes[kth].val}. group_next points to ${group_next !== null ? nodes[group_next].val : 'null'}.`,
          pause: true
        }, ctx);
        
        let prev = group_next;
        let curr = nodes[group_prev].next;
        let original_first = curr;
        
        domPushState(seq, {
          kind: 'reverse-init', line: 11, color: 'blue',
          nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next, prev, curr,
          explTitle: 'Initialize Reversal',
          explText: 'Set prev = group_next and curr = first node of group. We will now reverse this group.'
        }, ctx);
        
        for (let count = 0; count < k; count++) {
            let nxt = nodes[curr].next;
            nodes[curr].next = prev;
            prev = curr;
            curr = nxt;
            
            domPushState(seq, {
              kind: 'reverse-step', line: 14, color: 'amber',
              nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next, prev, curr,
              explTitle: 'Reverse Pointer',
              explText: `Reversed pointer for node ${nodes[prev].val}.`
            }, ctx);
        }
        
        let tmp = nodes[group_prev].next; // original first, which is now last in group
        nodes[group_prev].next = kth; // rewire group_prev to point to the new head of group (original kth)
        
        domPushState(seq, {
          kind: 'rewire-group', line: 18, color: 'emerald',
          nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth, group_next, prev: null, curr: null,
          explTitle: 'Rewire group_prev',
          explText: `Rewire group_prev (node ${nodes[group_prev].val}) to point to the new first node (${nodes[kth].val}).`
        }, ctx);
        
        group_prev = original_first; // move group_prev to the end of the reversed group
        
        domPushState(seq, {
          kind: 'advance-group', line: 19, color: 'default',
          nodes: JSON.parse(JSON.stringify(nodes)), k, group_prev, kth: null, group_next: null, prev: null, curr: null,
          explTitle: 'Advance group_prev',
          explText: `Move group_prev to node ${nodes[group_prev].val} to prepare for the next group.`,
          pause: true
        }, ctx);
    }
    
    return seq;
  },
  renderDOM(container, s, spec) {
    const getListHTML = (nodes) => {
        let html = '';
        
        // Find ordered traversal for visual display since pointers get mangled
        // We will just render nodes in logical order starting from dummy (index 0)
        let logicalOrder = [];
        let curr = 0;
        let visited = new Set();
        while (curr !== null && !visited.has(curr)) {
            logicalOrder.push({idx: curr, node: nodes[curr]});
            visited.add(curr);
            curr = nodes[curr].next;
        }
        
        logicalOrder.forEach((item, displayIdx) => {
            let cls = '';
            let ptrs = [];
            
            if (item.idx === s.group_prev) {
                cls = 'active-k';
                ptrs.push(`<div class="pointer" style="color:#f59e0b; top:-25px; white-space:nowrap;">↓ group_prev</div>`);
            }
            if (s.kth !== null && item.idx === s.kth) {
                cls = 'active-1';
                ptrs.push(`<div class="pointer" style="color:#10b981; top:-40px;">↓ kth</div>`);
            }
            if (s.group_next !== null && item.idx === s.group_next) {
                ptrs.push(`<div class="pointer" style="color:#8b5cf6; top:-55px; white-space:nowrap;">↓ group_next</div>`);
            }
            
            if (s.kind.startsWith('reverse')) {
                if (item.idx === s.prev) ptrs.push(`<div class="pointer" style="color:#3b82f6; bottom:-25px;">↑ prev</div>`);
                if (item.idx === s.curr) ptrs.push(`<div class="pointer" style="color:#ef4444; bottom:-40px;">↑ curr</div>`);
                if (item.idx === s.prev || item.idx === s.curr) cls = 'active-1';
            }
            
            let valHtml = item.idx === 0 ? `<div style="font-size:12px; font-weight:bold;">DUMMY</div>` : `<div style="font-weight:bold; font-size:16px;">${item.node.val}</div>`;
            let nextArrow = '→';
            if (item.node.next === null) nextArrow = '∅';
            else if (displayIdx + 1 < logicalOrder.length && logicalOrder[displayIdx+1].idx !== item.node.next) {
                nextArrow = `→ <span style="font-size:10px">idx ${item.node.next}</span>`;
            }
            
            html += `
            <div class="array-node ${cls}" style="position:relative; margin-right:20px; margin-bottom:40px; border-radius:50%; width:50px; height:50px; flex-shrink:0;">
                ${ptrs.join('')}
                <div style="position:absolute; top:-15px; font-size:10px; color:var(--text-dim);">idx ${item.idx}</div>
                ${valHtml}
                <div class="node-index" style="position:absolute; right:-25px; font-size:24px; color:var(--text-dim); background:transparent; border:none; box-shadow:none; z-index:10;">${nextArrow}</div>
    </div>`;
        });
        
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Linked List (Logical Traversal Order)</div>
                  <div class="array-track" style="padding-bottom:30px; padding-top:60px; justify-content:flex-start; flex-wrap:wrap;">${getListHTML(s.nodes)}</div>
              </div>
    </div>`;
  }
});
