content = """
defineAlgo('22_sorting_algorithms', {
  title: 'Merge Sorted Array', short: 'Merge Arrays',
  idea: 'Use three pointers starting from the end of both arrays to merge them in-place into nums1 without extra space.',
  complexity: 'Time O(m + n) · Space O(1)',
  input: '[1,2,3,0,0,0], 3, [2,5,6], 3', hint: 'nums1, m, nums2, n',
  code: [
    'def merge(nums1, m, nums2, n):',
    '    p1 = m - 1',
    '    p2 = n - 1',
    '    p = m + n - 1',
    '    while p1 >= 0 and p2 >= 0:',
    '        if nums1[p1] > nums2[p2]:',
    '            nums1[p] = nums1[p1]',
    '            p1 -= 1',
    '        else:',
    '            nums1[p] = nums2[p2]',
    '            p2 -= 1',
    '        p -= 1',
    '    while p2 >= 0:',
    '        nums1[p] = nums2[p2]',
    '        p2 -= 1',
    '        p -= 1'
  ],
  parse(str) {
    let parts = str.split('],');
    if (parts.length < 2) return { nums1: [1,2,3,0,0,0], m: 3, nums2: [2,5,6], n: 3 };
    let n1_str = parts[0].replace('[', '').trim();
    let nums1 = n1_str ? n1_str.split(',').map(Number) : [];
    
    let rem = parts[1].split(',[');
    let m = parseInt(rem[0].trim());
    
    let n2_str = rem[1] ? rem[1].replace(']', '').trim() : '';
    let nums2 = n2_str ? n2_str.split(',').map(Number) : [];
    
    let n = parseInt(parts[2] || (rem[2] ? rem[2] : nums2.length));
    
    return { nums1, m, nums2, n };
  },
  run({ nums1, m, nums2, n }) {
    const { F, snap } = avRecorder();
    let s = { nums1: [...nums1], nums2: [...nums2], m, n, p1: m - 1, p2: n - 1, p: m + n - 1 };
    
    snap(2, 'Initialize pointers at the end of the arrays.', s);
    
    while (s.p1 >= 0 && s.p2 >= 0) {
        snap(4, `Compare nums1[p1] (${s.nums1[s.p1]}) and nums2[p2] (${s.nums2[s.p2]}).`, s);
        if (s.nums1[s.p1] > s.nums2[s.p2]) {
            s.nums1[s.p] = s.nums1[s.p1];
            snap(6, `nums1[p1] is larger, place it at nums1[p] (index ${s.p}).`, s);
            s.p1--;
        } else {
            s.nums1[s.p] = s.nums2[s.p2];
            snap(9, `nums2[p2] is larger or equal, place it at nums1[p] (index ${s.p}).`, s);
            s.p2--;
        }
        s.p--;
    }
    
    while (s.p2 >= 0) {
        s.nums1[s.p] = s.nums2[s.p2];
        snap(13, `Copy remaining elements from nums2. Placed ${s.nums2[s.p2]} at index ${s.p}.`, s);
        s.p2--;
        s.p--;
    }
    
    snap(16, 'Merge complete.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let renderArray = (arr, title, ptr1, ptr1Name, ptr1Color, ptr2, ptr2Name, ptr2Color) => {
        let boxes = arr.map((val, i) => {
            let bg = 'var(--surface)';
            let borderColor = 'var(--border)';
            let labels = [];
            if (i === ptr1) {
                borderColor = ptr1Color;
                labels.push(`<div style="color:${ptr1Color}; font-size:12px; font-weight:bold;">${ptr1Name}</div>`);
            }
            if (ptr2 !== undefined && i === ptr2) {
                borderColor = ptr2Color;
                labels.push(`<div style="color:${ptr2Color}; font-size:12px; font-weight:bold;">${ptr2Name}</div>`);
            }
            return `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
                ${labels.join('')}
                <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:2px solid ${borderColor}; background:${bg}; border-radius:4px; font-weight:bold;">
                    ${val !== undefined && val !== null ? val : ''}
                </div>
                <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">${i}</div>
            </div>`;
        }).join('');
        return `<div>
            <div style="font-size:14px; color:var(--text-dim); margin-bottom:10px;">${title}</div>
            <div style="display:flex; gap:5px;">${boxes}</div>
        </div>`;
    };
    
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        ${renderArray(state.nums1, 'nums1', state.p1, 'p1', 'var(--accent)', state.p, 'p', '#34d399')}
        ${renderArray(state.nums2, 'nums2', state.p2, 'p2', '#f43f5e')}
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Sort an Array', short: 'Merge Sort',
  idea: 'Divide the array in halves recursively, then merge the sorted halves.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '5, 2, 3, 1', hint: 'comma-separated integers',
  code: [
    'def sortArray(nums):',
    '    if len(nums) <= 1:',
    '        return nums',
    '    mid = len(nums) // 2',
    '    left = sortArray(nums[:mid])',
    '    right = sortArray(nums[mid:])',
    '    return merge(left, right)',
    '',
    'def merge(left, right):',
    '    res = []',
    '    i = j = 0',
    '    while i < len(left) and j < len(right):',
    '        if left[i] < right[j]:',
    '            res.append(left[i])',
    '            i += 1',
    '        else:',
    '            res.append(right[j])',
    '            j += 1',
    '    res.extend(left[i:])',
    '    res.extend(right[j:])',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { currArr: [...nums], subArrays: [[...nums]], level: 0, action: 'Start' };
    
    function mergeSort(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.floor(arr.length / 2);
        
        s.action = `Splitting array of size ${arr.length}`;
        s.currArr = [...arr];
        s.level = lLevel;
        snap(4, `Split array: [${arr.join(', ')}]`, s);
        
        let left = mergeSort(arr.slice(0, mid), lLevel + 1);
        let right = mergeSort(arr.slice(mid), lLevel + 1);
        
        return mergeArrays(left, right, lLevel);
    }
    
    function mergeArrays(left, right, lLevel) {
        let res = [];
        let i = 0, j = 0;
        
        s.action = `Merging [${left.join(', ')}] and [${right.join(', ')}]`;
        s.level = lLevel;
        snap(9, `Merging two halves.`, s);
        
        while (i < left.length && j < right.length) {
            if (left[i] < right[j]) {
                res.push(left[i]);
                i++;
            } else {
                res.push(right[j]);
                j++;
            }
        }
        res = res.concat(left.slice(i)).concat(right.slice(j));
        
        s.action = `Merged Result: [${res.join(', ')}]`;
        s.currArr = [...res];
        s.level = lLevel;
        snap(19, `Merge complete.`, s);
        return res;
    }
    
    mergeSort(nums, 0);
    s.action = 'Finished Sorting';
    snap(7, 'Array is completely sorted.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        <div style="font-size:14px; color:var(--text-dim);">Recursion Level: ${state.level}</div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            ${state.currArr.map(x => `<div style="padding:10px 15px; border:1px solid var(--border); border-radius:4px; background:var(--surface); font-weight:bold; font-size:18px;">${x}</div>`).join('')}
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done chunk 1")
