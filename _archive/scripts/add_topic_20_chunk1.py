import sys

content = """
defineAlgo('20_bit_manipulation', {
  title: 'Single Number', short: 'Single Number',
  idea: 'XOR all numbers. Since `x ^ x = 0` and `x ^ 0 = x`, all pairs cancel out, leaving only the single number.',
  complexity: 'Time O(N) · Space O(1)',
  input: '4, 1, 2, 1, 2', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    res = 0',
    '    for n in nums:',
    '        res ^= n',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let res = 0;
    const s = { nums, res, i: null };
    
    snap(2, 'Initialize res = 0', s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       const oldRes = res;
       res ^= nums[i];
       s.res = res;
       snap(4, `XOR with ${nums[i]}: ${oldRes} ^ ${nums[i]} = ${res}. In binary: ${oldRes.toString(2).padStart(4,'0')} ^ ${nums[i].toString(2).padStart(4,'0')} = ${res.toString(2).padStart(4,'0')}`, s);
    }
    
    s.i = null;
    snap(5, `Finished. Pairs cancelled out. The single number is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:20px;">
        <div style="font-size:18px;">Current XOR Sum: <span style="font-weight:bold; color:var(--accent);">${state.res}</span> <span style="color:var(--text-dim); font-size:14px;">(${state.res.toString(2).padStart(8,'0')})</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-weight:bold; font-size:16px;">${state.nums[i]}</div>
          <div style="font-size:10px; color:var(--text-dim); font-family:var(--mono);">${state.nums[i].toString(2).padStart(4,'0')}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Number of 1 Bits', short: 'Count 1s',
  idea: 'Use `n &= (n - 1)` to clear the lowest set bit in each iteration. Count how many times we do this until `n == 0`.',
  complexity: 'Time O(1) (max 32 ops) · Space O(1)',
  input: '11', hint: 'integer (e.g. 11 for binary 1011)',
  code: [
    'def hammingWeight(n):',
    '    res = 0',
    '    while n:',
    '        n &= (n - 1)',
    '        res += 1',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let curr = n;
    const s = { n, curr, res };
    
    snap(2, `Initialize count = 0. Current number = ${curr} (binary: ${curr.toString(2).padStart(8,'0')}).`, s);
    
    while (curr > 0) {
       const prev = curr;
       curr &= (curr - 1);
       res += 1;
       s.curr = curr; s.res = res;
       snap(5, `n = n & (n - 1) clears the lowest 1 bit. ${prev.toString(2).padStart(8,'0')} & ${(prev-1).toString(2).padStart(8,'0')} = ${curr.toString(2).padStart(8,'0')}. Count = ${res}.`, s);
    }
    
    snap(6, `Finished. Number of 1 bits = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:20px; font-size:18px;">
        <div>Original: ${state.n}</div>
        <div>Count: <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>
    </div>`;
    
    html += `<div style="font-family:var(--mono); font-size:24px; letter-spacing:4px;">`;
    const bin = state.curr.toString(2).padStart(8,'0');
    for (let char of bin) {
       let color = char === '1' ? '#34d399' : 'var(--text-dim)';
       html += `<span style="color:${color}; font-weight:bold;">${char}</span>`;
    }
    html += `</div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Counting Bits', short: 'Counting Bits',
  idea: 'DP using bits: `dp[i] = dp[i >> 1] + (i & 1)`. The number of 1s in `i` is the number of 1s in `i / 2` plus 1 if `i` is odd.',
  complexity: 'Time O(N) · Space O(N)',
  input: '5', hint: 'integer n',
  code: [
    'def countBits(n):',
    '    dp = [0] * (n + 1)',
    '    for i in range(1, n + 1):',
    '        dp[i] = dp[i >> 1] + (i & 1)',
    '    return dp'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let dp = new Array(n + 1).fill(0);
    const s = { n, dp: [...dp], i: null };
    
    snap(2, 'Initialize dp array with 0s.', s);
    
    for (let i = 1; i <= n; i++) {
       s.i = i;
       const half = i >> 1;
       const odd = i & 1;
       dp[i] = dp[half] + odd;
       s.dp = [...dp];
       snap(4, `i = ${i} (binary ${i.toString(2)}). dp[${i}] = dp[${half}] + ${odd} = ${dp[i]}.`, s);
    }
    
    s.i = null;
    snap(5, `Finished. Result = [${dp.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-wrap:wrap; gap:8px; font-family:var(--mono);">';
    for (let i=0; i<=state.n; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px; min-width:50px;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i = ${i}</div>
          <div style="font-weight:bold; font-size:16px; color:var(--accent);">${state.dp[i]}</div>
          <div style="font-size:10px; color:var(--text-dim); margin-top:2px;">${i.toString(2).padStart(4,'0')}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Reverse Bits', short: 'Reverse Bits',
  idea: 'Iterate 32 times. Extract the lowest bit of `n` using `n & 1`. Shift `res` left and add the bit `res = (res << 1) | bit`. Shift `n` right by 1.',
  complexity: 'Time O(1) · Space O(1)',
  input: '43261596', hint: '32-bit unsigned integer',
  code: [
    'def reverseBits(n):',
    '    res = 0',
    '    for i in range(32):',
    '        bit = (n >> i) & 1',
    '        res = res | (bit << (31 - i))',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    const s = { n, res, i: null };
    
    snap(2, `Initialize res = 0. Original = ${n.toString(2).padStart(32,'0')}`, s);
    
    for (let i = 0; i < 32; i++) {
       s.i = i;
       const bit = (n >> i) & 1;
       res = (res | (bit << (31 - i))) >>> 0; // unsigned 32-bit cast
       s.res = res;
       
       if (i % 8 === 0 || i === 31) {
          snap(5, `Step ${i}: extracted bit ${bit}. res = ${res.toString(2).padStart(32,'0')}`, s);
       }
    }
    
    s.i = null;
    snap(6, `Finished. Reversed = ${res}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:10px;">`;
    
    html += `<div><div style="color:var(--text-dim); font-size:12px;">Original (n = ${state.n}):</div>`;
    html += `<div style="font-size:18px; letter-spacing:2px;">${state.n.toString(2).padStart(32,'0')}</div></div>`;
    
    html += `<div><div style="color:var(--text-dim); font-size:12px;">Reversed (res = ${state.res}):</div>`;
    html += `<div style="font-size:18px; letter-spacing:2px; color:var(--accent);">${state.res.toString(2).padStart(32,'0')}</div></div>`;
    
    if (state.i !== null) {
       html += `<div style="margin-top:10px; color:#34d399; font-weight:bold;">Iteration: ${state.i}/32</div>`;
    }
    html += `</div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 20 chunk 1.")
