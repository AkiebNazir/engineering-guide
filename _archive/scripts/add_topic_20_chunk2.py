import sys

content = """
defineAlgo('20_bit_manipulation', {
  title: 'Missing Number', short: 'Missing Number',
  idea: 'XOR all numbers from 0 to N and all elements in the array. All present numbers will cancel out, leaving the missing number.',
  complexity: 'Time O(N) · Space O(1)',
  input: '3, 0, 1', hint: 'comma-separated numbers',
  code: [
    'def missingNumber(nums):',
    '    res = len(nums)',
    '    for i, num in enumerate(nums):',
    '        res ^= i ^ num',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let res = nums.length;
    const s = { nums, res, i: null };
    
    snap(2, `Initialize res = N = ${res}.`, s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       const oldRes = res;
       res ^= i;
       res ^= nums[i];
       s.res = res;
       snap(4, `XOR with index ${i} and num ${nums[i]}: ${oldRes} ^ ${i} ^ ${nums[i]} = ${res}.`, s);
    }
    
    s.i = null;
    snap(5, `Finished. The missing number is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:20px; font-size:18px;">
        Current XOR Sum: <span style="font-weight:bold; color:var(--accent);">${state.res}</span>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-size:10px; color:var(--text-dim);">idx=${i}</div>
          <div style="font-weight:bold; font-size:16px;">${state.nums[i]}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Sum of Two Integers', short: 'Sum (No +)',
  idea: 'Use `a ^ b` for addition without carry. Use `(a & b) << 1` for the carry. Repeat until carry is 0.',
  complexity: 'Time O(1) · Space O(1)',
  input: '1, 2', hint: 'a, b',
  code: [
    'def getSum(a, b):',
    '    mask = 0xFFFFFFFF',
    '    while b != 0:',
    '        carry = (a & b) & mask',
    '        a = (a ^ b) & mask',
    '        b = (carry << 1) & mask',
    '    return a if a <= 0x7FFFFFFF else ~(a ^ mask)'
  ],
  parse(str) {
    const parts = str.split(',');
    return { a: parseInt(parts[0]), b: parseInt(parts[1]) };
  },
  run({ a, b }) {
    const { F, snap } = avRecorder();
    let currentA = a, currentB = b;
    const s = { a, b, currentA, currentB };
    
    snap(2, `Initialize a=${a}, b=${b}.`, s);
    
    let iterations = 0;
    while (currentB !== 0 && iterations < 32) {
       let carry = currentA & currentB;
       currentA = currentA ^ currentB;
       currentB = carry << 1;
       
       // simulate 32-bit integer overflow for JS
       currentA = currentA | 0;
       currentB = currentB | 0;
       
       s.currentA = currentA; s.currentB = currentB;
       snap(5, `carry = (a & b) << 1 = ${currentB}. a = a ^ b = ${currentA}.`, s);
       iterations++;
    }
    
    snap(6, `Finished. Sum = ${currentA}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(8,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:18px;">
        <div>A: <span style="font-weight:bold; color:var(--accent);">${state.currentA}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.currentA)})</span></div>
        <div>B (Carry): <span style="font-weight:bold; color:#ef4444;">${state.currentB}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.currentB)})</span></div>
    </div>`;
    
    if (state.currentB === 0) {
       html += `<div style="margin-top:20px; font-weight:bold; color:#34d399;">Result: ${state.currentA}</div>`;
    }
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Reverse Integer', short: 'Reverse Int',
  idea: 'Pop the last digit using `% 10` and push it to `res = res * 10 + digit`. Handle 32-bit integer overflow.',
  complexity: 'Time O(log(x)) · Space O(1)',
  input: '123', hint: 'integer',
  code: [
    'def reverse(x):',
    '    res = 0',
    '    sign = -1 if x < 0 else 1',
    '    x = abs(x)',
    '    ',
    '    while x:',
    '        digit = x % 10',
    '        x //= 10',
    '        if res > (2**31 - 1 - digit) // 10:',
    '            return 0',
    '        res = res * 10 + digit',
    '        ',
    '    return sign * res'
  ],
  parse(str) {
    return { x: parseInt(str.trim()) };
  },
  run({ x }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let sign = x < 0 ? -1 : 1;
    let curr = Math.abs(x);
    
    const s = { x, curr, res, sign, digit: null };
    snap(4, `Initialize res = 0, sign = ${sign}.`, s);
    
    while (curr > 0) {
       let digit = curr % 10;
       curr = Math.floor(curr / 10);
       
       if (res > Math.floor((2**31 - 1 - digit) / 10)) {
          snap(10, 'Integer overflow detected! Return 0.', s);
          return F;
       }
       
       res = res * 10 + digit;
       s.curr = curr; s.res = res; s.digit = digit;
       snap(11, `Pop digit ${digit}. res = res * 10 + digit = ${res}. x = ${curr}.`, s);
    }
    
    res *= sign;
    s.res = res; s.digit = null;
    snap(13, `Finished. Result = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:30px; font-family:var(--mono); font-size:18px;">
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Remaining X</div>
           <div style="font-weight:bold;">${state.curr}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Popped Digit</div>
           <div style="font-weight:bold; color:#ef4444;">${state.digit !== null ? state.digit : '-'}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Reversed (res)</div>
           <div style="font-weight:bold; color:var(--accent);">${state.res}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 20 chunk 2.")
