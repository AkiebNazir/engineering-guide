import sys

content = """
defineAlgo('18_greedy', {
  title: 'Gas Station', short: 'Gas Station',
  idea: 'If total gas < total cost, return -1. Otherwise, a solution exists. We keep a `curr_tank`. If `curr_tank < 0` at station `i`, it means no station from `start` to `i` can be the answer, so we reset `start` to `i + 1` and `curr_tank` to 0.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1,2,3,4,5; 3,4,5,1,2', hint: 'gas; cost',
  code: [
    'def canCompleteCircuit(gas, cost):',
    '    if sum(gas) < sum(cost):',
    '        return -1',
    '        ',
    '    curr_tank = 0',
    '    start = 0',
    '    ',
    '    for i in range(len(gas)):',
    '        curr_tank += gas[i] - cost[i]',
    '        if curr_tank < 0:',
    '            start = i + 1',
    '            curr_tank = 0',
    '            ',
    '    return start'
  ],
  parse(str) {
    const parts = str.split(';');
    return { gas: parts[0].split(',').map(Number), cost: parts[1].split(',').map(Number) };
  },
  run({ gas, cost }) {
    const { F, snap } = avRecorder();
    const sumGas = gas.reduce((a,b)=>a+b,0);
    const sumCost = cost.reduce((a,b)=>a+b,0);
    const n = gas.length;
    
    let s = { gas, cost, n, start: 0, curr_tank: 0, sumGas, sumCost, i: null };
    
    if (sumGas < sumCost) {
       snap(2, `Total gas (${sumGas}) < Total cost (${sumCost}). Impossible. Return -1.`, s);
       return F;
    }
    
    snap(4, `Total gas (${sumGas}) >= Total cost (${sumCost}). A solution must exist. Initialize start=0, curr_tank=0.`, s);
    
    let curr_tank = 0;
    let start = 0;
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       let diff = gas[i] - cost[i];
       curr_tank += diff;
       s.curr_tank = curr_tank;
       
       snap(8, `Station ${i}: gas=${gas[i]}, cost=${cost[i]}. Diff = ${diff}. curr_tank = ${curr_tank}.`, s);
       
       if (curr_tank < 0) {
          start = i + 1;
          curr_tank = 0;
          s.start = start;
          s.curr_tank = curr_tank;
          snap(10, `curr_tank < 0. We cannot reach the next station. Any start point from previous start up to ${i} is invalid. Reset start to ${start}, curr_tank to 0.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished checking. The valid start station is ${start}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px;">
        <div>Total Gas: ${state.sumGas}</div>
        <div>Total Cost: ${state.sumCost}</div>
        <div>Current Tank: <span style="color:${state.curr_tank<0?'#ef4444':'#34d399'}; font-weight:bold;">${state.curr_tank}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Gas:</div>';
    for (let i=0; i<state.n; i++) html += `<div style="width:40px; text-align:center; font-weight:bold;">${state.gas[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Cost:</div>';
    for (let i=0; i<state.n; i++) html += `<div style="width:40px; text-align:center; font-weight:bold; color:var(--text-dim);">${state.cost[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px; margin-top:5px;"><div style="width:60px;">Diff:</div>';
    for (let i=0; i<state.n; i++) {
       let diff = state.gas[i] - state.cost[i];
       html += `<div style="width:40px; text-align:center; font-weight:bold; color:${diff<0?'#ef4444':'#34d399'};">${diff > 0 ? '+'+diff : diff}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px; margin-top:5px;"><div style="width:60px;">State:</div>';
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let isStart = state.start === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid transparent';
       html += `<div style="width:40px; height:20px; display:flex; align-items:center; justify-content:center; border:${border};">
          ${isStart ? '<span style="color:#34d399; font-weight:bold; font-size:10px;">START</span>' : ''}
       </div>`;
    }
    html += '</div>';
    
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Best Time to Buy and Sell Stock II', short: 'Stock II',
  idea: 'Greedy approach. Since we can make infinite transactions, we can just capture every single upward price movement. Add `prices[i] - prices[i-1]` to profit if it\\'s positive.',
  complexity: 'Time O(N) · Space O(1)',
  input: '7,1,5,3,6,4', hint: 'comma-separated prices',
  code: [
    'def maxProfit(prices):',
    '    profit = 0',
    '    for i in range(1, len(prices)):',
    '        if prices[i] > prices[i-1]:',
    '            profit += prices[i] - prices[i-1]',
    '    return profit'
  ],
  parse(str) {
    return { prices: str.split(',').map(Number) };
  },
  run({ prices }) {
    const { F, snap } = avRecorder();
    let profit = 0;
    const n = prices.length;
    const s = { prices, n, profit, i: null };
    
    snap(2, 'Initialize total profit = 0.', s);
    
    for (let i = 1; i < n; i++) {
       s.i = i;
       if (prices[i] > prices[i-1]) {
          let diff = prices[i] - prices[i-1];
          profit += diff;
          s.profit = profit;
          snap(5, `Price increased from ${prices[i-1]} to ${prices[i]}. Capture this profit (+${diff}). Total = ${profit}.`, s);
       } else {
          snap(3, `Price decreased or stayed same (${prices[i-1]} to ${prices[i]}). Do nothing.`, s);
       }
    }
    
    s.i = null;
    snap(6, `Finished. Max profit = ${profit}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:16px;">Total Profit: <span style="color:#34d399; font-weight:bold;">${state.profit}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px; align-items:flex-end; height:100px;">';
    const maxP = Math.max(...state.prices, 1);
    
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i || state.i === i+1; 
       let h = (state.prices[i] / maxP) * 80;
       let color = 'var(--surface)';
       if (state.i === i) {
          color = state.prices[i] > state.prices[i-1] ? 'rgba(52,211,153,0.5)' : 'rgba(239,68,68,0.5)';
       }
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
          <div style="font-size:10px; color:var(--text-dim);">${state.prices[i]}</div>
          <div style="width:30px; height:${h}px; background:${color}; border:1px solid var(--border);"></div>
          <div style="font-size:10px; font-family:var(--mono);">Day ${i}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Hand of Straights', short: 'Hand of Straights',
  idea: 'Count frequencies. Iterate over sorted keys. If a key has count > 0, we must form a group of size W starting with this key. Decrement counts of `k, k+1, ..., k+W-1` by this count.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,2,3,6,2,3,4,7,8; 3', hint: 'hand; groupSize W',
  code: [
    'def isNStraightHand(hand, groupSize):',
    '    if len(hand) % groupSize != 0: return False',
    '    ',
    '    count = collections.Counter(hand)',
    '    for k in sorted(count.keys()):',
    '        if count[k] > 0:',
    '            c = count[k]',
    '            for i in range(k, k + groupSize):',
    '                if count[i] < c:',
    '                    return False',
    '                count[i] -= c',
    '                ',
    '    return True'
  ],
  parse(str) {
    const parts = str.split(';');
    return { hand: parts[0].split(',').map(Number), W: parseInt(parts[1]) };
  },
  run({ hand, W }) {
    const { F, snap } = avRecorder();
    const n = hand.length;
    let s = { hand, W, count: {}, sortedKeys: [], curK: null, curGrp: null };
    
    if (n % W !== 0) {
       snap(2, `Length ${n} is not divisible by groupSize ${W}. Return False.`, s);
       return F;
    }
    
    let count = {};
    for (const card of hand) count[card] = (count[card] || 0) + 1;
    let sortedKeys = Object.keys(count).map(Number).sort((a,b)=>a-b);
    
    s.count = JSON.parse(JSON.stringify(count));
    s.sortedKeys = sortedKeys;
    snap(4, `Count frequencies and sort keys.`, s);
    
    for (const k of sortedKeys) {
       s.curK = k;
       if (count[k] > 0) {
          const c = count[k];
          let grp = [];
          for(let i=k; i<k+W; i++) grp.push(i);
          s.curGrp = grp;
          snap(7, `We have ${c} occurrences of ${k}. We must form ${c} group(s) of [${grp.join(', ')}].`, s);
          
          for (let i = k; i < k + W; i++) {
             if ((count[i] || 0) < c) {
                snap(9, `Need ${c} of card ${i}, but only have ${count[i] || 0}. Cannot form group. Return False.`, s);
                return F;
             }
             count[i] -= c;
          }
          s.count = JSON.parse(JSON.stringify(count));
          snap(10, `Successfully subtracted ${c} from all cards in group.`, s);
       } else {
          s.curGrp = null;
          snap(6, `Count for ${k} is 0. Skip.`, s);
       }
    }
    
    s.curK = null; s.curGrp = null;
    snap(12, 'Successfully processed all cards. Return True.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Group Size (W): ${state.W}</div>`;
    
    html += '<div style="display:flex; gap:10px; flex-wrap:wrap;">';
    for (const k of state.sortedKeys) {
       let inGrp = state.curGrp && state.curGrp.includes(k);
       let isRoot = state.curK === k;
       
       let border = inGrp ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isRoot ? 'rgba(56,189,248,0.2)' : (inGrp ? 'rgba(52,211,153,0.1)' : 'var(--surface)');
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:50px; height:50px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-size:14px; font-weight:bold; font-family:var(--mono);">${k}</div>
          <div style="font-size:10px; color:var(--text-dim);">Count: ${state.count[k] || 0}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 18 chunk 2.")
