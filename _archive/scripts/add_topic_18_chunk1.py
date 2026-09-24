import sys

content = """
defineAlgo('18_greedy', {
  title: 'Maximize Sum Of Array After K Negations', short: 'Max Sum K Negations',
  idea: 'Greedily negate the most negative numbers first. If K > 0 and no negatives remain, repeatedly negate the smallest absolute value (which just flips its sign if K is odd).',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '4, -5, 4, -3, 1, 2; 2', hint: 'nums; k',
  code: [
    'def largestSumAfterKNegations(nums, k):',
    '    nums.sort()',
    '    ',
    '    for i in range(len(nums)):',
    '        if nums[i] < 0 and k > 0:',
    '            nums[i] = -nums[i]',
    '            k -= 1',
    '            ',
    '    if k % 2 == 1:',
    '        nums.sort()',
    '        nums[0] = -nums[0]',
    '        ',
    '    return sum(nums)'
  ],
  parse(str) {
    const parts = str.split(';');
    return { nums: parts[0].split(',').map(Number), k: parseInt(parts[1]) };
  },
  run({ nums, k }) {
    const { F, snap } = avRecorder();
    nums.sort((a,b) => a - b);
    
    let currentK = k;
    const s = { nums: [...nums], currentK, i: null };
    snap(3, `Sort array: [${nums.join(', ')}]. Remaining K = ${currentK}`, s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       if (nums[i] < 0 && currentK > 0) {
          nums[i] = -nums[i];
          currentK--;
          s.nums = [...nums];
          s.currentK = currentK;
          snap(7, `nums[${i}] is negative and K > 0. Negate it to ${nums[i]}. Remaining K = ${currentK}`, s);
       } else {
          snap(5, `nums[${i}] is >= 0 or K is 0. Move to next.`, s);
       }
    }
    s.i = null;
    
    if (currentK % 2 === 1) {
       nums.sort((a,b) => a - b);
       s.nums = [...nums];
       snap(11, `K is odd (${currentK}). Re-sort array to find the smallest absolute value.`, s);
       nums[0] = -nums[0];
       s.nums = [...nums];
       snap(12, `Negate the smallest value nums[0] to ${nums[0]}.`, s);
    }
    
    const sum = nums.reduce((a,b)=>a+b, 0);
    snap(14, `Done. Max sum = ${sum}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Remaining K: ${state.currentK}</div>`;
    html += '<div style="display:flex; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = 'var(--surface)';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Maximum Subarray', short: 'Kadane\\'s',
  idea: 'Kadane\\'s algorithm: Keep a running sum. If it goes below 0, it contributes negatively to any future subarray, so reset it to 0. Keep track of the max sum seen.',
  complexity: 'Time O(N) · Space O(1)',
  input: '-2,1,-3,4,-1,2,1,-5,4', hint: 'comma-separated nums',
  code: [
    'def maxSubArray(nums):',
    '    max_sum = nums[0]',
    '    curr_sum = 0',
    '    ',
    '    for n in nums:',
    '        if curr_sum < 0:',
    '            curr_sum = 0',
    '        curr_sum += n',
    '        max_sum = max(max_sum, curr_sum)',
    '        ',
    '    return max_sum'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let max_sum = nums[0];
    let curr_sum = 0;
    
    const s = { nums, max_sum, curr_sum, i: null };
    snap(3, 'Initialize max_sum to first element, curr_sum to 0.', s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       if (curr_sum < 0) {
          curr_sum = 0;
          s.curr_sum = curr_sum;
          snap(7, 'curr_sum < 0, resetting to 0 because a negative prefix will strictly decrease future sums.', s);
       }
       curr_sum += nums[i];
       s.curr_sum = curr_sum;
       max_sum = Math.max(max_sum, curr_sum);
       s.max_sum = max_sum;
       snap(9, `Add nums[${i}] (${nums[i]}) to curr_sum. curr_sum=${curr_sum}, max_sum=${max_sum}.`, s);
    }
    
    s.i = null;
    snap(11, `Done. Max subarray sum = ${max_sum}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:5px;">Current Sum: <span style="color:var(--accent); font-weight:bold;">${state.curr_sum}</span></div>`;
    html += `<div style="font-family:var(--mono); margin-bottom:10px;">Global Max Sum: <span style="color:#34d399; font-weight:bold;">${state.max_sum}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.1)' : 'var(--surface)';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Jump Game', short: 'Jump Game',
  idea: 'Greedy approach: Keep track of the furthest index we can reach (`goal` or `max_reach`). If we iterate to an index beyond our `max_reach`, we can\\'t go further (return False).',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,3,1,1,4', hint: 'comma-separated jump lengths',
  code: [
    'def canJump(nums):',
    '    max_reach = 0',
    '    for i in range(len(nums)):',
    '        if i > max_reach:',
    '            return False',
    '        max_reach = max(max_reach, i + nums[i])',
    '        if max_reach >= len(nums) - 1:',
    '            return True',
    '    return True'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let max_reach = 0;
    const n = nums.length;
    const s = { nums, max_reach, i: null };
    
    snap(2, 'Initialize max_reach to index 0.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       if (i > max_reach) {
          snap(5, `Index ${i} is beyond our max_reach of ${max_reach}. We cannot proceed. Return False.`, s);
          return F;
       }
       
       let new_reach = i + nums[i];
       if (new_reach > max_reach) {
          max_reach = new_reach;
          s.max_reach = max_reach;
          snap(6, `At index ${i}, we can jump up to ${nums[i]} steps. New max_reach = max(old, ${i}+${nums[i]}) = ${max_reach}.`, s);
       } else {
          snap(6, `At index ${i}, jump length ${nums[i]} gives reach ${i+nums[i]}, which is not better than current max_reach ${max_reach}.`, s);
       }
       
       if (max_reach >= n - 1) {
          snap(8, `max_reach ${max_reach} covers the last index. Return True.`, s);
          return F;
       }
    }
    
    s.i = null;
    snap(9, `Successfully iterated the array. Return True.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Furthest Reachable Index: <span style="color:#34d399; font-weight:bold;">${state.max_reach}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let isReachable = i <= state.max_reach;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isReachable ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i=${i}</div>
          <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold; color:${isReachable?'var(--text)':'var(--text-dim)'};">${state.nums[i]}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Jump Game II', short: 'Jump Game II',
  idea: 'We need minimum jumps. Maintain a `current_jump_end` and `farthest` index. Iterate through the array; when you hit `current_jump_end`, you *must* jump, so increment jumps and update `current_jump_end` to `farthest`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,3,1,1,4', hint: 'comma-separated jump lengths',
  code: [
    'def jump(nums):',
    '    jumps = 0',
    '    curr_end = 0',
    '    farthest = 0',
    '    ',
    '    for i in range(len(nums) - 1):',
    '        farthest = max(farthest, i + nums[i])',
    '        ',
    '        if i == curr_end:',
    '            jumps += 1',
    '            curr_end = farthest',
    '            ',
    '    return jumps'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let jumps = 0, curr_end = 0, farthest = 0;
    const n = nums.length;
    const s = { nums, jumps, curr_end, farthest, i: null };
    
    snap(4, 'Initialize jumps=0, curr_end=0, farthest=0.', s);
    
    for (let i = 0; i < n - 1; i++) {
       s.i = i;
       farthest = Math.max(farthest, i + nums[i]);
       s.farthest = farthest;
       
       snap(7, `At index ${i} (jump=${nums[i]}), farthest reach from here is ${i+nums[i]}. Global farthest is now ${farthest}.`, s);
       
       if (i === curr_end) {
          jumps++;
          curr_end = farthest;
          s.jumps = jumps;
          s.curr_end = curr_end;
          snap(10, `Reached curr_end (${i}). We must jump now. Jumps = ${jumps}, new curr_end = ${curr_end}.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished. Minimum jumps required = ${jumps}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px;">
        <div>Jumps: <span style="color:var(--accent); font-weight:bold;">${state.jumps}</span></div>
        <div>Current Jump End: <span style="color:#ef4444; font-weight:bold;">${state.curr_end}</span></div>
        <div>Farthest Known Reach: <span style="color:#34d399; font-weight:bold;">${state.farthest}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let isEnd = state.curr_end === i;
       let isFarthest = state.farthest === i;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       if (isEnd) border = '2px solid #ef4444';
       
       let bg = i <= state.farthest ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i=${i}</div>
          <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>
          <div style="font-size:10px; color:#34d399; height:12px; margin-top:2px;">${isFarthest?'farthest':''}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 18 chunk 1.")
