content = """
defineAlgo('22_sorting_algorithms', {
  title: 'Maximum Gap', short: 'Maximum Gap',
  idea: 'Use Bucket Sort concept (Pigeonhole principle). Divide the range into buckets of size `(max - min) / (N - 1)`. The maximum gap cannot be within a single bucket, so we only need to track the min and max of each bucket, and find the max difference between adjacent non-empty buckets.',
  complexity: 'Time O(N) · Space O(N)',
  input: '3, 6, 9, 1', hint: 'comma-separated integers',
  code: [
    'def maximumGap(nums):',
    '    if len(nums) < 2: return 0',
    '    lo, hi = min(nums), max(nums)',
    '    if lo == hi: return 0',
    '    ',
    '    bucket_size = max(1, (hi - lo) // (len(nums) - 1))',
    '    bucket_count = (hi - lo) // bucket_size + 1',
    '    bucket_min = [None] * bucket_count',
    '    bucket_max = [None] * bucket_count',
    '    ',
    '    for x in nums:',
    '        idx = (x - lo) // bucket_size',
    '        bucket_min[idx] = x if bucket_min[idx] is None else min(bucket_min[idx], x)',
    '        bucket_max[idx] = x if bucket_max[idx] is None else max(bucket_max[idx], x)',
    '        ',
    '    max_gap, prev_max = 0, lo',
    '    for i in range(bucket_count):',
    '        if bucket_min[i] is None: continue',
    '        max_gap = max(max_gap, bucket_min[i] - prev_max)',
    '        prev_max = bucket_max[i]',
    '    return max_gap'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], bucket_min: [], bucket_max: [], max_gap: 0, prev_max: null, curr_num: null, curr_bucket: null, curr_gap: null };
    
    if (nums.length < 2) {
        snap(2, 'Less than 2 elements, max gap is 0.', s);
        return F;
    }
    
    let lo = Math.min(...nums);
    let hi = Math.max(...nums);
    
    if (lo === hi) {
        snap(4, 'All elements are equal, max gap is 0.', s);
        return F;
    }
    
    let bucket_size = Math.max(1, Math.floor((hi - lo) / (nums.length - 1)));
    let bucket_count = Math.floor((hi - lo) / bucket_size) + 1;
    
    s.bucket_min = new Array(bucket_count).fill(null);
    s.bucket_max = new Array(bucket_count).fill(null);
    
    snap(9, `Calculated Min: ${lo}, Max: ${hi}. Bucket size: ${bucket_size}, Count: ${bucket_count}`, s);
    
    for (let x of nums) {
        let idx = Math.floor((x - lo) / bucket_size);
        s.curr_num = x;
        s.curr_bucket = idx;
        
        if (s.bucket_min[idx] === null || x < s.bucket_min[idx]) s.bucket_min[idx] = x;
        if (s.bucket_max[idx] === null || x > s.bucket_max[idx]) s.bucket_max[idx] = x;
        
        snap(14, `Place ${x} into bucket ${idx}. Min of bucket: ${s.bucket_min[idx]}, Max of bucket: ${s.bucket_max[idx]}.`, s);
    }
    
    s.curr_num = null;
    s.curr_bucket = null;
    s.prev_max = lo;
    s.max_gap = 0;
    
    snap(17, `Finished placing numbers. Now iterate through buckets to find max gap.`, s);
    
    for (let i = 0; i < bucket_count; i++) {
        if (s.bucket_min[i] === null) continue;
        s.curr_bucket = i;
        
        let gap = s.bucket_min[i] - s.prev_max;
        s.curr_gap = gap;
        if (gap > s.max_gap) {
            s.max_gap = gap;
            snap(20, `Bucket ${i} min is ${s.bucket_min[i]}. Gap with prev_max (${s.prev_max}) is ${gap}. NEW MAX GAP!`, s);
        } else {
            snap(20, `Bucket ${i} min is ${s.bucket_min[i]}. Gap with prev_max (${s.prev_max}) is ${gap}.`, s);
        }
        
        s.prev_max = s.bucket_max[i];
    }
    
    s.curr_bucket = null;
    snap(22, `Final max gap is ${s.max_gap}.`, s);
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.bucket_min.map((_, i) => {
        let minV = state.bucket_min[i];
        let maxV = state.bucket_max[i];
        let isCurr = state.curr_bucket === i;
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:60px; padding:5px; border:2px solid ${isCurr ? 'var(--accent)' : 'var(--border)'}; border-radius:4px; background:var(--surface);">
            <div style="font-size:12px; color:var(--text-dim);">B ${i}</div>
            <div style="font-size:14px; font-weight:bold; color:#34d399; margin-top:5px;">${minV !== null ? minV : '-'}</div>
            <div style="font-size:14px; font-weight:bold; color:#f43f5e;">${maxV !== null ? maxV : '-'}</div>
        </div>`;
    }).join('');
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:20px;">
        ${state.curr_num !== null ? `<div style="font-size:16px;">Current Num: <span style="font-weight:bold; color:var(--accent);">${state.curr_num}</span></div>` : ''}
        
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <div style="display:flex; flex-direction:column; justify-content:center; padding-right:10px;">
                <div style="font-size:12px; color:var(--text-dim);">&nbsp;</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:5px;">Min</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:3px;">Max</div>
            </div>
            ${boxes}
        </div>
        
        <div style="display:flex; flex-direction:column; gap:5px;">
            <div>Prev Max: <span style="font-weight:bold;">${state.prev_max !== null ? state.prev_max : '-'}</span></div>
            <div>Current Gap: <span style="font-weight:bold;">${state.curr_gap !== null ? state.curr_gap : '-'}</span></div>
            <div style="font-size:18px;">Max Gap: <span style="font-weight:bold; color:var(--accent);">${state.max_gap}</span></div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Count of Smaller Numbers After Self', short: 'Count Smaller',
  idea: 'Merge Sort based. We sort an array of (value, original_index). During the merge step, when an element from the left half is added to the merged array, the number of elements already added from the right half is exactly the number of smaller elements to its right.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '5, 2, 6, 1', hint: 'comma-separated integers',
  code: [
    'def countSmaller(nums):',
    '    counts = [0] * len(nums)',
    '    arr = [(v, i) for i, v in enumerate(nums)]',
    '    ',
    '    def merge_sort(arr):',
    '        if len(arr) <= 1: return arr',
    '        mid = len(arr) // 2',
    '        left = merge_sort(arr[:mid])',
    '        right = merge_sort(arr[mid:])',
    '        ',
    '        merged = []',
    '        i = j = 0',
    '        while i < len(left) and j < len(right):',
    '            if left[i][0] <= right[j][0]:',
    '                counts[left[i][1]] += j',
    '                merged.append(left[i])',
    '                i += 1',
    '            else:',
    '                merged.append(right[j])',
    '                j += 1',
    '        while i < len(left):',
    '            counts[left[i][1]] += j',
    '            merged.append(left[i])',
    '            i += 1',
    '        merged.extend(right[j:])',
    '        return merged',
    '        ',
    '    merge_sort(arr)',
    '    return counts'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], counts: new Array(nums.length).fill(0), arr: nums.map((v, i) => ({v, i})), action: 'Start', left: [], right: [], merged: [], current_i: null, current_j: null };
    
    function merge_sort(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.floor(arr.length / 2);
        
        let left = merge_sort(arr.slice(0, mid), lLevel + 1);
        let right = merge_sort(arr.slice(mid), lLevel + 1);
        
        let merged = [];
        let i = 0, j = 0;
        
        s.action = `Merging Arrays`;
        s.left = [...left];
        s.right = [...right];
        s.merged = [];
        s.current_i = i;
        s.current_j = j;
        snap(10, `Merging left: [${left.map(x=>x.v).join(',')}] and right: [${right.map(x=>x.v).join(',')}]`, s);
        
        while (i < left.length && j < right.length) {
            s.current_i = i;
            s.current_j = j;
            if (left[i].v <= right[j].v) {
                s.counts[left[i].i] += j;
                merged.push(left[i]);
                snap(15, `left[${i}] (${left[i].v}) <= right[${j}] (${right[j].v}). Add to counts[${left[i].i}] += ${j} (elements taken from right).`, s);
                i++;
            } else {
                merged.push(right[j]);
                snap(19, `left[${i}] (${left[i].v}) > right[${j}] (${right[j].v}). Take from right.`, s);
                j++;
            }
            s.merged = [...merged];
        }
        
        while (i < left.length) {
            s.current_i = i;
            s.current_j = j;
            s.counts[left[i].i] += j;
            merged.push(left[i]);
            snap(23, `Take remaining from left: ${left[i].v}. Add to counts[${left[i].i}] += ${j}.`, s);
            i++;
            s.merged = [...merged];
        }
        
        while (j < right.length) {
            merged.push(right[j]);
            j++;
        }
        s.merged = [...merged];
        
        s.current_i = null;
        s.current_j = null;
        snap(26, `Merge segment complete.`, s);
        return merged;
    }
    
    snap(3, `Start merge sort. Initial counts: [${s.counts.join(', ')}]`, s);
    merge_sort(s.arr, 0);
    
    s.action = 'Finished Sorting';
    s.left = [];
    s.right = [];
    snap(29, `Merge sort complete. Final counts: [${s.counts.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        
        <div style="display:flex; gap:20px;">
            <div style="display:flex; flex-direction:column;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Left</div>
                <div style="display:flex; gap:5px;">
                    ${state.left.map((item, i) => {
                        let bg = state.current_i === i ? 'var(--accent)' : 'var(--surface)';
                        let col = state.current_i === i ? '#000' : 'var(--text-color)';
                        return `<div style="padding:5px 10px; border:1px solid var(--border); background:${bg}; color:${col}; border-radius:4px; text-align:center;">
                            <div style="font-weight:bold;">${item.v}</div>
                            <div style="font-size:10px; color:${state.current_i===i?'#333':'var(--text-dim)'};">idx ${item.i}</div>
                        </div>`;
                    }).join('') || '<span style="color:var(--text-dim);">empty</span>'}
                </div>
            </div>
            
            <div style="display:flex; flex-direction:column;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Right</div>
                <div style="display:flex; gap:5px;">
                    ${state.right.map((item, j) => {
                        let bg = state.current_j === j ? '#f43f5e' : 'var(--surface)';
                        let col = state.current_j === j ? '#fff' : 'var(--text-color)';
                        return `<div style="padding:5px 10px; border:1px solid var(--border); background:${bg}; color:${col}; border-radius:4px; text-align:center;">
                            <div style="font-weight:bold;">${item.v}</div>
                            <div style="font-size:10px; color:${state.current_j===j?'#ffccd5':'var(--text-dim)'};">idx ${item.i}</div>
                        </div>`;
                    }).join('') || '<span style="color:var(--text-dim);">empty</span>'}
                </div>
            </div>
        </div>
        
        <div style="display:flex; flex-direction:column; margin-top:10px;">
            <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Merged</div>
            <div style="display:flex; gap:5px;">
                ${state.merged.map((item) => `<div style="padding:5px 10px; border:1px solid var(--border); background:var(--surface); border-radius:4px; text-align:center; opacity:0.8;">
                    <div style="font-weight:bold;">${item.v}</div>
                    <div style="font-size:10px; color:var(--text-dim);">idx ${item.i}</div>
                </div>`).join('') || '<span style="color:var(--text-dim);">empty</span>'}
            </div>
        </div>
        
        <div style="margin-top:20px;">
            <div style="font-size:14px; margin-bottom:10px;">Counts Array (Result):</div>
            <div style="display:flex; gap:5px;">
                ${state.counts.map((c, i) => `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
                    <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:2px solid #34d399; background:var(--surface); border-radius:4px; font-weight:bold;">
                        ${c}
                    </div>
                    <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">idx ${i}</div>
                </div>`).join('')}
            </div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done chunk 4")
