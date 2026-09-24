import sys

content = """
defineAlgo('19_intervals', {
  title: 'Meeting Rooms', short: 'Meeting Rooms',
  idea: 'Sort intervals by start time. Check if any meeting ends after the next one starts (`intervals[i][1] > intervals[i+1][0]`). If so, a person cannot attend both.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '0,30; 5,10; 15,20', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def canAttendMeetings(intervals):',
    '    intervals.sort(key=lambda x: x[0])',
    '    ',
    '    for i in range(len(intervals) - 1):',
    '        if intervals[i][1] > intervals[i+1][0]:',
    '            return False',
    '            ',
    '    return True'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[0] - b[0]);
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), i: null };
    
    snap(2, 'Sort intervals by start time.', s);
    
    for (let i = 0; i < intervals.length - 1; i++) {
       s.i = i;
       if (intervals[i][1] > intervals[i+1][0]) {
          snap(5, `Overlap found! Meeting ${i} ends at ${intervals[i][1]}, but meeting ${i+1} starts at ${intervals[i+1][0]}. Cannot attend all.`, s);
          return F;
       }
       snap(4, `Meeting ${i} ends at ${intervals[i][1]} and next starts at ${intervals[i+1][0]}. No overlap.`, s);
    }
    
    s.i = null;
    snap(8, 'No overlaps found. Can attend all meetings!', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 10);
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j || state.i === j-1 ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="display:flex; align-items:center; gap:8px;">
          <div style="width:30px;">[${start},${end}]</div>
          <div style="position:relative; width:calc(100% - 50px); height:24px; background:var(--surface); border:1px solid var(--border);">
             <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px;"></div>
          </div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Merge Intervals', short: 'Merge',
  idea: 'Sort by start time. Build a `merged` list. If the current interval overlaps the last added interval (`curr.start <= last.end`), update `last.end = max(last.end, curr.end)`. Otherwise, append `curr`.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,3; 2,6; 8,10; 15,18', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def merge(intervals):',
    '    intervals.sort(key=lambda x: x[0])',
    '    merged = []',
    '    ',
    '    for interval in intervals:',
    '        if not merged or merged[-1][1] < interval[0]:',
    '            merged.append(interval)',
    '        else:',
    '            merged[-1][1] = max(merged[-1][1], interval[1])',
    '            ',
    '    return merged'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[0] - b[0]);
    let merged = [];
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), merged: [...merged], i: null };
    
    snap(2, 'Sort intervals by start time.', s);
    
    for (let i = 0; i < intervals.length; i++) {
       s.i = i;
       const curr = intervals[i];
       
       if (merged.length === 0 || merged[merged.length - 1][1] < curr[0]) {
          merged.push([...curr]);
          s.merged = JSON.parse(JSON.stringify(merged));
          snap(7, `Current [${curr}] doesn't overlap with last merged (or merged is empty). Append it.`, s);
       } else {
          const last = merged[merged.length - 1];
          last[1] = Math.max(last[1], curr[1]);
          s.merged = JSON.parse(JSON.stringify(merged));
          snap(9, `Overlap! Current [${curr}] overlaps with [${last[0]}, ${last[1]}]. Extend end to max(${last[1]}, ${curr[1]}) = ${last[1]}.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished merging.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Sorted Intervals:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '<div><div style="margin-bottom:5px; color:var(--accent); font-weight:bold;">Merged Result:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.merged.length; j++) {
       const [start, end] = state.merged[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:rgba(52,211,153,0.8); border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Insert Interval', short: 'Insert',
  idea: 'Traverse sorted intervals. Add intervals ending before newInterval starts. Merge intervals overlapping newInterval. Add intervals starting after newInterval ends.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1,3; 6,9| 2,5', hint: 'intervals split by ; | newInterval',
  code: [
    'def insert(intervals, newInterval):',
    '    res = []',
    '    i = 0',
    '    n = len(intervals)',
    '    ',
    '    while i < n and intervals[i][1] < newInterval[0]:',
    '        res.append(intervals[i])',
    '        i += 1',
    '        ',
    '    while i < n and intervals[i][0] <= newInterval[1]:',
    '        newInterval[0] = min(newInterval[0], intervals[i][0])',
    '        newInterval[1] = max(newInterval[1], intervals[i][1])',
    '        i += 1',
    '    res.append(newInterval)',
    '    ',
    '    while i < n:',
    '        res.append(intervals[i])',
    '        i += 1',
    '        ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const intervals = parts[0].split(';').map(s => s.split(',').map(Number));
    const newInt = parts[1].split(',').map(Number);
    return { intervals, newInt };
  },
  run({ intervals, newInt }) {
    const { F, snap } = avRecorder();
    let res = [];
    let i = 0, n = intervals.length;
    const s = { intervals, newInt: [...newInt], res: [...res], phase: 'before', i };
    
    snap(3, `Start inserting [${newInt}]`, s);
    
    while (i < n && intervals[i][1] < newInt[0]) {
       res.push(intervals[i]);
       s.res = JSON.parse(JSON.stringify(res));
       s.i = i;
       snap(7, `[${intervals[i]}] ends before newInterval starts. Add to result.`, s);
       i++;
    }
    
    s.phase = 'merge';
    while (i < n && intervals[i][0] <= newInt[1]) {
       newInt[0] = Math.min(newInt[0], intervals[i][0]);
       newInt[1] = Math.max(newInt[1], intervals[i][1]);
       s.newInt = [...newInt];
       s.i = i;
       snap(12, `[${intervals[i]}] overlaps. Merge into newInterval: [${newInt}].`, s);
       i++;
    }
    res.push(newInt);
    s.res = JSON.parse(JSON.stringify(res));
    snap(13, `Done merging. Add [${newInt}] to result.`, s);
    
    s.phase = 'after';
    while (i < n) {
       res.push(intervals[i]);
       s.res = JSON.parse(JSON.stringify(res));
       s.i = i;
       snap(17, `[${intervals[i]}] starts after newInterval. Add to result.`, s);
       i++;
    }
    
    s.i = null; s.phase = 'done';
    snap(20, 'Finished insertion.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), state.newInt[1], 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Original Intervals & <span style="color:#ef4444; font-weight:bold;">New Interval [${state.newInt[0]},${state.newInt[1]}]</span>:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '<div><div style="margin-bottom:5px; color:var(--accent); font-weight:bold;">Result:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.res.length; j++) {
       const [start, end] = state.res[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:rgba(52,211,153,0.8); border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Non-overlapping Intervals', short: 'Non-overlap',
  idea: 'Greedy. Sort by END time. Iterate through. If the current start < prev_end, it overlaps and must be removed (increment count). Otherwise, we keep it and update prev_end = current end.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '1,2; 2,3; 3,4; 1,3', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def eraseOverlapIntervals(intervals):',
    '    intervals.sort(key=lambda x: x[1])',
    '    count = 0',
    '    prev_end = float("-inf")',
    '    ',
    '    for start, end in intervals:',
    '        if start >= prev_end:',
    '            prev_end = end',
    '        else:',
    '            count += 1',
    '            ',
    '    return count'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[1] - b[1]);
    let count = 0, prev_end = -Infinity;
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), count, prev_end, i: null, removed: [] };
    
    snap(2, 'Sort intervals by END time. This optimally maximizes space for future intervals.', s);
    
    for (let i = 0; i < intervals.length; i++) {
       s.i = i;
       const [start, end] = intervals[i];
       
       if (start >= prev_end) {
          prev_end = end;
          s.prev_end = prev_end;
          snap(8, `[${start}, ${end}] start >= prev_end (${prev_end === -Infinity ? '-inf' : start}). Keep it. prev_end is now ${end}.`, s);
       } else {
          count++;
          s.count = count;
          s.removed.push(i);
          snap(10, `[${start}, ${end}] start < prev_end (${prev_end}). Overlap detected! Remove it. count=${count}.`, s);
       }
    }
    
    s.i = null;
    snap(13, `Done. Removed ${count} intervals.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    html += `<div style="font-weight:bold; color:var(--text);">Removed Count: <span style="color:#ef4444;">${state.count}</span></div>`;
    
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 10);
    
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       
       let isCurr = state.i === j;
       let isRemoved = state.removed.includes(j);
       
       let color = 'rgba(100,100,100,0.5)';
       if (isCurr) color = 'rgba(56,189,248,0.8)';
       if (isRemoved) color = 'rgba(239,68,68,0.3)';
       else if (!isCurr && j < (state.i===null ? state.intervals.length : state.i)) color = 'rgba(52,211,153,0.8)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border); ${isRemoved?'opacity:0.4;':''}">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}] ${isRemoved?'(X)':''}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 19 chunk 1.")
