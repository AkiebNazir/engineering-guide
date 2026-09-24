content = """
defineAlgo('22_sorting_algorithms', {
  title: 'Sort Colors', short: 'Sort Colors',
  idea: 'Dutch National Flag algorithm. Use three pointers: low, mid, and high. mid scans the array and swaps elements to place 0s before low, 2s after high, and leaves 1s in the middle.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,0,2,1,1,0', hint: 'comma-separated colors (0, 1, 2)',
  code: [
    'def sortColors(nums):',
    '    low, mid, high = 0, 0, len(nums) - 1',
    '    while mid <= high:',
    '        if nums[mid] == 0:',
    '            nums[low], nums[mid] = nums[mid], nums[low]',
    '            low += 1',
    '            mid += 1',
    '        elif nums[mid] == 1:',
    '            mid += 1',
    '        else:',
    '            nums[mid], nums[high] = nums[high], nums[mid]',
    '            high -= 1'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], low: 0, mid: 0, high: nums.length - 1 };
    
    snap(2, 'Initialize pointers: low = 0, mid = 0, high = len - 1.', s);
    
    while (s.mid <= s.high) {
        if (s.nums[s.mid] === 0) {
            snap(4, `nums[mid] is 0. Swap nums[low] and nums[mid].`, s);
            let temp = s.nums[s.low];
            s.nums[s.low] = s.nums[s.mid];
            s.nums[s.mid] = temp;
            s.low++;
            s.mid++;
            snap(6, `Increment low and mid.`, s);
        } else if (s.nums[s.mid] === 1) {
            snap(8, `nums[mid] is 1. Just increment mid.`, s);
            s.mid++;
            snap(9, `Increment mid.`, s);
        } else {
            snap(11, `nums[mid] is 2. Swap nums[mid] and nums[high].`, s);
            let temp = s.nums[s.high];
            s.nums[s.high] = s.nums[s.mid];
            s.nums[s.mid] = temp;
            s.high--;
            snap(12, `Decrement high.`, s);
        }
    }
    snap(12, 'Sorting complete.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.nums.map((val, i) => {
        let bg = 'var(--surface)';
        if (val === 0) bg = '#fca5a5'; // Red-ish
        else if (val === 1) bg = '#fde047'; // White/Yellow-ish
        else if (val === 2) bg = '#93c5fd'; // Blue-ish
        
        let labels = [];
        if (i === state.low) labels.push('<div style="color:#ef4444; font-size:12px; font-weight:bold;">low</div>');
        if (i === state.mid) labels.push('<div style="color:var(--accent); font-size:12px; font-weight:bold;">mid</div>');
        if (i === state.high) labels.push('<div style="color:#3b82f6; font-size:12px; font-weight:bold;">high</div>');
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
            <div style="height:45px; display:flex; flex-direction:column; justify-content:flex-end;">
                ${labels.join('')}
            </div>
            <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); background:${bg}; color:#000; border-radius:4px; font-weight:bold; margin-top:5px;">
                ${val}
            </div>
            <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">${i}</div>
        </div>`;
    }).join('');
    
    let html = `
        <div style="font-family:var(--mono);">
            <div style="display:flex; gap:10px;">${boxes}</div>
            <div style="margin-top:20px; font-size:14px; color:var(--text-dim);">
                Colors: <span style="color:#ef4444; font-weight:bold;">0 (Red)</span>, 
                <span style="color:#eab308; font-weight:bold;">1 (White)</span>, 
                <span style="color:#3b82f6; font-weight:bold;">2 (Blue)</span>
            </div>
        </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Sort List', short: 'Sort List',
  idea: 'Top-down merge sort on a linked list. Use fast and slow pointers to find the middle, split the list, recursively sort both halves, and then merge them.',
  complexity: 'Time O(N log N) · Space O(log N) recursion depth',
  input: '4,2,1,3', hint: 'comma-separated values',
  code: [
    'def sortList(head):',
    '    if not head or not head.next:',
    '        return head',
    '    ',
    '    slow, fast = head, head.next',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '    ',
    '    mid = slow.next',
    '    slow.next = None',
    '    ',
    '    left = sortList(head)',
    '    right = sortList(mid)',
    '    return merge(left, right)',
    '',
    'def merge(list1, list2):',
    '    dummy = ListNode()',
    '    tail = dummy',
    '    while list1 and list2:',
    '        if list1.val < list2.val:',
    '            tail.next = list1',
    '            list1 = list1.next',
    '        else:',
    '            tail.next = list2',
    '            list2 = list2.next',
    '        tail = tail.next',
    '    tail.next = list1 or list2',
    '    return dummy.next'
  ],
  parse(str) {
    return { vals: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ vals }) {
    const { F, snap } = avRecorder();
    let s = { list1: [], list2: [], action: 'Start', merged: [...vals] };
    
    function mergeSortList(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.ceil(arr.length / 2); // To mimic slow/fast pointer (head.next)
        
        s.action = 'Splitting List';
        s.list1 = arr.slice(0, mid);
        s.list2 = arr.slice(mid);
        s.merged = [];
        snap(10, `Split list into two halves.`, s);
        
        let left = mergeSortList(arr.slice(0, mid), lLevel + 1);
        let right = mergeSortList(arr.slice(mid), lLevel + 1);
        
        return mergeArrays(left, right);
    }
    
    function mergeArrays(left, right) {
        let res = [];
        let i = 0, j = 0;
        
        s.action = 'Merging Lists';
        s.list1 = left.slice(i);
        s.list2 = right.slice(j);
        s.merged = [...res];
        snap(18, `Start merging.`, s);
        
        while (i < left.length && j < right.length) {
            if (left[i] < right[j]) {
                res.push(left[i]);
                i++;
            } else {
                res.push(right[j]);
                j++;
            }
            s.list1 = left.slice(i);
            s.list2 = right.slice(j);
            s.merged = [...res];
            snap(20, `Merge step.`, s);
        }
        res = res.concat(left.slice(i)).concat(right.slice(j));
        s.list1 = [];
        s.list2 = [];
        s.merged = [...res];
        snap(27, `Merge complete for this segment.`, s);
        return res;
    }
    
    let result = mergeSortList(vals, 0);
    s.action = 'Done';
    s.merged = result;
    s.list1 = [];
    s.list2 = [];
    snap(28, `List is fully sorted.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let renderList = (arr) => {
        if (!arr || arr.length === 0) return `<div style="color:var(--text-dim); font-style:italic;">null</div>`;
        return arr.map((val, i) => {
            let node = `<div style="display:flex; align-items:center; justify-content:center; width:35px; height:35px; border:1px solid var(--border); border-radius:50%; background:var(--surface); font-weight:bold;">${val}</div>`;
            if (i < arr.length - 1) {
                return node + `<div style="margin:0 5px; color:var(--text-dim);">→</div>`;
            }
            return node;
        }).join('');
    };
    
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div style="font-size:14px; color:var(--text-dim);">Left List (or Split 1):</div>
            <div style="display:flex; align-items:center;">${renderList(state.list1)}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div style="font-size:14px; color:var(--text-dim);">Right List (or Split 2):</div>
            <div style="display:flex; align-items:center;">${renderList(state.list2)}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; gap:10px; margin-top:20px;">
            <div style="font-size:14px; color:var(--text-dim);">Merged / Result List:</div>
            <div style="display:flex; align-items:center;">${renderList(state.merged)}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done chunk 2")
