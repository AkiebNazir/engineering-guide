content = """
defineAlgo('21_math_geometry', {
  title: 'Multiply Strings', short: 'Multiply',
  idea: 'Simulate grade-school multiplication. Array of size len(num1) + len(num2) stores intermediate results. Update indices i+j and i+j+1.',
  complexity: 'Time O(N*M) · Space O(N+M)',
  input: '12, 34', hint: 'num1, num2 (e.g. 12, 34)',
  code: [
    'def multiply(num1, num2):',
    '    if "0" in [num1, num2]:',
    '        return "0"',
    '    res = [0] * (len(num1) + len(num2))',
    '    num1, num2 = num1[::-1], num2[::-1]',
    '    for i1 in range(len(num1)):',
    '        for i2 in range(len(num2)):',
    '            digit = int(num1[i1]) * int(num2[i2])',
    '            res[i1 + i2] += digit',
    '            res[i1 + i2 + 1] += res[i1 + i2] // 10',
    '            res[i1 + i2] = res[i1 + i2] % 10',
    '    res, beg = res[::-1], 0',
    '    while beg < len(res) and res[beg] == 0:',
    '        beg += 1',
    '    return "".join(map(str, res[beg:]))'
  ],
  parse(str) {
    const parts = str.split(',').map(s => s.trim());
    return { num1: parts[0], num2: parts[1] };
  },
  run({ num1, num2 }) {
    const { F, snap } = avRecorder();
    
    if (num1 === '0' || num2 === '0') {
        snap(2, 'One of the numbers is zero. Result is "0".', { num1, num2, res: [0], i1: null, i2: null });
        return F;
    }
    
    let res = new Array(num1.length + num2.length).fill(0);
    const revNum1 = num1.split('').reverse().join('');
    const revNum2 = num2.split('').reverse().join('');
    
    let s = { num1: revNum1, num2: revNum2, res: [...res], i1: null, i2: null, digit: null };
    
    snap(4, 'Initialize result array of zeros.', s);
    
    for (let i1 = 0; i1 < revNum1.length; i1++) {
        for (let i2 = 0; i2 < revNum2.length; i2++) {
            s.i1 = i1;
            s.i2 = i2;
            
            const n1 = parseInt(revNum1[i1]);
            const n2 = parseInt(revNum2[i2]);
            const digit = n1 * n2;
            s.digit = digit;
            
            res[i1 + i2] += digit;
            res[i1 + i2 + 1] += Math.floor(res[i1 + i2] / 10);
            res[i1 + i2] = res[i1 + i2] % 10;
            
            s.res = [...res];
            snap(9, `Multiply ${n1} and ${n2} = ${digit}. Add to res[${i1+i2}] and handle carry to res[${i1+i2+1}].`, s);
        }
    }
    
    s.i1 = null; s.i2 = null; s.digit = null;
    let finalRes = [...res].reverse();
    let beg = 0;
    while (beg < finalRes.length && finalRes[beg] === 0) beg++;
    finalRes = finalRes.slice(beg);
    
    s.res = finalRes;
    snap(12, `Reverse result array and remove leading zeros. Final result: ${finalRes.join('')}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; gap:20px;">
            <div style="font-size:18px;">Reversed num1: <span style="font-weight:bold; letter-spacing:2px;">${state.num1}</span></div>
            <div style="font-size:18px;">Reversed num2: <span style="font-weight:bold; letter-spacing:2px;">${state.num2}</span></div>
        </div>`;
        
    if (state.i1 !== null && state.i2 !== null) {
        html += `<div style="padding:10px; border:1px solid var(--accent); border-radius:6px; background:rgba(56,189,248,0.1);">
            Multiplying num1[${state.i1}] (${state.num1[state.i1]}) and num2[${state.i2}] (${state.num2[state.i2]}) = ${state.digit}
        </div>`;
    }
    
    html += `<div style="margin-top:10px; font-size:14px; color:var(--text-dim);">Result Array (from least significant to most):</div>
        <div style="display:flex; flex-wrap:wrap; gap:8px;">`;
    
    for (let i = 0; i < state.res.length; i++) {
        let isUpdated = (state.i1 !== null && state.i2 !== null && (i === state.i1 + state.i2 || i === state.i1 + state.i2 + 1));
        let border = isUpdated ? '2px solid var(--accent)' : '1px solid var(--border)';
        let bg = isUpdated ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
        
        html += `<div style="display:flex; flex-direction:column; align-items:center; padding:10px 15px; border:${border}; background:${bg}; border-radius:6px;">
            <div style="color:var(--text-dim); font-size:12px; margin-bottom:5px;">idx ${i}</div>
            <div style="font-size:24px; font-weight:bold; ${isUpdated ? 'color:var(--accent);' : ''}">${state.res[i]}</div>
        </div>`;
    }
    
    html += `</div></div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Integer to Roman', short: 'Int to Roman',
  idea: 'Greedy approach. Iterate through a predefined list of values and their Roman symbols from largest to smallest. Subtract value and append symbol while n >= value.',
  complexity: 'Time O(1) (max 15 ops) · Space O(1)',
  input: '3749', hint: 'integer between 1 and 3999',
  code: [
    'def intToRoman(num):',
    '    symList = [["I", 1], ["IV", 4], ["V", 5], ["IX", 9],',
    '               ["X", 10], ["XL", 40], ["L", 50], ["XC", 90],',
    '               ["C", 100], ["CD", 400], ["D", 500], ["CM", 900],',
    '               ["M", 1000]]',
    '    res = ""',
    '    for sym, val in reversed(symList):',
    '        if num // val:',
    '            count = num // val',
    '            res += (sym * count)',
    '            num = num % val',
    '    return res'
  ],
  parse(str) {
    return { num: parseInt(str.trim()) };
  },
  run({ num }) {
    const { F, snap } = avRecorder();
    const symList = [
      ["M", 1000], ["CM", 900], ["D", 500], ["CD", 400],
      ["C", 100], ["XC", 90], ["L", 50], ["XL", 40],
      ["X", 10], ["IX", 9], ["V", 5], ["IV", 4], ["I", 1]
    ];
    
    let res = "";
    let s = { num, res, currSym: null, currVal: null };
    
    snap(3, `Start with num = ${num}, res = ""`, s);
    
    for (let i = 0; i < symList.length; i++) {
        let sym = symList[i][0];
        let val = symList[i][1];
        
        s.currSym = sym;
        s.currVal = val;
        
        if (num >= val) {
            let count = Math.floor(num / val);
            res += sym.repeat(count);
            num = num % val;
            
            s.num = num;
            s.res = res;
            snap(9, `Value ${val} (${sym}) fits ${count} times. Append "${sym.repeat(count)}" to res. num becomes ${num}.`, s);
        } else {
            snap(7, `Value ${val} (${sym}) is too large for ${num}. Skip.`, s);
        }
        
        if (num === 0) break;
    }
    
    s.currSym = null; s.currVal = null;
    snap(12, `Finished. Roman numeral is "${res}".`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
            <div>
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Remaining Value</div>
                <div style="font-size:32px; font-weight:bold; color:var(--text);">${state.num}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current Roman String</div>
                <div style="font-size:32px; font-weight:bold; color:var(--accent); letter-spacing:2px;">${state.res || '""'}</div>
            </div>
        </div>`;
        
    if (state.currSym) {
        html += `<div style="padding:15px; border:2px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1); text-align:center;">
            <div style="font-size:16px;">Checking Symbol: <span style="font-weight:bold; color:#fbbf24; font-size:24px; margin-left:10px;">${state.currSym} (${state.currVal})</span></div>
        </div>`;
    }
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Count Primes', short: 'Count Primes',
  idea: 'Sieve of Eratosthenes. Start with an array of booleans. For each prime found, mark all its multiples as composite (not prime).',
  complexity: 'Time O(N log(log N)) · Space O(N)',
  input: '30', hint: 'integer n',
  code: [
    'def countPrimes(n):',
    '    if n < 2:',
    '        return 0',
    '    isPrime = [True] * n',
    '    isPrime[0] = isPrime[1] = False',
    '    for i in range(2, int(math.ceil(math.sqrt(n)))):',
    '        if isPrime[i]:',
    '            for multiples_of_i in range(i * i, n, i):',
    '                isPrime[multiples_of_i] = False',
    '    return sum(isPrime)'
  ],
  parse(str) {
    let n = parseInt(str.trim());
    if (n > 100) n = 100; // Cap to 100 for visualization
    return { n };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    
    if (n < 2) {
        snap(2, 'n is less than 2, return 0.', { n, primes: [], curr: null });
        return F;
    }
    
    let isPrime = new Array(n).fill(true);
    isPrime[0] = isPrime[1] = false;
    
    let s = { n, primes: [...isPrime], curr: null, multiple: null };
    snap(4, 'Initialize boolean array for primes up to n-1. Mark 0 and 1 as False.', s);
    
    let limit = Math.ceil(Math.sqrt(n));
    
    for (let i = 2; i < limit; i++) {
        s.curr = i;
        s.multiple = null;
        
        if (isPrime[i]) {
            snap(6, `Found prime ${i}. Now mark all its multiples starting from ${i*i} as False.`, s);
            
            for (let j = i * i; j < n; j += i) {
                isPrime[j] = false;
                s.multiple = j;
                s.primes = [...isPrime];
                snap(8, `Mark ${j} (multiple of ${i}) as not prime.`, s);
            }
        } else {
            snap(6, `Number ${i} is already marked as not prime. Skip.`, s);
        }
    }
    
    s.curr = null; s.multiple = null; s.primes = [...isPrime];
    let count = isPrime.filter(p => p).length;
    snap(10, `Finished. Count of primes less than ${n} is ${count}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:15px; font-family:var(--mono);">
        <div style="font-size:18px;">Finding primes less than ${state.n}</div>
        <div style="display:flex; flex-wrap:wrap; gap:5px;">`;
        
    for (let i = 0; i < state.primes.length; i++) {
        let isCurr = state.curr === i;
        let isMultiple = state.multiple === i;
        let isPrime = state.primes[i];
        
        let border = '1px solid var(--border)';
        let bg = 'var(--surface)';
        let color = 'var(--text)';
        
        if (isCurr) {
            border = '2px solid #34d399';
            bg = 'rgba(52,211,153,0.2)';
        } else if (isMultiple) {
            border = '2px solid #ef4444';
            bg = 'rgba(239,68,68,0.2)';
        } else if (isPrime && i >= 2) {
            bg = 'rgba(52,211,153,0.1)';
            color = '#34d399';
        } else {
            color = 'var(--text-dim)';
        }
        
        html += `<div style="width:35px; height:35px; display:flex; justify-content:center; align-items:center; border:${border}; background:${bg}; border-radius:4px; font-size:14px; font-weight:${isPrime ? 'bold' : 'normal'}; color:${color}; ${!isPrime ? 'text-decoration:line-through;' : ''}">
            ${i}
        </div>`;
    }
    
    html += `</div></div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 21 chunk 2.")
