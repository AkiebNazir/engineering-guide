import sys

content = """
defineAlgo('20_bit_manipulation', {
  title: 'Single Number II', short: 'Single Number II',
  idea: 'Use digital logic design. `ones` tracks bits appearing once, `twos` tracks bits appearing twice. Formula: `ones = (ones ^ n) & ~twos`, `twos = (twos ^ n) & ~ones`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 2, 3, 2', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    ones, twos = 0, 0',
    '    for n in nums:',
    '        ones = (ones ^ n) & ~twos',
    '        twos = (twos ^ n) & ~ones',
    '    return ones'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let ones = 0, twos = 0;
    const s = { nums, ones, twos, curr: null };
    
    snap(2, 'Initialize ones=0, twos=0.', s);
    
    for (const n of nums) {
       s.curr = n;
       ones = (ones ^ n) & ~twos;
       twos = (twos ^ n) & ~ones;
       
       // Force 32-bit unsigned for JS display (optional, keeps it clean)
       ones = ones >>> 0;
       twos = twos >>> 0;
       
       s.ones = ones; s.twos = twos;
       snap(5, `Process ${n}. ones = ${ones.toString(2).padStart(4,'0')}, twos = ${twos.toString(2).padStart(4,'0')}.`, s);
    }
    
    s.curr = null;
    snap(6, `Finished. The single number is in 'ones': ${ones}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(4,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div style="font-weight:bold; color:var(--text-dim);">Processing: ${state.curr !== null ? state.curr : 'None'}</div>
        <div>Ones: <span style="font-weight:bold; color:var(--accent);">${state.ones}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.ones)})</span></div>
        <div>Twos: <span style="font-weight:bold; color:#ef4444;">${state.twos}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.twos)})</span></div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Single Number III', short: 'Single Number III',
  idea: 'XOR all elements to get `a ^ b`. Find any set bit (`diff &= -diff`). Use this bit to partition numbers into two groups and XOR each group separately to isolate `a` and `b`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 2, 1, 3, 2, 5', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    xor = 0',
    '    for n in nums:',
    '        xor ^= n',
    '        ',
    '    diff = xor & -xor',
    '    ',
    '    a, b = 0, 0',
    '    for n in nums:',
    '        if n & diff:',
    '            a ^= n',
    '        else:',
    '            b ^= n',
    '            ',
    '    return [a, b]'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let xor = 0;
    for (const n of nums) xor ^= n;
    
    let diff = xor & -xor;
    let a = 0, b = 0;
    const s = { nums, xor, diff, a, b, phase: 1, curr: null };
    
    snap(6, `Phase 1: XOR all elements. Result = ${xor} (binary ${xor.toString(2).padStart(4,'0')}). This is a ^ b. Find rightmost set bit: diff = ${diff} (binary ${diff.toString(2).padStart(4,'0')}).`, s);
    
    s.phase = 2;
    for (const n of nums) {
       s.curr = n;
       if (n & diff) {
          a ^= n;
          s.a = a;
          snap(11, `n = ${n} (binary ${n.toString(2).padStart(4,'0')}) has the diff bit set. XOR into 'a'. a = ${a}.`, s);
       } else {
          b ^= n;
          s.b = b;
          snap(13, `n = ${n} (binary ${n.toString(2).padStart(4,'0')}) does NOT have the diff bit set. XOR into 'b'. b = ${b}.`, s);
       }
    }
    
    s.curr = null; s.phase = 3;
    snap(15, `Finished. The two single numbers are [${a}, ${b}].`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(4,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div style="font-weight:bold; color:var(--text-dim);">a ^ b: ${state.xor} (${toBin(state.xor)}) | Diff Bit: ${state.diff} (${toBin(state.diff)})</div>
    </div>`;
    
    html += `<div style="display:flex; gap:20px; margin-top:20px;">
        <div style="display:flex; flex-direction:column; gap:5px;">
           <div style="font-weight:bold; color:var(--accent);">Group A (bit set)</div>
           <div style="font-size:24px; font-weight:bold;">${state.a}</div>
        </div>
        <div style="display:flex; flex-direction:column; gap:5px;">
           <div style="font-weight:bold; color:#ef4444;">Group B (bit NOT set)</div>
           <div style="font-size:24px; font-weight:bold;">${state.b}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Bitwise AND of Numbers Range', short: 'AND Range',
  idea: 'The bitwise AND of a range reduces to finding the common prefix of `left` and `right`. Shift both right until they equal, keeping a count. Then shift the common prefix left by the count.',
  complexity: 'Time O(1) · Space O(1)',
  input: '5, 7', hint: 'left, right',
  code: [
    'def rangeBitwiseAnd(left, right):',
    '    shifts = 0',
    '    while left != right:',
    '        left >>= 1',
    '        right >>= 1',
    '        shifts += 1',
    '    return left << shifts'
  ],
  parse(str) {
    const parts = str.split(',');
    return { left: parseInt(parts[0]), right: parseInt(parts[1]) };
  },
  run({ left, right }) {
    const { F, snap } = avRecorder();
    let shifts = 0;
    let l = left, r = right;
    const s = { left, right, l, r, shifts };
    
    snap(2, `Initialize. We need the common prefix of left and right.`, s);
    
    while (l !== r) {
       l >>= 1;
       r >>= 1;
       shifts++;
       s.l = l; s.r = r; s.shifts = shifts;
       snap(6, `Shift right. l = ${l}, r = ${r}. Shifts = ${shifts}.`, s);
    }
    
    const res = l << shifts;
    snap(7, `They are equal! Common prefix is ${l}. Shift left by ${shifts} to restore 0s. Result = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(8,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div>Shifts: <span style="font-weight:bold; color:var(--accent);">${state.shifts}</span></div>
        <div>Current Left:  <span style="font-weight:bold; letter-spacing:2px;">${toBin(state.l)}</span></div>
        <div>Current Right: <span style="font-weight:bold; letter-spacing:2px;">${toBin(state.r)}</span></div>
    </div>`;
    
    if (state.l === state.r) {
       html += `<div style="margin-top:20px; color:#34d399; font-weight:bold; font-size:18px;">Final Result: ${state.l << state.shifts}</div>`;
    }
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 20 chunk 3.")
