content = """
defineAlgo('21_math_geometry', {
  title: 'Factorial Trailing Zeroes', short: 'Trailing Zeroes',
  idea: 'A trailing zero is produced by a factor of 10, which is 2 * 5. In any factorial, the number of 5 factors is always less than the number of 2 factors, so we just count factors of 5.',
  complexity: 'Time O(log5(N)) · Space O(1)',
  input: '25', hint: 'integer (e.g. 25)',
  code: [
    'def trailingZeroes(n):',
    '    res = 0',
    '    while n > 0:',
    '        n //= 5',
    '        res += n',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let s = { n, res, currN: n };
    
    snap(2, 'Initialize res = 0.', s);
    
    while (s.currN > 0) {
        let added = Math.floor(s.currN / 5);
        s.currN = added;
        res += added;
        s.res = res;
        
        snap(4, `Divide n by 5: new n = ${s.currN}. Add to res. res is now ${res}.`, s);
    }
    
    snap(6, `Finished. Total trailing zeroes is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original n = <span style="font-weight:bold;">${state.n}</span></div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current n (n //= 5)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${state.currN}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Trailing Zeroes Count (res)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.res}</div>
            </div>
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 21 chunk 3.")
