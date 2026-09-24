import sys

content = """
defineAlgo('16_dp_1d', {
  title: 'Climbing Stairs', short: 'Climbing Stairs',
  idea: 'DP state: `dp[i]` is the number of distinct ways to reach step `i`. To reach step `i`, you must come from either step `i-1` or step `i-2`. Thus `dp[i] = dp[i-1] + dp[i-2]`. Instead of an array, we can optimize space by keeping only the last two values.',
  complexity: 'Time O(N) · Space O(1)',
  input: '5', hint: 'n',
  code: [
    'def climbStairs(n):',
    '    if n <= 2: return n',
    '    prev2, prev1 = 1, 2',
    '    for i in range(3, n + 1):',
    '        curr = prev1 + prev2',
    '        prev2 = prev1',
    '        prev1 = curr',
    '    return prev1',
  ],
  parse(str) {
    const n = parseInt(str.trim());
    if (isNaN(n) || n < 1) throw new Error("Input must be a positive integer.");
    return { n };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    
    if (n <= 2) {
       snap(1, `n is ${n}, which is <= 2. Return ${n}.`, { n, prev2: null, prev1: null, curr: null, i: null });
       return F;
    }
    
    let prev2 = 1, prev1 = 2;
    const s = { n, prev2, prev1, curr: null, i: null };
    snap(2, `Initialize prev2 = 1 (ways to reach step 1) and prev1 = 2 (ways to reach step 2).`, s);
    
    for (let i = 3; i <= n; i++) {
       s.i = i;
       let curr = prev1 + prev2;
       s.curr = curr;
       snap(4, `Step ${i}: Ways to reach this step is the sum of ways to reach step ${i-1} (${prev1}) and step ${i-2} (${prev2}). curr = ${curr}.`, s);
       
       prev2 = prev1;
       s.prev2 = prev2;
       snap(5, `Shift prev2 forward to ${prev1}.`, s);
       
       prev1 = curr;
       s.prev1 = prev1;
       snap(6, `Shift prev1 forward to ${curr}.`, s);
    }
    
    s.i = null; s.curr = null;
    snap(7, `Loop finished. Return prev1 (${prev1}).`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap: 20px; align-items:center; width: 100%; padding: 20px;">
          <div style="font-size: 16px; color: var(--accent); font-weight: bold; letter-spacing: 0.05em; text-transform: uppercase;">n = ${s.n}</div>
          
          <div style="display:flex; gap: 20px; align-items: flex-end; height: 100px; margin-top: 20px;">
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--text-dim); font-size: 13px;">prev2</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.prev2 !== null ? 'var(--border)' : 'transparent'}; border-radius: 8px; background: var(--surface); font-size: 20px; font-weight: bold; color: var(--text);">
                   ${s.prev2 !== null ? s.prev2 : ''}
                </div>
             </div>
             
             <div style="font-size: 24px; color: var(--text-dim); padding-bottom: 15px;">+</div>
             
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--text-dim); font-size: 13px;">prev1</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.prev1 !== null ? 'var(--border)' : 'transparent'}; border-radius: 8px; background: var(--surface); font-size: 20px; font-weight: bold; color: var(--text);">
                   ${s.prev1 !== null ? s.prev1 : ''}
                </div>
             </div>
             
             <div style="font-size: 24px; color: var(--text-dim); padding-bottom: 15px;">=</div>
             
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--accent); font-size: 13px; font-weight: bold;">curr (step ${s.i || '?'})</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.curr !== null ? 'var(--accent)' : 'transparent'}; border-radius: 8px; background: rgba(56, 189, 248, 0.1); font-size: 20px; font-weight: bold; color: var(--accent);">
                   ${s.curr !== null ? s.curr : ''}
                </div>
             </div>
          </div>
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); text-align: center; max-width: 400px; line-height: 1.5;">
              Visualizes the rolling variables optimization for 1D DP. Only the last two states are needed to compute the current state.
          </div>
      </div>
    `;
  }
});

defineAlgo('16_dp_1d', {
  title: 'Coin Change', short: 'Coin Change',
  idea: 'Unbounded Knapsack. `dp[a]` is the minimum number of coins to make amount `a`. We initialize `dp` with infinity, set `dp[0] = 0`, and iterate from `1` to `amount`. For each amount, we try all coins `c`. If `c <= a`, then `dp[a] = min(dp[a], dp[a - c] + 1)`.',
  complexity: 'Time O(amount * len(coins)) · Space O(amount)',
  input: '1, 2, 5; 11', hint: 'comma-separated coins; amount',
  code: [
    'def coinChange(coins, amount):',
    '    dp = [float("inf")] * (amount + 1)',
    '    dp[0] = 0',
    '    ',
    '    for a in range(1, amount + 1):',
    '        for c in coins:',
    '            if c <= a:',
    '                dp[a] = min(dp[a], dp[a - c] + 1)',
    '                ',
    '    return dp[amount] if dp[amount] != float("inf") else -1',
  ],
  parse(str) {
    const parts = str.split(';');
    if (parts.length < 2) throw new Error("Input must contain coins and amount, separated by semicolon.");
    const coins = parts[0].split(',').map(Number).filter(n => !isNaN(n));
    const amount = parseInt(parts[1].trim());
    if (isNaN(amount)) throw new Error("Amount must be an integer.");
    if (coins.length === 0) throw new Error("Must provide at least one coin.");
    return { coins, amount };
  },
  run({ coins, amount }) {
    const { F, snap } = avRecorder();
    
    let dp = new Array(amount + 1).fill('inf');
    dp[0] = 0;
    
    const s = { coins, amount, dp: [...dp], a: null, c: null };
    snap(2, `Initialize dp array of size ${amount + 1} with infinity. Set dp[0] = 0.`, s);
    
    for (let a = 1; a <= amount; a++) {
       s.a = a; s.c = null;
       snap(4, `Compute min coins for amount ${a}.`, s);
       
       for (let c of coins) {
          s.c = c;
          if (c <= a) {
             const prevDp = dp[a - c] === 'inf' ? Infinity : dp[a - c];
             const curDp = dp[a] === 'inf' ? Infinity : dp[a];
             
             if (prevDp !== Infinity) {
                if (prevDp + 1 < curDp) {
                   dp[a] = prevDp + 1;
                   s.dp = [...dp];
                   snap(7, `Using coin ${c}, we reach amount ${a} from amount ${a - c}. dp[${a}] = min(${curDp === Infinity ? 'inf' : curDp}, ${prevDp} + 1) = ${prevDp + 1}.`, s);
                } else {
                   snap(7, `Using coin ${c} gives ${prevDp} + 1 = ${prevDp + 1} coins, which is not better than current dp[${a}] = ${curDp === Infinity ? 'inf' : curDp}.`, s);
                }
             } else {
                snap(7, `Amount ${a - c} is unreachable, so we cannot use coin ${c} here.`, s);
             }
          } else {
             snap(6, `Coin ${c} is greater than amount ${a}, skip.`, s);
          }
       }
    }
    
    s.a = null; s.c = null;
    const ans = dp[amount] === 'inf' ? -1 : dp[amount];
    snap(9, `Loop finished. Result is dp[${amount}] = ${ans === -1 ? 'inf -> -1' : ans}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getDpHTML = () => {
       let html = '<div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom: 20px;">';
       for (let i = 0; i <= s.amount; i++) {
          const isActiveA = i === s.a;
          const isSourceA = s.a !== null && s.c !== null && s.c <= s.a && i === s.a - s.c;
          
          let bg = 'var(--surface)';
          let border = 'var(--border)';
          
          if (isActiveA) { border = 'var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
          else if (isSourceA) { border = '#34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
          
          const val = s.dp[i] === 'inf' ? '∞' : s.dp[i];
          
          html += `
          <div style="display:flex; flex-direction:column; align-items:center;">
             <div style="font-family: var(--mono); font-size: 11px; color: var(--text-dim); margin-bottom: 2px;">${i}</div>
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: 2px solid ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px; font-weight: ${isActiveA || isSourceA ? 'bold' : 'normal'};">
                ${val}
             </div>
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    const getCoinsHTML = () => {
       let html = '<div style="display:flex; gap:8px; margin-bottom: 20px;">';
       for (let c of s.coins) {
          const isActive = c === s.c;
          let border = isActive ? 'var(--accent)' : 'var(--border)';
          let bg = isActive ? 'rgba(56, 189, 248, 0.1)' : 'var(--surface)';
          
          html += `
          <div style="padding: 6px 12px; border: 2px solid ${border}; border-radius: 999px; background: ${bg}; font-family: var(--mono); font-size: 14px; font-weight: bold; color: ${isActive ? 'var(--accent)' : 'var(--text)'};">
             ${c}
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; width: 100%; padding: 10px;">
          <div style="color: var(--accent); font-weight: 600; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">DP Array (Minimum Coins)</div>
          ${getDpHTML()}
          
          <div style="color: var(--accent); font-weight: 600; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Available Coins</div>
          ${getCoinsHTML()}
          
          <div style="margin-top: 15px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.a !== null && s.c !== null && s.c <= s.a ? 
                `dp[${s.a}] = min(dp[${s.a}], dp[${s.a - s.c}] + 1)` : 
                'Iterating through amounts and coins...'}
          </div>
      </div>
    `;
  }
});
"""
with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending topic 16 visualizers.")
