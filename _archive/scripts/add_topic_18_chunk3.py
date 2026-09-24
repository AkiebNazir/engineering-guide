import sys

content = """
defineAlgo('18_greedy', {
  title: 'Merge Triplets to Form Target Triplet', short: 'Merge Triplets',
  idea: 'We can merge any triplets by taking element-wise max. A triplet is usable ONLY if all its elements are <= target elements. We greedily merge all usable triplets and check if the result equals target.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,5,3; 1,8,4; 1,7,5; 2,7,5| 2,7,5', hint: 'triplets split by ; | target',
  code: [
    'def mergeTriplets(triplets, target):',
    '    res = [0, 0, 0]',
    '    for t in triplets:',
    '        if t[0] <= target[0] and t[1] <= target[1] and t[2] <= target[2]:',
    '            res[0] = max(res[0], t[0])',
    '            res[1] = max(res[1], t[1])',
    '            res[2] = max(res[2], t[2])',
    '            ',
    '    return res == target'
  ],
  parse(str) {
    const parts = str.split('|');
    const triplets = parts[0].split(';').map(t => t.split(',').map(Number));
    const target = parts[1].split(',').map(Number);
    return { triplets, target };
  },
  run({ triplets, target }) {
    const { F, snap } = avRecorder();
    let res = [0, 0, 0];
    const s = { triplets, target, res: [...res], curT: null };
    
    snap(2, 'Initialize result to [0, 0, 0]', s);
    
    for (let i = 0; i < triplets.length; i++) {
       const t = triplets[i];
       s.curT = t;
       
       if (t[0] <= target[0] && t[1] <= target[1] && t[2] <= target[2]) {
          res[0] = Math.max(res[0], t[0]);
          res[1] = Math.max(res[1], t[1]);
          res[2] = Math.max(res[2], t[2]);
          s.res = [...res];
          snap(5, `Triplet [${t}] is usable (all elements <= target). Merge it! Current max = [${res}]`, s);
       } else {
          snap(4, `Triplet [${t}] has an element > target. Discard it.`, s);
       }
    }
    
    s.curT = null;
    const match = res[0] === target[0] && res[1] === target[1] && res[2] === target[2];
    snap(8, `Final max = [${res}]. Target = [${target}]. Matches? ${match}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>Target: <span style="font-weight:bold; color:var(--text);">[${state.target}]</span></div>
        <div>Current Max: <span style="font-weight:bold; color:var(--accent);">[${state.res}]</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let i=0; i<state.triplets.length; i++) {
       const t = state.triplets[i];
       const isValid = t[0]<=state.target[0] && t[1]<=state.target[1] && t[2]<=state.target[2];
       const isCurr = state.curT === t;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = 'var(--surface)';
       if (isCurr && isValid) bg = 'rgba(52,211,153,0.2)';
       else if (isCurr && !isValid) bg = 'rgba(239,68,68,0.2)';
       
       html += `<div style="padding:8px; border:${border}; background:${bg}; font-family:var(--mono); width:max-content; border-radius:6px;">
          [${t[0]}, ${t[1]}, ${t[2]}] ${isCurr ? (isValid ? '✓ Valid' : '✗ Invalid') : ''}
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Partition Labels', short: 'Partition Labels',
  idea: 'Greedy. Find the last occurrence index for every char. Iterate through string, keeping a running `end = max(end, last_occurrence[char])`. When `i == end`, partition here.',
  complexity: 'Time O(N) · Space O(1) (26 chars max)',
  input: 'ababcbacadefegdehijhklij', hint: 'string s',
  code: [
    'def partitionLabels(s):',
    '    last = {c: i for i, c in enumerate(s)}',
    '    res = []',
    '    size = 0',
    '    end = 0',
    '    ',
    '    for i, c in enumerate(s):',
    '        size += 1',
    '        end = max(end, last[c])',
    '        ',
    '        if i == end:',
    '            res.append(size)',
    '            size = 0',
    '            ',
    '    return res'
  ],
  parse(str) {
    return { s_str: str.trim(), n: str.trim().length };
  },
  run({ s_str, n }) {
    const { F, snap } = avRecorder();
    let last = {};
    for (let i = 0; i < n; i++) last[s_str[i]] = i;
    
    let res = [];
    let size = 0, end = 0;
    
    const s = { s_str, n, last, res: [...res], size, end, i: null };
    snap(2, 'Compute last occurrence index for each character.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       size++;
       s.size = size;
       
       const charLast = last[s_str[i]];
       end = Math.max(end, charLast);
       s.end = end;
       
       snap(7, `Char '${s_str[i]}' last seen at ${charLast}. Boundary extends to max(end, ${charLast}) = ${end}.`, s);
       
       if (i === end) {
          res.push(size);
          s.res = [...res];
          snap(10, `i == end (${i}). We can safely partition here. Partition size = ${size}.`, s);
          size = 0;
          s.size = size;
       }
    }
    
    s.i = null;
    snap(12, `Finished. Partitions = [${res.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:14px;">
        <div>Required End Boundary: <span style="font-weight:bold; color:#ef4444;">${state.end}</span></div>
        <div>Current Partitions: <span style="font-weight:bold; color:var(--accent);">[${state.res.join(', ')}]</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:2px; font-family:var(--mono);">';
    let currentPartLen = 0;
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let isEnd = state.end === i;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       if (isEnd) border = '2px solid #ef4444';
       
       let bg = 'var(--surface)';
       if (i <= state.end && state.i !== null) bg = 'rgba(239,68,68,0.1)';
       
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:9px; color:var(--text-dim); margin-bottom:1px;">${i}</div>
          <div style="width:24px; height:24px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold; font-size:12px;">${state.s_str[i]}</div>
          <div style="font-size:9px; color:var(--accent); margin-top:1px;">${state.last[state.s_str[i]]}</div>
       </div>`;
    }
    html += '</div>';
    html += '<div style="margin-top:10px; font-size:11px; color:var(--text-dim); font-family:var(--mono);">Top number = index. Box = character. Bottom number = last occurrence of this char.</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Valid Parenthesis String', short: 'Valid Parenthesis (*)',
  idea: 'Keep track of `min_open` and `max_open` possible open brackets. `(` increments both. `)` decrements both. `*` decrements `min` and increments `max`. `min_open` cannot be < 0. If `max_open < 0`, string is invalid.',
  complexity: 'Time O(N) · Space O(1)',
  input: '(*))', hint: 'string of (, ), and *',
  code: [
    'def checkValidString(s):',
    '    min_open = 0',
    '    max_open = 0',
    '    ',
    '    for c in s:',
    '        if c == "(": ',
    '            min_open += 1',
    '            max_open += 1',
    '        elif c == ")":',
    '            min_open -= 1',
    '            max_open -= 1',
    '        else:',
    '            min_open -= 1',
    '            max_open += 1',
    '            ',
    '        if max_open < 0:',
    '            return False',
    '        min_open = max(min_open, 0)',
    '        ',
    '    return min_open == 0'
  ],
  parse(str) {
    return { str: str.trim(), n: str.trim().length };
  },
  run({ str, n }) {
    const { F, snap } = avRecorder();
    let min_open = 0, max_open = 0;
    const s = { str, n, min_open, max_open, i: null };
    
    snap(3, 'Initialize min_open=0, max_open=0.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       const c = str[i];
       
       if (c === '(') {
          min_open++; max_open++;
          s.min_open = min_open; s.max_open = max_open;
          snap(6, `Char is '('. Both min and max increment.`, s);
       } else if (c === ')') {
          min_open--; max_open--;
          s.min_open = min_open; s.max_open = max_open;
          snap(9, `Char is ')'. Both min and max decrement.`, s);
       } else {
          min_open--; max_open++;
          s.min_open = min_open; s.max_open = max_open;
          snap(12, `Char is '*'. It can be ')', empty, or '('. Min decrements, Max increments.`, s);
       }
       
       if (max_open < 0) {
          snap(14, `max_open < 0. Too many closing brackets! Return False.`, s);
          return F;
       }
       if (min_open < 0) {
          min_open = 0;
          s.min_open = min_open;
          snap(16, `min_open went below 0. We cannot have negative open brackets, so we clip it to 0.`, s);
       }
    }
    
    s.i = null;
    snap(18, `Finished. min_open == 0? ${min_open === 0}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>min_open: <span style="font-weight:bold; color:var(--text);">${state.min_open}</span></div>
        <div>max_open: <span style="font-weight:bold; color:var(--text);">${state.max_open}</span></div>
    </div>`;
    
    html += '<div style="display:flex; gap:4px; font-family:var(--mono); font-size:24px;">';
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let color = state.str[i] === '*' ? '#38bdf8' : 'var(--text)';
       let border = isCurr ? '2px solid var(--accent)' : '2px solid transparent';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; color:${color}; font-weight:bold; border:${border}; border-radius:6px; background:var(--surface);">${state.str[i]}</div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 18 chunk 3.")
