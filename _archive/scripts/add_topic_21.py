content = """
defineAlgo('21_math_geometry', {
  title: 'Palindrome Number', short: 'Palindrome',
  idea: 'Revert half of the number to avoid string conversion and overflow issues. Compare the first half with the reverted second half.',
  complexity: 'Time O(log10(N)) · Space O(1)',
  input: '1221', hint: 'integer (e.g. 1221)',
  code: [
    'def isPalindrome(x):',
    '    if x < 0 or (x % 10 == 0 and x != 0):',
    '        return False',
    '    revertedNumber = 0',
    '    while x > revertedNumber:',
    '        revertedNumber = revertedNumber * 10 + x % 10',
    '        x //= 10',
    '    return x == revertedNumber or x == revertedNumber // 10'
  ],
  parse(str) {
    return { x: parseInt(str.trim()) };
  },
  run({ x }) {
    const { F, snap } = avRecorder();
    const original = x;
    let s = { x, revertedNumber: 0, original };
    
    if (x < 0 || (x % 10 === 0 && x !== 0)) {
        snap(2, 'Negative numbers or numbers ending in 0 (except 0 itself) are not palindromes.', s);
        snap(3, 'Return false.', s);
        return F;
    }
    
    snap(4, 'Initialize revertedNumber = 0.', s);
    
    while (x > s.revertedNumber) {
        s.revertedNumber = s.revertedNumber * 10 + x % 10;
        x = Math.floor(x / 10);
        s.x = x;
        snap(6, `Pop last digit and append to revertedNumber. x = ${x}, revertedNumber = ${s.revertedNumber}.`, s);
    }
    
    snap(8, `Loop ends. If original number had odd length, we can discard the middle digit by revertedNumber // 10.`, s);
    let result = (x === s.revertedNumber) || (x === Math.floor(s.revertedNumber / 10));
    snap(8, `Return x == revertedNumber or x == revertedNumber // 10. Result: ${result}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original: <span style="font-weight:bold;">${state.original}</span></div>
        <div style="display:flex; gap:30px;">
            <div style="display:flex; flex-direction:column; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">x (First Half)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${state.x}</div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">revertedNumber (Second Half)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.revertedNumber}</div>
            </div>
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Plus One', short: 'Plus One',
  idea: 'Start from the last digit. If it is 9, it becomes 0 and we carry over 1. Otherwise, just add 1 and we are done. If all digits are 9, we prepend a 1.',
  complexity: 'Time O(N) · Space O(1) in-place',
  input: '1,2,9', hint: 'comma-separated digits',
  code: [
    'def plusOne(digits):',
    '    for i in range(len(digits) - 1, -1, -1):',
    '        if digits[i] == 9:',
    '            digits[i] = 0',
    '        else:',
    '            digits[i] += 1',
    '            return digits',
    '    return [1] + digits'
  ],
  parse(str) {
    return { digits: str.split(',').map(n => parseInt(n.trim())) };
  },
  run({ digits }) {
    const { F, snap } = avRecorder();
    let s = { digits: [...digits], curr: null };
    
    snap(2, 'Start traversing digits from right to left.', s);
    
    for (let i = digits.length - 1; i >= 0; i--) {
        s.curr = i;
        snap(3, `Check digit at index ${i}: ${s.digits[i]}.`, s);
        
        if (s.digits[i] === 9) {
            s.digits[i] = 0;
            snap(4, `Digit is 9, change to 0 and carry 1 to the next left digit.`, s);
        } else {
            s.digits[i] += 1;
            snap(6, `Digit is not 9, add 1. No more carry, we are done.`, s);
            s.curr = null;
            return F;
        }
    }
    
    s.curr = null;
    s.digits = [1, ...s.digits];
    snap(8, 'All digits were 9. Prepend 1 to the result.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.digits.length; i++) {
       let isCurr = state.curr === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:10px 15px; border:${border}; background:${bg}; border-radius:6px; font-family:var(--mono);">
          <div style="font-weight:bold; font-size:24px;">${state.digits[i]}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Happy Number', short: 'Happy Number',
  idea: 'Replace the number by the sum of the squares of its digits. Use Floyd cycle detection (slow and fast pointers) to find if it loops to 1.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '19', hint: 'integer (e.g. 19)',
  code: [
    'def get_next(n):',
    '    total_sum = 0',
    '    while n > 0:',
    '        n, digit = divmod(n, 10)',
    '        total_sum += digit ** 2',
    '    return total_sum',
    '',
    'def isHappy(n):',
    '    slow_runner = n',
    '    fast_runner = get_next(n)',
    '    while fast_runner != 1 and slow_runner != fast_runner:',
    '        slow_runner = get_next(slow_runner)',
    '        fast_runner = get_next(get_next(fast_runner))',
    '    return fast_runner == 1'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    
    function getNext(num) {
        let sum = 0;
        let temp = num;
        while (temp > 0) {
            let digit = temp % 10;
            sum += digit * digit;
            temp = Math.floor(temp / 10);
        }
        return sum;
    }
    
    let slow = n;
    let fast = getNext(n);
    let s = { slow, fast, n, history: [{slow, fast}] };
    
    snap(8, `Initialize slow = ${n}, fast = get_next(${n}) = ${fast}.`, s);
    
    while (fast !== 1 && slow !== fast) {
        slow = getNext(slow);
        fast = getNext(getNext(fast));
        s.slow = slow;
        s.fast = fast;
        s.history.push({slow, fast});
        snap(11, `Update slow = get_next(slow) = ${slow}, fast = get_next(get_next(fast)) = ${fast}.`, s);
    }
    
    let isHappy = (fast === 1);
    snap(14, `Loop terminates. fast == 1? ${isHappy}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original: ${state.n}</div>
        <div style="display:flex; gap:20px;">
            <div style="padding:10px 20px; border:2px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1);">
                <div style="color:var(--text-dim); font-size:12px;">Slow Pointer</div>
                <div style="font-size:24px; font-weight:bold; color:#fbbf24;">${state.slow}</div>
            </div>
            <div style="padding:10px 20px; border:2px solid #ef4444; border-radius:8px; background:rgba(239,68,68,0.1);">
                <div style="color:var(--text-dim); font-size:12px;">Fast Pointer</div>
                <div style="font-size:24px; font-weight:bold; color:#ef4444;">${state.fast}</div>
            </div>
        </div>
        <div style="font-size:14px; color:var(--text-dim); margin-top:10px;">
            History: <br/>
            ${state.history.map((h, idx) => `<span style="margin-right:10px;">[${idx}] S:${h.slow} F:${h.fast}</span>`).join('')}
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Pow(x, n)', short: 'Pow(x, n)',
  idea: 'Binary Exponentiation. Calculate x^n efficiently by squaring x and halving n. If n is odd, multiply result by current x.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '2.0, 10', hint: 'x, n (e.g. 2.0, 10)',
  code: [
    'def myPow(x, n):',
    '    if n < 0:',
    '        x = 1 / x',
    '        n = -n',
    '    res = 1',
    '    while n > 0:',
    '        if n % 2 == 1:',
    '            res *= x',
    '        x *= x',
    '        n //= 2',
    '    return res'
  ],
  parse(str) {
    const parts = str.split(',');
    return { x: parseFloat(parts[0].trim()), n: parseInt(parts[1].trim()) };
  },
  run({ x, n }) {
    const { F, snap } = avRecorder();
    let currentX = x;
    let currentN = n;
    
    let s = { currentX, currentN, res: 1, isOdd: false };
    
    if (currentN < 0) {
        currentX = 1 / currentX;
        currentN = -currentN;
        s.currentX = currentX;
        s.currentN = currentN;
        snap(2, 'n is negative, invert x and negate n.', s);
    }
    
    snap(5, 'Initialize res = 1.', s);
    
    while (currentN > 0) {
        s.isOdd = currentN % 2 === 1;
        if (s.isOdd) {
            s.res *= currentX;
            snap(7, `n is odd. res *= x. res = ${s.res}.`, s);
        } else {
            snap(7, `n is even. Skip res update.`, s);
        }
        
        currentX *= currentX;
        currentN = Math.floor(currentN / 2);
        s.currentX = currentX;
        s.currentN = currentN;
        snap(9, `x *= x (x becomes ${currentX}), n //= 2 (n becomes ${currentN}).`, s);
    }
    
    s.isOdd = false;
    snap(10, `n is 0. Return res = ${s.res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Result (res)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${Number.isInteger(state.res) ? state.res : state.res.toFixed(5)}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current x</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${Number.isInteger(state.currentX) ? state.currentX : state.currentX.toFixed(5)}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current n</div>
                <div style="font-size:24px; font-weight:bold; color:#f87171;">${state.currentN}</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:5px;">${state.currentN.toString(2)} (binary)</div>
            </div>
        </div>
        ${state.isOdd ? '<div style="color:#f87171; font-weight:bold;">Current n is odd! Multiply Result by Current x.</div>' : '<div style="color:var(--text-dim); font-weight:bold;">Current n is even. Square Current x.</div>'}
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 21 chunk 1.")
