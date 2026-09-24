content = """
defineAlgo('22_sorting_algorithms', {
  title: 'Largest Number', short: 'Largest Number',
  idea: 'Sort strings by a custom comparator where `a + b > b + a` ensures the optimal concatenation.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '3, 30, 34, 5, 9', hint: 'comma-separated integers',
  code: [
    'class Solution:',
    '    def largestNumber(self, nums: List[int]) -> str:',
    '        nums_str = [str(n) for n in nums]',
    '        nums_str.sort(key=cmp_to_key(lambda a, b: -1 if a+b > b+a else (1 if a+b < b+a else 0)))',
    '        if nums_str[0] == "0":',
    '            return "0"',
    '        return "".join(nums_str)'
  ],
  parse(str) {
    return { nums: str.split(',').map(s => s.trim()).filter(s => s) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], compare: null, res: "" };
    
    snap(3, 'Convert all numbers to strings and begin custom sorting.', s);
    
    // Bubble sort for visualization purposes to show comparisons
    let arr = [...nums];
    for (let i = 0; i < arr.length; i++) {
        for (let j = 0; j < arr.length - 1 - i; j++) {
            let a = arr[j], b = arr[j+1];
            s.nums = [...arr];
            s.compare = { a, b, ab: a+b, ba: b+a, idx_a: j, idx_b: j+1, swap: false };
            
            if (a + b < b + a) {
                s.compare.swap = true;
                snap(4, `Compare '${a}' and '${b}': '${a+b}' < '${b+a}', so '${b}' should come first. Swap.`, s);
                let temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
                s.nums = [...arr];
                snap(4, `Swapped.`, s);
            } else {
                s.compare.swap = false;
                snap(4, `Compare '${a}' and '${b}': '${a+b}' >= '${b+a}', so order is correct.`, s);
            }
        }
    }
    
    s.compare = null;
    s.nums = [...arr];
    
    if (s.nums[0] === '0') {
        s.res = "0";
        snap(5, 'Array is sorted. Leading digit is 0, so result is "0".', s);
    } else {
        s.res = s.nums.join("");
        snap(7, `Array is sorted. Concatenate all elements.`, s);
    }
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.nums.map((val, i) => {
        let isComparing = state.compare && (state.compare.idx_a === i || state.compare.idx_b === i);
        let bg = isComparing ? 'var(--accent)' : 'var(--surface)';
        let color = isComparing ? '#000' : 'var(--text-color)';
        return `<div style="padding:10px; border:1px solid var(--border); border-radius:4px; background:${bg}; color:${color}; font-weight:bold; font-size:16px;">
            ${val}
        </div>`;
    }).join('');
    
    let compareHtml = '';
    if (state.compare) {
        let c = state.compare;
        compareHtml = `
            <div style="margin-top:20px; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:10px;">Comparison:</div>
                <div style="display:flex; justify-content:space-around; text-align:center;">
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">a + b</div>
                        <div style="font-weight:bold;">${c.ab}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">b + a</div>
                        <div style="font-weight:bold;">${c.ba}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">Action</div>
                        <div style="font-weight:bold; color:${c.swap ? '#ef4444' : '#34d399'};">${c.swap ? 'Swap' : 'Keep'}</div>
                    </div>
                </div>
            </div>`;
    }
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:10px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap;">${boxes}</div>
        ${compareHtml}
        ${state.res ? `<div style="margin-top:20px; font-size:16px;">Result: <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>` : ''}
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'H-Index', short: 'H-Index',
  idea: 'Sort citations descending. Linearly scan; as long as citations[i] >= i + 1, we can form an h-index of i + 1.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '3,0,6,1,5', hint: 'comma-separated citation counts',
  code: [
    'def hIndex(citations):',
    '    citations = sorted(citations, reverse=True)',
    '    h = 0',
    '    for i, c in enumerate(citations):',
    '        if c >= i + 1:',
    '            h = i + 1',
    '        else:',
    '            break',
    '    return h'
  ],
  parse(str) {
    return { citations: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ citations }) {
    const { F, snap } = avRecorder();
    let s = { citations: [...citations], sorted: false, i: null, h: 0 };
    
    snap(1, 'Initial unsorted citations array.', s);
    
    s.citations.sort((a, b) => b - a);
    s.sorted = true;
    snap(2, 'Sort citations in descending order.', s);
    
    for (let i = 0; i < s.citations.length; i++) {
        s.i = i;
        let c = s.citations[i];
        snap(4, `Examine paper at index ${i} with ${c} citations. Require ${c} >= ${i + 1} (index + 1) for an h-index of ${i + 1}.`, s);
        
        if (c >= i + 1) {
            s.h = i + 1;
            snap(6, `Condition met! c (${c}) >= ${i + 1}. Current best h-index = ${s.h}.`, s);
        } else {
            snap(8, `Condition failed! c (${c}) < ${i + 1}. Stop here.`, s);
            break;
        }
    }
    
    s.i = null;
    snap(9, `Return final h-index = ${s.h}.`, s);
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.citations.map((c, i) => {
        let isCurrent = state.i === i;
        let bg = isCurrent ? 'var(--accent)' : 'var(--surface)';
        let color = isCurrent ? '#000' : 'var(--text-color)';
        let label = (state.sorted && c >= i + 1 && (state.i === null || state.i >= i)) ? `<div style="color:#34d399; font-size:12px;">Valid</div>` : '';
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:50px;">
            <div style="height:20px;">${label}</div>
            <div style="width:100%; height:50px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); background:${bg}; color:${color}; font-weight:bold; font-size:18px; border-radius:4px;">
                ${c}
            </div>
            <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">idx ${i}</div>
            <div style="font-size:11px; color:var(--text-dim);">Req >= ${i+1}</div>
        </div>`;
    }).join('');
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:20px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap;">${boxes}</div>
        <div style="font-size:18px;">Current h: <span style="font-weight:bold; color:var(--accent);">${state.h}</span></div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done chunk 3")
